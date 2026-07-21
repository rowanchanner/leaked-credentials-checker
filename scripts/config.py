"""
config.py — Settings persistence for Sharky Checker.
"""

import os
import json

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
SETTINGS_FILE = os.path.join(OUTPUT_DIR, "settings.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)

_DEFAULTS = {
    "auto_grab_dumps": False,
    "dump_sources": True,
    "max_dump_age_hours": 24,
    "grab_on_startup": False,
}


def load_settings() -> dict:
    settings = dict(_DEFAULTS)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
                saved = json.load(fh)
                settings.update(saved)
        except (json.JSONDecodeError, OSError):
            pass
    return settings


def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2)
