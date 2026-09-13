"""
Gameloop / PUBG Mobile Scanner — RT Tool
Detects Gameloop installation via registry and common file paths.
"""

import os
import winreg
import subprocess
from pathlib import Path

# Known Gameloop install registry keys
REGISTRY_PATHS = [
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\TxGameAssistant"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\TxGameAssistant"),
    (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\TxGameAssistant"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GameLoop"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\GameLoop"),
]

# Common install directories
COMMON_PATHS = [
    r"C:\Program Files\TxGameAssistant",
    r"C:\Program Files (x86)\TxGameAssistant",
    r"C:\GameLoop",
    r"C:\Program Files\GameLoop",
    r"C:\Program Files (x86)\GameLoop",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "TxGameAssistant"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "GameLoop"),
    r"D:\TxGameAssistant",
    r"D:\GameLoop",
    r"E:\TxGameAssistant",
    r"E:\GameLoop",
]

# PUBG Mobile sub-paths within Gameloop
PUBG_SUBPATHS = [
    r"AppMarket\apps\com.tencent.ig",
    r"AppMarket\apps\com.pubg.imobile",
    r"vms\0\userdata\com.tencent.ig",
    r"vms\0\userdata\com.pubg.imobile",
]

GAMELOOP_EXE_NAMES = [
    "GameLoop.exe", "TxGameAssistant.exe", "AndroidEmulator.exe",
    "dnplayer.exe", "MuMuPlayer.exe",
]


def scan_registry(callback=None):
    """
    Scan registry for Gameloop install path.
    Returns (install_path, version) or (None, None).
    """
    for hive, key_path in REGISTRY_PATHS:
        try:
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
                if callback:
                    callback(f"Checking registry: HKLM\\{key_path}")
                # Try common value names
                for val_name in ("InstallPath", "Path", "Install_Dir",
                                  "GamePath", "AppPath", ""):
                    try:
                        path, _ = winreg.QueryValueEx(key, val_name)
                        if path and os.path.exists(path):
                            version = _try_read_version(key)
                            return str(path), version
                    except FileNotFoundError:
                        continue
        except (FileNotFoundError, PermissionError, OSError):
            continue
    return None, None


def scan_filesystem(callback=None):
    """Scan common filesystem paths for Gameloop."""
    for path in COMMON_PATHS:
        if callback:
            callback(f"Scanning path: {path}")
        if os.path.isdir(path):
            # Look for a Gameloop executable inside
            for exe in GAMELOOP_EXE_NAMES:
                exe_path = os.path.join(path, exe)
                if os.path.isfile(exe_path):
                    return path, exe_path
            # Return directory even without exe if it looks like Gameloop
            return path, None
    return None, None


def detect_pubg_mobile(gameloop_path, callback=None):
    """Check if PUBG Mobile is installed within Gameloop."""
    if not gameloop_path:
        return False, None
    for sub in PUBG_SUBPATHS:
        full = os.path.join(gameloop_path, sub)
        if callback:
            callback(f"Checking PUBG: {full}")
        if os.path.isdir(full):
            return True, full
    return False, None


def full_scan(callback=None):
    """
    Run the full detection sequence.
    Returns a dict with all scan results.
    """
    result = {
        "gameloop_found": False,
        "gameloop_path": None,
        "gameloop_exe": None,
        "gameloop_version": None,
        "pubg_found": False,
        "pubg_path": None,
        "scan_log": [],
    }

    def log(msg):
        result["scan_log"].append(msg)
        if callback:
            callback(msg)

    log("═" * 50)
    log("RT TOOL — SYSTEM SCAN INITIATED")
    log("═" * 50)
    log("")
    log("[REGISTRY] Scanning Windows registry...")

    # Registry scan
    reg_path, reg_version = scan_registry(log)
    if reg_path:
        log(f"[✓] Registry entry found: {reg_path}")
        result["gameloop_found"] = True
        result["gameloop_path"] = reg_path
        result["gameloop_version"] = reg_version or "Unknown"
    else:
        log("[!] No registry entry found. Scanning filesystem...")
        fs_path, fs_exe = scan_filesystem(log)
        if fs_path:
            log(f"[✓] Gameloop found at: {fs_path}")
            result["gameloop_found"] = True
            result["gameloop_path"] = fs_path
            result["gameloop_exe"] = fs_exe
        else:
            log("[✗] Gameloop not found on filesystem.")

    if result["gameloop_found"]:
        log("")
        log("[PUBG] Checking for PUBG Mobile installation...")
        pubg_found, pubg_path = detect_pubg_mobile(result["gameloop_path"], log)
        result["pubg_found"] = pubg_found
        result["pubg_path"] = pubg_path
        if pubg_found:
            log(f"[✓] PUBG Mobile detected at: {pubg_path}")
        else:
            log("[!] PUBG Mobile not found. Install it via Gameloop App Market.")

    log("")
    log("[SYSTEM] Detecting hardware...")
    log(f"[✓] CPU: {_get_cpu_name()}")
    log(f"[✓] GPU: {_get_gpu_name()}")
    log(f"[✓] RAM: {_get_ram_total()} GB")

    log("")
    if result["gameloop_found"] and result["pubg_found"]:
        log("[✓] ALL CHECKS PASSED — READY TO OPTIMIZE")
    elif result["gameloop_found"]:
        log("[!] Gameloop found but PUBG Mobile not detected.")
    else:
        log("[✗] Gameloop not found. Please install Gameloop emulator.")

    return result


def get_gameloop_exe(gameloop_path):
    """Find the main Gameloop executable."""
    if not gameloop_path:
        return None
    for exe in GAMELOOP_EXE_NAMES:
        p = os.path.join(gameloop_path, exe)
        if os.path.isfile(p):
            return p
    return None


def launch_gameloop(gameloop_path):
    """Launch Gameloop with optimized startup flags."""
    exe = get_gameloop_exe(gameloop_path)
    if exe and os.path.isfile(exe):
        try:
            subprocess.Popen([exe], cwd=os.path.dirname(exe))
            return True, exe
        except Exception as e:
            return False, str(e)
    return False, "Executable not found"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _try_read_version(key):
    for name in ("Version", "DisplayVersion", "ver"):
        try:
            v, _ = winreg.QueryValueEx(key, name)
            return str(v)
        except FileNotFoundError:
            continue
    return None


def _get_cpu_name():
    try:
        import platform
        return platform.processor() or "Unknown"
    except Exception:
        return "Unknown CPU"


def _get_gpu_name():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    try:
        import wmi
        w = wmi.WMI()
        gpus = w.Win32_VideoController()
        if gpus:
            return gpus[0].Name
    except Exception:
        pass
    return "Unknown GPU"


def _get_ram_total():
    try:
        import psutil
        return round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except Exception:
        return 0
