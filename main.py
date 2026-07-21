"""
main.py — Sharky Checker launcher.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from colorama import Fore, Style, init as colorama_init
from scripts import print_banner, print_status, load_combos, INPUT_DIR
from scripts.config import load_settings, save_settings

colorama_init(autoreset=True)

SERVICES = ["spotify", "netflix", "disney", "crunchyroll", "nordvpn"]


def show_menu():
    settings = load_settings()
    grab_tag = f"{Fore.GREEN}ON" if settings["auto_grab_dumps"] else f"{Fore.RED}OFF"

    print(f"""
  {Fore.GREEN}╔══════════════════════════════════════════╗
  ║          SHARKY CHECKER                  ║
  ╠══════════════════════════════════════════╣
  ║                                          ║
  ║  {Fore.CYAN}[1]{Fore.GREEN} Spotify                            ║
  ║  {Fore.CYAN}[2]{Fore.GREEN} Netflix                            ║
  ║  {Fore.CYAN}[3]{Fore.GREEN} Disney+                            ║
  ║  {Fore.CYAN}[4]{Fore.GREEN} Crunchyroll                        ║
  ║  {Fore.CYAN}[5]{Fore.GREEN} NordVPN                            ║
  ║                                          ║
  ║  {Fore.MAGENTA}[6]{Fore.GREEN} Grab Dumps                         ║
  ║  {Fore.YELLOW}[7]{Fore.GREEN} Settings  {Fore.WHITE}Auto-Grab:{grab_tag}{Fore.GREEN}          ║
  ║                                          ║
  ║  {Fore.RED}[0]{Fore.GREEN} Exit                               ║
  ║                                          ║
  ╚══════════════════════════════════════════╝{Style.RESET_ALL}
""")


def select_combo_file() -> str:
    """Let user pick or enter a combo file path."""
    if os.path.exists(INPUT_DIR):
        files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt") and f != "proxies.txt"]

        # Also check dumps subfolder
        dumps_dir = os.path.join(INPUT_DIR, "dumps")
        if os.path.exists(dumps_dir):
            dump_files = [os.path.join("dumps", f) for f in os.listdir(dumps_dir) if f.endswith(".txt")]
            files.extend(dump_files)

        if files:
            print_status("Available combo files:", "info")
            for i, f in enumerate(files, 1):
                filepath = os.path.join(INPUT_DIR, f)
                try:
                    line_count = sum(1 for _ in open(filepath, encoding="utf-8", errors="ignore"))
                except Exception:
                    line_count = 0
                print(f"    [{i}] {f} ({line_count:,} lines)")
            print()

            choice = input(f"  {Fore.CYAN}Select file number (or enter custom path): {Style.RESET_ALL}").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(files):
                    return os.path.join(INPUT_DIR, files[idx])
            except ValueError:
                pass

            if os.path.exists(choice):
                return choice

    path = input(f"  {Fore.CYAN}Enter combo file path: {Style.RESET_ALL}").strip()
    return path


def settings_menu():
    """Toggle settings for the checker."""
    while True:
        settings = load_settings()

        grab_status = f"{Fore.GREEN}ON {Style.RESET_ALL}" if settings["auto_grab_dumps"] else f"{Fore.RED}OFF{Style.RESET_ALL}"
        startup_status = f"{Fore.GREEN}ON {Style.RESET_ALL}" if settings["grab_on_startup"] else f"{Fore.RED}OFF{Style.RESET_ALL}"

        print(f"""
  {Fore.YELLOW}╔══════════════════════════════════════════╗
  ║              S E T T I N G S             ║
  ╠══════════════════════════════════════════╣
  ║                                          ║
  ║  {Fore.CYAN}[1]{Fore.YELLOW} Auto-Grab Dumps     [{grab_status}{Fore.YELLOW}]            ║
  ║  {Fore.CYAN}[2]{Fore.YELLOW} Grab on Startup     [{startup_status}{Fore.YELLOW}]            ║
  ║  {Fore.CYAN}[3]{Fore.YELLOW} Max Dump Age: {settings['max_dump_age_hours']}h                    ║
  ║                                          ║
  ║  {Fore.WHITE}[0]{Fore.YELLOW} Back                               ║
  ║                                          ║
  ╚══════════════════════════════════════════╝{Style.RESET_ALL}
""")

        choice = input(f"  {Fore.CYAN}Select: {Style.RESET_ALL}").strip()

        if choice == "1":
            settings["auto_grab_dumps"] = not settings["auto_grab_dumps"]
            save_settings(settings)
            state = "ON" if settings["auto_grab_dumps"] else "OFF"
            print_status(f"Auto-Grab Dumps → {state}  (saved)", "success")

        elif choice == "2":
            settings["grab_on_startup"] = not settings["grab_on_startup"]
            save_settings(settings)
            state = "ON" if settings["grab_on_startup"] else "OFF"
            print_status(f"Grab on Startup → {state}  (saved)", "success")

        elif choice == "3":
            try:
                hours = int(input(f"  {Fore.CYAN}Max dump age in hours: {Style.RESET_ALL}").strip())
                settings["max_dump_age_hours"] = max(1, hours)
                save_settings(settings)
                print_status(f"Max Dump Age → {settings['max_dump_age_hours']}h  (saved)", "success")
            except ValueError:
                print_status("Invalid number", "error")

        elif choice == "0":
            return
        else:
            print_status("Invalid option — pick 0-3", "error")


def auto_grab_check():
    """Run auto-grab on startup if enabled."""
    settings = load_settings()
    if settings.get("grab_on_startup"):
        print_status("Auto-grab enabled — fetching dumps...", "action")
        from scripts.grabber import grab_pastebin_api, grab_github_gists, save_dump, merge_all_dumps
        all_combos = []
        all_combos.extend(grab_pastebin_api())
        all_combos.extend(grab_github_gists())
        if all_combos:
            save_dump(all_combos, "auto_grab")
            merge_all_dumps()
        else:
            print_status("No combos found in auto-grab", "info")
        print()


def main():
    # Check for auto-grab on startup
    auto_grab_check()

    while True:
        print_banner()
        show_menu()

        choice = input(f"  {Fore.CYAN}Select option: {Style.RESET_ALL}").strip()

        if choice == "0":
            print_status("Shutting down. 🦈\n", "info")
            sys.exit(0)

        elif choice == "6":
            from scripts.grabber import run as run_grabber
            run_grabber()
            input(f"\n  {Fore.CYAN}Press Enter to return to menu...{Style.RESET_ALL}")
            continue

        elif choice == "7":
            settings_menu()
            continue

        try:
            service_idx = int(choice) - 1
            if service_idx < 0 or service_idx >= len(SERVICES):
                print_status("Invalid option", "error")
                input(f"\n  {Fore.CYAN}Press Enter...{Style.RESET_ALL}")
                continue
        except ValueError:
            print_status("Invalid option", "error")
            input(f"\n  {Fore.CYAN}Press Enter...{Style.RESET_ALL}")
            continue

        service_name = SERVICES[service_idx]
        print_status(f"Selected: {service_name.upper()}\n", "action")

        # Auto-grab before checking if enabled
        settings = load_settings()
        if settings.get("auto_grab_dumps"):
            print_status("Auto-grab enabled — checking for fresh dumps...", "action")
            from scripts.grabber import grab_github_gists, save_dump, merge_all_dumps
            combos_grabbed = grab_github_gists()
            if combos_grabbed:
                save_dump(combos_grabbed, "auto_pre_check")
                merge_all_dumps()
            print()

        # Select combo file
        combo_file = select_combo_file()
        combos = load_combos(combo_file)

        if not combos:
            print_status("No combos loaded", "error")
            input(f"\n  {Fore.CYAN}Press Enter...{Style.RESET_ALL}")
            continue

        # Thread and delay config
        try:
            threads = int(input(f"  {Fore.CYAN}Threads (default 5): {Style.RESET_ALL}").strip() or "5")
            threads = max(1, min(threads, 50))
            delay = float(input(f"  {Fore.CYAN}Delay between checks seconds (default 0.5): {Style.RESET_ALL}").strip() or "0.5")
        except ValueError:
            threads = 5
            delay = 0.5

        print()
        from scripts.checker import run_checker
        run_checker(service_name, combos, threads, delay)

        input(f"\n  {Fore.CYAN}Press Enter to return to menu...{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
