<div align="center">

# 🦈 Sharky Checker

### by [SharkySolvers](https://github.com/sharkysolvers)

**Multi-service credential checker — Spotify, Netflix, Disney+, Crunchyroll, NordVPN.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

</div>

---

## ⚡ Supported Services

| Service | Auth Method | Detects |
|---------|------------|---------|
| 🟢 **Spotify** | CSRF + API login | Display name |
| 🔴 **Netflix** | authURL + form POST | Subscription status |
| 🔵 **Disney+** | BAM API device flow | Account validity |
| 🟠 **Crunchyroll** | OAuth token | Premium/Free tier |
| 🔷 **NordVPN** | API token auth | Active subscription |

---

## 🚀 Quick Start

**Windows:** double-click `run.bat`

**Manual:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r scripts\requirements.txt
python main.py
```

### Setup

1. Drop your combo list in `input/` as a `.txt` file (format: `email:password`)
2. Optionally add proxies to `input/proxies.txt`
3. Run, select service, select combo file, configure threads
4. Hits saved to `output/{service}_hits.txt`

---

## 📊 Live Stats

- Checked count / total
- Hits, fails, errors
- CPM (checks per minute)
- Hit rate percentage
- Auto rate-limit detection and retry

---

## 📁 Structure

```
leaked check/
├── main.py
├── run.bat
├── input/
│   ├── combos.txt          # Your email:password list
│   └── proxies.txt         # Optional proxies
├── output/
│   ├── spotify_hits.txt
│   ├── netflix_hits.txt
│   └── ...
└── scripts/
    ├── __init__.py
    ├── checker.py           # Core engine
    ├── modules/
    │   ├── spotify.py
    │   ├── netflix.py
    │   ├── disney.py
    │   ├── crunchyroll.py
    │   └── nordvpn.py
    └── requirements.txt
```

---

## ⚠️ Disclaimer

This tool is for **educational and authorized security testing purposes only**. Unauthorized access to accounts is illegal. Use at your own risk.

---

<div align="center">

**Built by [SharkySolvers](https://github.com/sharkysolvers)** 🦈

</div>
