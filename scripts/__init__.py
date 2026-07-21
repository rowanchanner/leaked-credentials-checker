"""
Sharky Checker — scripts package.
Shared utilities, banner, status printer.
"""

import os
import sys
import time
import random
import threading
from datetime import datetime
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)
INPUT_DIR = os.path.join(PROJECT_ROOT, "input")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

BANNER = f"""{Fore.GREEN}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║      ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗███████╗██████╗  ║
║     ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗ ║
║     ██║     ███████║█████╗  ██║     █████╔╝ █████╗  ██████╔╝ ║
║     ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ ██╔══╝  ██╔══██╗ ║
║     ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗███████╗██║  ██║ ║
║      ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ║
║                                                              ║
║              S H A R K Y   C H E C K E R                    ║
║                    by SharkySolvers                           ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""


def print_banner():
    os.system("cls" if os.name == "nt" else "clear")
    print(BANNER)


def print_status(message: str, status: str = "info"):
    colors = {
        "info": Fore.CYAN, "success": Fore.GREEN, "hit": Fore.GREEN,
        "warning": Fore.YELLOW, "error": Fore.RED, "action": Fore.MAGENTA,
        "fail": Fore.RED,
    }
    symbols = {
        "info": "ℹ", "success": "✓", "hit": "✓",
        "warning": "⚠", "error": "✗", "action": "►",
        "fail": "✗",
    }
    color = colors.get(status, Fore.WHITE)
    symbol = symbols.get(status, "•")
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  {Fore.WHITE}{ts} {color}{symbol} {message}{Style.RESET_ALL}")


def load_combos(filepath: str) -> list[tuple[str, str]]:
    """Load email:pass or user:pass combos from file. Auto-deduplicates."""
    if not os.path.exists(filepath):
        print_status(f"File not found: {filepath}", "error")
        return []

    seen = set()
    combos = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":", 1)
            if len(parts) == 2:
                combo = (parts[0].strip(), parts[1].strip())
                if combo not in seen:
                    seen.add(combo)
                    combos.append(combo)

    print_status(f"Loaded {len(combos)} unique combos", "info")
    return combos


def load_proxies() -> list[str]:
    """Load proxies from input/proxies.txt."""
    proxy_file = os.path.join(INPUT_DIR, "proxies.txt")
    if not os.path.exists(proxy_file):
        return []

    with open(proxy_file, "r", encoding="utf-8") as fh:
        proxies = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

    if proxies:
        print_status(f"Loaded {len(proxies)} proxies", "info")
    return proxies


def get_proxy_dict(proxies: list[str]) -> dict | None:
    """Pick a random proxy and return requests-compatible dict."""
    if not proxies:
        return None
    proxy = random.choice(proxies)
    if "@" in proxy:
        return {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    return {"http": f"http://{proxy}", "https": f"http://{proxy}"}


def save_hit(service: str, email: str, password: str, extra: str = ""):
    """Save a working credential to output/{service}_hits.txt."""
    filepath = os.path.join(OUTPUT_DIR, f"{service}_hits.txt")
    with open(filepath, "a", encoding="utf-8") as fh:
        line = f"{email}:{password}"
        if extra:
            line += f" | {extra}"
        fh.write(line + "\n")
