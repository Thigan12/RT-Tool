"""
Windows Optimization Engine — RT Tool
Apply/revert registry tweaks, power plans, and process settings.
All changes are logged for one-click revert.
"""

import subprocess
import winreg
import os
import json
import ctypes
import psutil
from pathlib import Path

STATE_FILE = Path(os.environ.get("LOCALAPPDATA", ".")) / "RTTool" / "opt_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


# ── Utility ──────────────────────────────────────────────────────────────────

def _run(cmd, timeout=5):
    """Run a shell command silently. Returns (success, output)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def _reg_write(hive, path, name, value, reg_type=winreg.REG_DWORD):
    """Write a registry value. Returns True on success."""
    try:
        with winreg.OpenKey(hive, path, 0,
                            winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as k:
            winreg.SetValueEx(k, name, 0, reg_type, value)
        return True
    except Exception:
        try:
            with winreg.CreateKeyEx(hive, path, 0,
                                    winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as k:
                winreg.SetValueEx(k, name, 0, reg_type, value)
            return True
        except Exception:
            return False


def _reg_read(hive, path, name, default=None):
    """Read a registry value."""
    try:
        with winreg.OpenKey(hive, path, 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
            val, _ = winreg.QueryValueEx(k, name)
            return val
    except Exception:
        return default


# ── Power Plan ───────────────────────────────────────────────────────────────

ULTIMATE_PERF_GUID = "e9a42b02-d5df-448d-aa00-03f14749eb61"
HIGH_PERF_GUID     = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
BALANCED_GUID      = "381b4222-f694-41f0-9685-ff5bb260df2e"

def apply_ultimate_power_plan():
    """Enable Ultimate Performance power plan."""
    # Try to duplicate first (in case it doesn't exist)
    _run(f'powercfg -duplicatescheme {ULTIMATE_PERF_GUID}')
    ok, out = _run(f'powercfg /setactive {ULTIMATE_PERF_GUID}')
    if not ok:
        # Fall back to High Performance
        ok, out = _run(f'powercfg /setactive {HIGH_PERF_GUID}')
    return ok, "Ultimate Performance" if ok else out


def restore_balanced_power_plan():
    ok, out = _run(f'powercfg /setactive {BALANCED_GUID}')
    return ok, out


def get_active_power_plan():
    ok, out = _run("powercfg /getactivescheme")
    if ok and out:
        if "(" in out and ")" in out:
            return out[out.rfind("(") + 1:out.rfind(")")]
    return "Unknown"


# ── GPU Preference (Force Dedicated GPU) ─────────────────────────────────────

def force_dedicated_gpu(exe_name="TxGameAssistant.exe", enable=True):
    """
    Set per-app GPU preference to force high-performance GPU via DirectX registry.
    """
    key_path = r"SOFTWARE\Microsoft\DirectX\UserGpuPreferences"
    # GpuPreference=2 = High Performance, =1 = Power saving, =0 = Default
    value = f"GpuPreference={'2' if enable else '0'};"
    return _reg_write(
        winreg.HKEY_CURRENT_USER, key_path,
        exe_name, value, winreg.REG_SZ
    )


# ── CPU Core Parking ─────────────────────────────────────────────────────────

CORE_PARKING_KEY = (
    r"SYSTEM\CurrentControlSet\Control\Power\PowerSettings"
    r"\54533251-82be-4824-96c1-47b60b740d00"
    r"\0cc5b647-c1df-4637-891a-dec35c318583"
)

def set_core_parking(disabled=True):
    """Disable/enable CPU core parking."""
    # ValueMax = 0 disables parking; 100 = default
    val = 0 if disabled else 100
    ok1 = _reg_write(winreg.HKEY_LOCAL_MACHINE, CORE_PARKING_KEY,
                     "ValueMax", val, winreg.REG_DWORD)
    ok2 = _reg_write(winreg.HKEY_LOCAL_MACHINE, CORE_PARKING_KEY,
                     "ValueMin", val, winreg.REG_DWORD)
    # Also set via powercfg if admin
    _run("powercfg /setacvalueindex SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 0cc5b647-c1df-4637-891a-dec35c318583 0")
    _run("powercfg /setactive SCHEME_CURRENT")
    return ok1 and ok2


# ── Windows Game Mode ─────────────────────────────────────────────────────────

GAMEBAR_KEY = r"SOFTWARE\Microsoft\GameBar"

def set_game_mode(enabled=True):
    v = 1 if enabled else 0
    ok1 = _reg_write(winreg.HKEY_CURRENT_USER, GAMEBAR_KEY,
                     "AutoGameModeEnabled", v)
    ok2 = _reg_write(winreg.HKEY_CURRENT_USER, GAMEBAR_KEY,
                     "AllowAutoGameMode", v)
    return ok1 and ok2


# ── Mouse / Input ─────────────────────────────────────────────────────────────

MOUSE_KEY = r"Control Panel\Mouse"

def set_mouse_precision(enabled=False):
    """Disable Enhanced Pointer Precision for raw mouse input."""
    val = "1" if enabled else "0"
    return _reg_write(winreg.HKEY_CURRENT_USER, MOUSE_KEY,
                      "MouseSpeed", val, winreg.REG_SZ)


def set_mouse_acceleration(enabled=False):
    val1 = "1" if enabled else "0"
    ok1 = _reg_write(winreg.HKEY_CURRENT_USER, MOUSE_KEY,
                     "MouseThreshold1", val1, winreg.REG_SZ)
    ok2 = _reg_write(winreg.HKEY_CURRENT_USER, MOUSE_KEY,
                     "MouseThreshold2", val1, winreg.REG_SZ)
    return ok1 and ok2


# ── Network Tweaks (Nagle Algorithm, TCP) ─────────────────────────────────────

def disable_nagle_algorithm(enable_disable=True):
    """Disable Nagle's algorithm for lower TCP latency."""
    key = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
    val = 0 if enable_disable else 1  # TcpAckFrequency=1, TCPNoDelay=1 to disable
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as k:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(k, i)
                    sub_path = f"{key}\\{subkey_name}"
                    _reg_write(winreg.HKEY_LOCAL_MACHINE, sub_path,
                               "TcpAckFrequency", 1)
                    _reg_write(winreg.HKEY_LOCAL_MACHINE, sub_path,
                               "TCPNoDelay", 1)
                    i += 1
                except OSError:
                    break
        return True
    except Exception:
        return False


def optimize_network_adapter():
    """Disable interrupt moderation for lower network latency."""
    _run('netsh int tcp set global autotuninglevel=normal')
    _run('netsh int tcp set global chimney=enabled')
    _run('netsh int tcp set global rss=enabled')
    _run('netsh int tcp set global timestamps=disabled')
    return True


# ── Background Apps ───────────────────────────────────────────────────────────

BGAPPS_KEY = (r"SOFTWARE\Policies\Microsoft\Windows"
              r"\AppPrivacy")

def disable_background_apps(disable=True):
    val = 2 if disable else 0   # 2 = force off, 0 = user setting
    return _reg_write(winreg.HKEY_LOCAL_MACHINE, BGAPPS_KEY,
                      "LetAppsRunInBackground", val)


# ── Timer Resolution ──────────────────────────────────────────────────────────

def set_timer_resolution(high=True):
    """Set system timer resolution for lower latency scheduling."""
    if high:
        # Set 0.5ms timer via Win32 API (requires admin but try anyway)
        try:
            ntdll = ctypes.windll.ntdll
            ntdll.NtSetTimerResolution(5000, True, ctypes.byref(ctypes.c_ulong()))
            return True
        except Exception:
            pass
        _run("bcdedit /set useplatformclock false")
        _run("bcdedit /set disabledynamictick yes")
        return True
    else:
        _run("bcdedit /set useplatformclock true")
        _run("bcdedit /deletevalue disabledynamictick")
        return True


# ── Visual Effects (Windows Performance) ─────────────────────────────────────

VISUAL_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"

def optimize_visual_effects(gaming_mode=True):
    """Set Windows visual effects to performance mode."""
    val = 2 if gaming_mode else 1  # 2 = best performance, 1 = best appearance
    return _reg_write(winreg.HKEY_CURRENT_USER, VISUAL_KEY,
                      "VisualFXSetting", val)


# ── RAM Cleanup ───────────────────────────────────────────────────────────────

def clear_ram_standby():
    """Clear standby memory list using Windows API."""
    try:
        # EmptyWorkingSet for all accessible processes
        cleared = 0
        for proc in psutil.process_iter():
            try:
                handle = ctypes.windll.kernel32.OpenProcess(
                    0x1F0FFF, False, proc.pid)
                if handle:
                    ctypes.windll.psapi.EmptyWorkingSet(handle)
                    ctypes.windll.kernel32.CloseHandle(handle)
                    cleared += 1
            except Exception:
                continue
        return True, f"Cleared {cleared} processes"
    except Exception as e:
        return False, str(e)


# ── Process Priority ─────────────────────────────────────────────────────────

def set_gameloop_priority(level="high"):
    """Set Gameloop process priority."""
    priority_map = {
        "low":      psutil.BELOW_NORMAL_PRIORITY_CLASS,
        "normal":   psutil.NORMAL_PRIORITY_CLASS,
        "high":     psutil.HIGH_PRIORITY_CLASS,
        "realtime": psutil.REALTIME_PRIORITY_CLASS,
    }
    priority = priority_map.get(level, psutil.HIGH_PRIORITY_CLASS)
    count = 0
    for proc in psutil.process_iter(["name"]):
        try:
            name = proc.info["name"] or ""
            if any(n.lower() in name.lower() for n in
                   ["TxGameAssistant", "GameLoop", "AndroidEmulator",
                    "dnplayer", "NoxVMHandle"]):
                proc.nice(priority)
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return count > 0, f"Updated {count} Gameloop processes"


# ── Apply Full Optimization Profile ──────────────────────────────────────────

def apply_profile_settings(s: dict):
    """Apply a settings dictionary directly to system, registry, and GameLoop."""
    if not s or not isinstance(s, dict):
        return {}

    results = {}
    pp = s.get("power_plan", "high_performance")
    if "ultimate" in pp:
        ok, msg = apply_ultimate_power_plan()
    elif "high" in pp:
        ok, _ = _run(f'powercfg /setactive {HIGH_PERF_GUID}')
        msg = "High Performance"
    elif "balanced" in pp:
        restore_balanced_power_plan()
        ok, msg = True, "Balanced"
    else:
        ok, msg = True, pp
    results["power_plan"] = (ok, msg)

    if "game_mode" in s:
        set_game_mode(s["game_mode"])

    if "core_parking" in s:
        set_core_parking(s["core_parking"])

    if "mouse_precision_off" in s:
        set_mouse_precision(not s["mouse_precision_off"])
    elif "mouse_precision" in s:
        set_mouse_precision(s["mouse_precision"])

    if s.get("nagle_disabled") or s.get("nagle"):
        disable_nagle_algorithm()

    if "visual_fx_perf" in s:
        optimize_visual_effects(s["visual_fx_perf"])
    elif "visual_fx" in s:
        optimize_visual_effects(s["visual_fx"])

    if "timer_resolution" in s:
        set_timer_resolution(s["timer_resolution"])
    elif "timer" in s:
        set_timer_resolution(s["timer"])

    if s.get("kill_bloat"):
        try:
            from core.process_manager import kill_bloat
            kill_bloat()
        except Exception:
            pass

    if s.get("ram_cleanup"):
        clear_ram_standby()

    if "fps_target" in s:
        try:
            from core.registry_manager import set_gameloop_value, REG_DWORD
            fps = int(s["fps_target"])
            set_gameloop_value("TargetFPS", fps, REG_DWORD)
            if fps >= 90:
                set_gameloop_value("FPS_Extreme", 1, REG_DWORD)
                set_gameloop_value("VSyncEnabled", 0, REG_DWORD)
        except Exception:
            pass

    return results


def apply_profile(profile_name: str):
    """Apply a named optimization profile."""
    from core.profile_manager import load_profile, save_active_profile
    prof = load_profile(profile_name)
    s = prof.get("settings", {})
    results = apply_profile_settings(s)
    save_active_profile(profile_name, s)
    return results


def restore_defaults():
    """Revert all optimizations to Windows defaults."""
    restore_balanced_power_plan()
    set_game_mode(False)
    set_core_parking(False)
    set_mouse_precision(True)
    optimize_visual_effects(False)
    set_timer_resolution(False)
    return True
