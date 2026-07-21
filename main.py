"""
main.py — Sharky Checker launcher.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from colorama import Fore, Style, init as colorama_init
from scripts import print_banner, print_status, load_combos, INPUT_DIR

colorama_init(autoreset=True)

SERVICES = ["spotify", "netflix", "disney", "crunchyroll", "nordvpn"]


def show_menu():
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
  ║  {Fore.RED}[0]{Fore.GREEN} Exit                               ║
  ║                                          ║
  ╚══════════════════════════════════════════╝{Style.RESET_ALL}
""")


def select_combo_file() -> str:
    """Let user pick or enter a combo file path."""
    # List txt files in input/
    if os.path.exists(INPUT_DIR):
        files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt") and f != "proxies.txt"]
        if files:
            print_status("Available combo files in input/:", "info")
            for i, f in enumerate(files, 1):
                filepath = os.path.join(INPUT_DIR, f)
                line_count = sum(1 for _ in open(filepath, encoding="utf-8", errors="ignore"))
                print(f"    [{i}] {f} ({line_count:,} lines)")
            print()

            choice = input(f"  {Fore.CYAN}Select file number (or enter custom path): {Style.RESET_ALL}").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(files):
                    return os.path.join(INPUT_DIR, files[idx])
            except ValueError:
                pass

            # Custom path
            if os.path.exists(choice):
                return choice

    # Fallback — ask for path
    path = input(f"  {Fore.CYAN}Enter combo file path: {Style.RESET_ALL}").strip()
    return path


def main():
    while True:
        print_banner()
        show_menu()

        choice = input(f"  {Fore.CYAN}Select service: {Style.RESET_ALL}").strip()

        if choice == "0":
            print_status("Shutting down. 🦈\n", "info")
            sys.exit(0)

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
