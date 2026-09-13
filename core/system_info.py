"""
System Info — RT Tool
Real-time hardware data via psutil + WMI + subprocess.
"""

import psutil
import subprocess
import platform
import os
from datetime import datetime

try:
    import wmi
    _wmi = wmi.WMI()
    WMI_AVAILABLE = True
except Exception:
    _wmi = None
    WMI_AVAILABLE = False


# ── GPU ──────────────────────────────────────────────────────────────────────

def get_gpu_info():
    """Return dict with GPU name, usage%, VRAM used/total via nvidia-smi."""
    info = {
        "name": "Unknown GPU",
        "usage": 0,
        "vram_used": 0,
        "vram_total": 0,
        "temp": 0,
        "driver": "N/A",
        "available": False,
    }
    try:
        result = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,driver_version",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = [p.strip() for p in result.stdout.strip().split(",")]
            if len(parts) >= 6:
                info["name"] = parts[0]
                info["usage"] = int(parts[1]) if parts[1].isdigit() else 0
                info["vram_used"] = int(parts[2]) if parts[2].isdigit() else 0
                info["vram_total"] = int(parts[3]) if parts[3].isdigit() else 0
                info["temp"] = int(parts[4]) if parts[4].isdigit() else 0
                info["driver"] = parts[5]
                info["available"] = True
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass

    if not info["available"] and WMI_AVAILABLE:
        try:
            gpus = _wmi.Win32_VideoController()
            if gpus:
                g = gpus[0]
                info["name"] = g.Name or "Unknown GPU"
                info["vram_total"] = int(g.AdapterRAM or 0) // (1024 * 1024)
                info["driver"] = g.DriverVersion or "N/A"
        except Exception:
            pass
    return info


def get_gpu_usage_simple():
    """Fast GPU usage % for real-time updates."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            val = result.stdout.strip()
            if val.isdigit():
                return int(val)
    except Exception:
        pass
    return 0


# ── CPU ──────────────────────────────────────────────────────────────────────

def get_cpu_info():
    """Return dict with CPU name, usage, freq, cores, threads."""
    return {
        "name": platform.processor() or "Unknown CPU",
        "usage": psutil.cpu_percent(interval=0.1),
        "freq_mhz": int(psutil.cpu_freq().current) if psutil.cpu_freq() else 0,
        "cores_physical": psutil.cpu_count(logical=False) or 0,
        "cores_logical": psutil.cpu_count(logical=True) or 0,
        "temp": _get_cpu_temp(),
    }


def _get_cpu_temp():
    """Try to get CPU temperature; returns 0 if unavailable."""
    try:
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
                    if key in temps:
                        return int(temps[key][0].current)
    except Exception:
        pass
    if WMI_AVAILABLE:
        try:
            sensors = _wmi.MSAcpi_ThermalZoneTemperature()
            if sensors:
                kelvin = sensors[0].CurrentTemperature / 10
                return int(kelvin - 273.15)
        except Exception:
            pass
    return 0


def get_cpu_usage():
    return psutil.cpu_percent(interval=None)


# ── RAM ──────────────────────────────────────────────────────────────────────

def get_ram_info():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total_gb": round(mem.total / (1024 ** 3), 1),
        "used_gb": round(mem.used / (1024 ** 3), 1),
        "available_gb": round(mem.available / (1024 ** 3), 1),
        "percent": mem.percent,
        "swap_total_gb": round(swap.total / (1024 ** 3), 1),
        "swap_used_gb": round(swap.used / (1024 ** 3), 1),
    }


def get_ram_usage():
    return psutil.virtual_memory().percent


# ── Disk ─────────────────────────────────────────────────────────────────────

def get_disk_info(path="C:\\"):
    try:
        d = psutil.disk_usage(path)
        return {
            "total_gb": round(d.total / (1024 ** 3), 1),
            "used_gb": round(d.used / (1024 ** 3), 1),
            "free_gb": round(d.free / (1024 ** 3), 1),
            "percent": d.percent,
        }
    except Exception:
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}


# ── System ───────────────────────────────────────────────────────────────────

def get_system_info():
    return {
        "os": f"{platform.system()} {platform.version()}",
        "hostname": platform.node(),
        "arch": platform.machine(),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M"),
    }


def get_power_plan():
    """Return current Windows power plan name."""
    try:
        result = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            line = result.stdout.strip()
            if "(" in line and ")" in line:
                return line[line.rfind("(") + 1:line.rfind(")")]
    except Exception:
        pass
    return "Unknown"
