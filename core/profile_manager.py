"""
Profile Manager — RT Tool
Save/load/export/import optimization profiles as JSON.
"""

import json
import os
from pathlib import Path
from datetime import datetime

PROFILES_DIR = Path(os.environ.get("LOCALAPPDATA", ".")) / "RTTool" / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

ACTIVE_PROFILE_FILE = PROFILES_DIR / "active.json"

# Preset hardware tier configurations
PRESET_PROFILES = {
    "budget": {
        "name": "Budget",
        "tier": "budget",
        "description": "Safe tweaks for low-end PCs. Stable FPS, no crashes.",
        "color": "#00FF88",
        "settings": {
            "power_plan": "high_performance",
            "game_mode": True,
            "core_parking": False,
            "gpu_dedicated": True,
            "gpu_priority": False,
            "mouse_precision_off": True,
            "nagle_disabled": True,
            "visual_fx_perf": True,
            "timer_resolution": False,
            "process_priority": "high",
            "kill_bloat": False,
            "stop_services": False,
            "fps_target": 60,
            "ram_cleanup": True,
            "dns_preset": "Cloudflare (1.1.1.1)",
            "spatial_audio": False,
            "audio_latency": "medium",
            "crosshair_enabled": True,
            "hud_enabled": True,
        }
    },
    "mid": {
        "name": "Mid-Range",
        "tier": "mid",
        "description": "Balanced tweaks for mid-range systems. Great FPS/stability.",
        "color": "#00C8FF",
        "settings": {
            "power_plan": "high_performance",
            "game_mode": True,
            "core_parking": True,
            "gpu_dedicated": True,
            "gpu_priority": True,
            "mouse_precision_off": True,
            "nagle_disabled": True,
            "visual_fx_perf": True,
            "timer_resolution": True,
            "process_priority": "high",
            "kill_bloat": True,
            "stop_services": False,
            "fps_target": 90,
            "ram_cleanup": True,
            "dns_preset": "Cloudflare (1.1.1.1)",
            "spatial_audio": True,
            "audio_latency": "low",
            "crosshair_enabled": True,
            "hud_enabled": True,
        }
    },
    "high": {
        "name": "High-End",
        "tier": "high",
        "description": "Aggressive tweaks for high-end rigs. Maximum performance.",
        "color": "#FFD700",
        "settings": {
            "power_plan": "ultimate_performance",
            "game_mode": True,
            "core_parking": True,
            "gpu_dedicated": True,
            "gpu_priority": True,
            "mouse_precision_off": True,
            "nagle_disabled": True,
            "visual_fx_perf": True,
            "timer_resolution": True,
            "process_priority": "high",
            "kill_bloat": True,
            "stop_services": True,
            "fps_target": 144,
            "ram_cleanup": True,
            "dns_preset": "Cloudflare (1.1.1.1)",
            "spatial_audio": True,
            "audio_latency": "ultra_low",
            "crosshair_enabled": True,
            "hud_enabled": True,
        }
    },
    "enthusiast": {
        "name": "Enthusiast",
        "tier": "enthusiast",
        "description": "Maximum everything. Competitive edge. Use with caution.",
        "color": "#FF3366",
        "settings": {
            "power_plan": "ultimate_performance",
            "game_mode": True,
            "core_parking": True,
            "gpu_dedicated": True,
            "gpu_priority": True,
            "mouse_precision_off": True,
            "nagle_disabled": True,
            "visual_fx_perf": True,
            "timer_resolution": True,
            "process_priority": "realtime",
            "kill_bloat": True,
            "stop_services": True,
            "fps_target": 240,
            "ram_cleanup": True,
            "dns_preset": "Cloudflare (1.1.1.1)",
            "spatial_audio": True,
            "audio_latency": "ultra_low",
            "crosshair_enabled": True,
            "hud_enabled": True,
        }
    }
}


def get_preset(name: str) -> dict:
    """Return a preset profile config."""
    return PRESET_PROFILES.get(name, PRESET_PROFILES["mid"])


def list_presets() -> list:
    return list(PRESET_PROFILES.values())


def list_custom_profiles() -> list:
    """Return list of saved custom profile names."""
    profiles = []
    for f in PROFILES_DIR.glob("*.json"):
        if f.name == "active.json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            profiles.append(data)
        except Exception:
            continue
    return profiles


def save_profile(name: str, settings: dict) -> bool:
    """Save current settings as a named custom profile."""
    profile = {
        "name": name,
        "tier": "custom",
        "description": f"Custom profile saved {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "color": "#FF6B00",
        "settings": settings,
        "saved_at": datetime.now().isoformat(),
    }
    safe_name = "".join(c for c in name if c.isalnum() or c in "_ -")
    path = PROFILES_DIR / f"{safe_name}.json"
    try:
        path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def load_profile(name: str) -> dict:
    """Load a profile by name (preset or custom)."""
    if name.lower() in PRESET_PROFILES:
        return PRESET_PROFILES[name.lower()]
    safe_name = "".join(c for c in name if c.isalnum() or c in "_ -")
    path = PROFILES_DIR / f"{safe_name}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return PRESET_PROFILES["mid"]


def delete_profile(name: str) -> bool:
    safe_name = "".join(c for c in name if c.isalnum() or c in "_ -")
    path = PROFILES_DIR / f"{safe_name}.json"
    try:
        path.unlink()
        return True
    except Exception:
        return False


def save_active_profile(profile_name: str, settings: dict):
    data = {"profile": profile_name, "settings": settings,
            "updated": datetime.now().isoformat()}
    try:
        ACTIVE_PROFILE_FILE.write_text(
            json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_active_profile() -> dict:
    try:
        if ACTIVE_PROFILE_FILE.exists():
            return json.loads(ACTIVE_PROFILE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"profile": "mid", "settings": PRESET_PROFILES["mid"]["settings"]}


def export_profile(profile_name: str, export_path: str) -> bool:
    data = load_profile(profile_name)
    try:
        Path(export_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def import_profile(import_path: str) -> tuple:
    """Import a profile from a JSON file. Returns (success, profile_name)."""
    try:
        data = json.loads(Path(import_path).read_text(encoding="utf-8"))
        name = data.get("name", "Imported Profile")
        if save_profile(name, data.get("settings", {})):
            return True, name
    except Exception as e:
        return False, str(e)
    return False, "Failed to import"
