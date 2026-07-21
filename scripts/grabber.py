"""
grabber.py — Credential dump grabber.
Scrapes leaked combo lists from known public paste/dump sites.
Downloads and saves to input/ for use with the checker.
"""

import os
import re
import time
import random
import hashlib
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from . import print_status, INPUT_DIR

DUMPS_DIR = os.path.join(INPUT_DIR, "dumps")
os.makedirs(DUMPS_DIR, exist_ok=True)

# Known public sources that aggregate leaked pastes
SOURCES = [
    {
        "name": "Pastebin (Recent)",
        "scrape_url": "https://scrape.pastebin.com/api_scraping.php?limit=100",
        "type": "api",
        "parse": "pastebin_api",
    },
    {
        "name": "Rentry.co",
        "scrape_url": "https://rentry.co",
        "type": "scrape",
        "parse": "generic_paste",
    },
    {
        "name": "dpaste.org",
        "scrape_url": "https://dpaste.org",
        "type": "scrape",
        "parse": "generic_paste",
    },
    {
        "name": "PrivateBin instances",
        "scrape_url": "https://paste.mozilla.org",
        "type": "scrape",
        "parse": "generic_paste",
    },
    {
        "name": "GitHub Gist Search",
        "scrape_url": "https://gist.github.com/search?q=email+password+combo&type=code",
        "type": "scrape",
        "parse": "github_gist",
    },
]

# Regex patterns that identify credential-like content
COMBO_PATTERNS = [
    re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+[:\|;][\S]+', re.MULTILINE),  # email:pass
    re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+\t[\S]+', re.MULTILINE),       # email\tpass
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def extract_combos(text: str) -> list[str]:
    """Extract email:password combos from raw text."""
    combos = set()
    for pattern in COMBO_PATTERNS:
        matches = pattern.findall(text)
        for match in matches:
            # Normalize separator to ':'
            normalized = match.replace("|", ":").replace(";", ":").replace("\t", ":")
            parts = normalized.split(":", 1)
            if len(parts) == 2 and "@" in parts[0] and len(parts[1]) >= 4:
                combos.add(f"{parts[0]}:{parts[1]}")
    return list(combos)


def grab_pastebin_api() -> list[str]:
    """
    Grab recent pastes from Pastebin's scraping API.
    *Requires a Pastebin PRO account with scraping API access.
     Free accounts get 403. Falls back gracefully.*
    """
    all_combos = []
    try:
        print_status("Fetching Pastebin recent pastes...", "action")
        resp = requests.get(
            "https://scrape.pastebin.com/api_scraping.php?limit=50",
            headers=HEADERS, timeout=10
        )

        if resp.status_code == 403:
            print_status("Pastebin API requires PRO — skipping", "warning")
            return []

        if resp.status_code != 200:
            print_status(f"Pastebin returned {resp.status_code}", "warning")
            return []

        pastes = resp.json()
        print_status(f"Found {len(pastes)} recent pastes", "info")

        for paste in pastes[:30]:
            try:
                paste_url = paste.get("scrape_url", "")
                if not paste_url:
                    continue

                paste_resp = requests.get(paste_url, headers=HEADERS, timeout=5)
                if paste_resp.status_code == 200:
                    combos = extract_combos(paste_resp.text)
                    if combos:
                        all_combos.extend(combos)
                        print_status(f"Found {len(combos)} combos in paste", "success")

                time.sleep(random.uniform(0.5, 1.5))

            except Exception:
                continue

    except Exception as exc:
        print_status(f"Pastebin error: {exc}", "error")

    return all_combos


def grab_generic_search() -> list[str]:
    """Search Google for public combo list pastes."""
    all_combos = []
    search_queries = [
        "site:pastebin.com email password combo",
        "site:rentry.co combo list email",
        "site:dpaste.org email:password",
    ]

    for query in search_queries:
        try:
            print_status(f"Searching: {query[:50]}...", "action")
            resp = requests.get(
                "https://www.google.com/search",
                params={"q": query, "num": 10},
                headers=HEADERS, timeout=10
            )

            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            links = []

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if "pastebin.com/" in href or "rentry.co/" in href or "dpaste.org/" in href:
                    # Extract actual URL from Google redirect
                    url_match = re.search(r'(https?://[^\s&]+)', href)
                    if url_match:
                        links.append(url_match.group(1))

            for link in links[:5]:
                try:
                    page_resp = requests.get(link, headers=HEADERS, timeout=5)
                    if page_resp.status_code == 200:
                        combos = extract_combos(page_resp.text)
                        if combos:
                            all_combos.extend(combos)
                            print_status(f"Found {len(combos)} combos from {link[:40]}", "success")
                    time.sleep(random.uniform(1.0, 2.0))
                except Exception:
                    continue

            time.sleep(random.uniform(2.0, 4.0))

        except Exception:
            continue

    return all_combos


def grab_github_gists() -> list[str]:
    """Search GitHub Gists for public combo lists."""
    all_combos = []
    try:
        print_status("Searching GitHub Gists...", "action")
        resp = requests.get(
            "https://api.github.com/gists/public",
            params={"per_page": 30},
            headers={**HEADERS, "Accept": "application/vnd.github.v3+json"},
            timeout=10
        )

        if resp.status_code != 200:
            print_status(f"GitHub API returned {resp.status_code}", "warning")
            return []

        gists = resp.json()
        for gist in gists:
            for filename, file_info in gist.get("files", {}).items():
                raw_url = file_info.get("raw_url", "")
                if not raw_url:
                    continue

                try:
                    raw_resp = requests.get(raw_url, headers=HEADERS, timeout=5)
                    if raw_resp.status_code == 200:
                        combos = extract_combos(raw_resp.text)
                        if combos:
                            all_combos.extend(combos)
                            print_status(f"Found {len(combos)} combos in gist: {filename}", "success")
                except Exception:
                    continue

            time.sleep(random.uniform(0.3, 0.8))

    except Exception as exc:
        print_status(f"GitHub error: {exc}", "error")

    return all_combos


def save_dump(combos: list[str], source_name: str) -> str | None:
    """Save grabbed combos to a file in input/dumps/."""
    if not combos:
        return None

    # Deduplicate
    unique = list(set(combos))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r'[^\w]', '_', source_name.lower())
    filename = f"dump_{safe_name}_{timestamp}.txt"
    filepath = os.path.join(DUMPS_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as fh:
        for combo in sorted(unique):
            fh.write(combo + "\n")

    print_status(f"Saved {len(unique)} unique combos to input/dumps/{filename}", "success")
    return filepath


def merge_all_dumps() -> str | None:
    """Merge all dump files into one master combo file."""
    if not os.path.exists(DUMPS_DIR):
        return None

    all_combos = set()
    for filename in os.listdir(DUMPS_DIR):
        if filename.endswith(".txt"):
            filepath = os.path.join(DUMPS_DIR, filename)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    line = line.strip()
                    if line and ":" in line and "@" in line.split(":")[0]:
                        all_combos.add(line)

    if not all_combos:
        print_status("No combos found in dumps", "warning")
        return None

    merged_path = os.path.join(INPUT_DIR, "merged_dumps.txt")
    with open(merged_path, "w", encoding="utf-8") as fh:
        for combo in sorted(all_combos):
            fh.write(combo + "\n")

    print_status(f"Merged {len(all_combos)} unique combos to input/merged_dumps.txt", "success")
    return merged_path


def run():
    """Interactive dump grabber."""
    from colorama import Fore, Style

    print_status("Dump Grabber", "action")
    print_status("=" * 40, "info")

    print(f"""
  {Fore.CYAN}Sources:
  {Fore.GREEN}[1]{Fore.CYAN} Pastebin (API — requires PRO)
  {Fore.GREEN}[2]{Fore.CYAN} Google search for public pastes
  {Fore.GREEN}[3]{Fore.CYAN} GitHub Gists
  {Fore.GREEN}[4]{Fore.CYAN} All sources
  {Fore.GREEN}[5]{Fore.CYAN} Merge existing dumps{Style.RESET_ALL}
""")

    choice = input(f"  {Fore.CYAN}Select: {Style.RESET_ALL}").strip()

    if choice == "1":
        combos = grab_pastebin_api()
        save_dump(combos, "pastebin")
    elif choice == "2":
        combos = grab_generic_search()
        save_dump(combos, "google_search")
    elif choice == "3":
        combos = grab_github_gists()
        save_dump(combos, "github_gists")
    elif choice == "4":
        all_combos = []
        all_combos.extend(grab_pastebin_api())
        all_combos.extend(grab_generic_search())
        all_combos.extend(grab_github_gists())
        save_dump(all_combos, "all_sources")
    elif choice == "5":
        merge_all_dumps()
    else:
        print_status("Invalid option", "error")
        return

    # Offer to merge
    if choice in ("1", "2", "3", "4"):
        merge = input(f"\n  {Fore.CYAN}Merge all dumps into one file? (y/n): {Style.RESET_ALL}").strip().lower()
        if merge == "y":
            merge_all_dumps()
