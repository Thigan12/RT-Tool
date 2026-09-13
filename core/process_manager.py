"""
Process Manager — RT Tool
Kill background processes, set priorities, manage Windows services.
"""

import psutil
import subprocess
import winreg

# Processes commonly known to reduce gaming performance
BLOAT_PROCESSES = [
    "OneDrive.exe", "OneDriveSetup.exe",
    "SearchIndexer.exe", "SearchUI.exe",
    "SkypeApp.exe", "Skype.exe",
    "Teams.exe", "MicrosoftTeams.exe",
    "Spotify.exe", "Discord.exe",
    "steam.exe", "EpicGamesLauncher.exe",
    "AdobeARM.exe", "AdobeUpdateService.exe",
    "Dropbox.exe", "GoogleDriveFS.exe",
    "iCloudDrive.exe", "iCloudPhotos.exe",
    "WebHelper.exe", "iTunes.exe",
    "WinRAR.exe", "7zG.exe",
    "msiexec.exe",
    "SamsungMagician.exe", "MSIAfterburner.exe",
    "RazerSynapse.exe", "LogiOptions.exe",
    "acrotray.exe", "reader_sl.exe",
    "wuauserv",
]

# Services to disable during gaming
SERVICES_TO_STOP = [
    "wuauserv",      # Windows Update
    "SysMain",       # SuperFetch
    "DiagTrack",     # Telemetry
    "WSearch",       # Windows Search
    "TabletInputService",
    "PrintSpooler",
    "Fax",
    "WbioSrvc",      # Biometric
]


def get_running_processes(sort_by="cpu"):
    """Return list of running process info dicts, sorted by cpu or ram."""
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent",
                                   "memory_percent", "status"]):
        try:
            info = p.info
            if info["name"] and info["status"] != "zombie":
                procs.append({
                    "pid": info["pid"],
                    "name": info["name"],
                    "cpu": round(info["cpu_percent"] or 0, 1),
                    "mem": round(info["memory_percent"] or 0, 1),
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "cpu" if sort_by == "cpu" else "mem"
    procs.sort(key=lambda x: x[key], reverse=True)
    return procs


def kill_process(pid=None, name=None):
    """Kill process by PID or name."""
    killed = 0
    for p in psutil.process_iter(["pid", "name"]):
        try:
            if pid and p.pid == pid:
                p.kill()
                killed += 1
            elif name and p.name().lower() == name.lower():
                p.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return killed


def kill_bloat(callback=None):
    """Kill known bloat processes."""
    killed = []
    for p in psutil.process_iter(["pid", "name"]):
        try:
            if p.name() in BLOAT_PROCESSES:
                p.kill()
                killed.append(p.name())
                if callback:
                    callback(f"Killed: {p.name()}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return killed


def stop_gaming_services(callback=None):
    """Temporarily stop high-overhead Windows services."""
    stopped = []
    for svc in SERVICES_TO_STOP:
        try:
            result = subprocess.run(
                ["sc", "stop", svc],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                stopped.append(svc)
                if callback:
                    callback(f"Stopped service: {svc}")
        except Exception:
            continue
    return stopped


def restore_services(callback=None):
    """Re-start stopped services."""
    for svc in SERVICES_TO_STOP:
        try:
            subprocess.run(["sc", "start", svc],
                           capture_output=True, timeout=5)
            if callback:
                callback(f"Started: {svc}")
        except Exception:
            continue


def set_process_priority(pid, level="high"):
    """Set priority for a specific process PID."""
    priority_map = {
        "idle":      psutil.IDLE_PRIORITY_CLASS,
        "low":       psutil.BELOW_NORMAL_PRIORITY_CLASS,
        "normal":    psutil.NORMAL_PRIORITY_CLASS,
        "high":      psutil.HIGH_PRIORITY_CLASS,
        "realtime":  psutil.REALTIME_PRIORITY_CLASS,
    }
    try:
        p = psutil.Process(pid)
        p.nice(priority_map.get(level, psutil.HIGH_PRIORITY_CLASS))
        return True, f"Priority set to {level} for PID {pid}"
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        return False, str(e)


def set_affinity(pid, cores):
    """Set CPU affinity for a process (list of core indices)."""
    try:
        p = psutil.Process(pid)
        p.cpu_affinity(cores)
        return True
    except Exception:
        return False


def get_gameloop_pids():
    """Return list of PIDs for all Gameloop-related processes."""
    names = ["TxGameAssistant", "GameLoop", "AndroidEmulator",
             "dnplayer", "NoxVMHandle", "AndroidEmulatorEx"]
    pids = []
    for p in psutil.process_iter(["pid", "name"]):
        try:
            if any(n.lower() in (p.name() or "").lower() for n in names):
                pids.append(p.pid)
        except Exception:
            continue
    return pids
