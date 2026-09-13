"""
Network Tools — RT Tool
Ping monitoring, DNS optimization, packet loss detection, server selection.
"""

import socket
import subprocess
import struct
import time
import threading
import requests
from typing import Callable, Optional

# PUBG Mobile server IPs (game data centers)
PUBG_SERVERS = {
    "Asia (KR)":    ("13.209.0.0",   "Seoul, Korea"),
    "Asia (SG)":    ("18.139.0.0",   "Singapore"),
    "Asia (HK)":    ("16.162.0.0",   "Hong Kong"),
    "South Asia":   ("3.109.0.0",    "Mumbai, India"),
    "EU (Frankfurt)": ("18.184.0.0", "Frankfurt, Germany"),
    "NA (Virginia)": ("54.208.0.0",  "N. Virginia, USA"),
    "NA (Oregon)":  ("54.148.0.0",   "Oregon, USA"),
    "SA (Brazil)":  ("54.232.0.0",   "São Paulo, Brazil"),
    "OCE (Sydney)": ("13.211.0.0",   "Sydney, Australia"),
    "ME (Bahrain)": ("15.185.0.0",   "Bahrain"),
}

# Gaming-optimized DNS servers
DNS_PRESETS = {
    "Cloudflare (1.1.1.1)":   ("1.1.1.1",   "1.0.0.1"),
    "Google (8.8.8.8)":       ("8.8.8.8",   "8.8.4.4"),
    "OpenDNS":                 ("208.67.222.222", "208.67.220.220"),
    "Quad9 (Gaming)":          ("9.9.9.9",   "149.112.112.112"),
    "AdGuard":                 ("94.140.14.14", "94.140.15.15"),
    "Default (ISP)":           ("", ""),
}


# ── Ping ─────────────────────────────────────────────────────────────────────

def ping_host(host: str, timeout: float = 2.0) -> Optional[int]:
    """
    Ping a host and return round-trip time in ms.
    Returns None if unreachable.
    Uses Windows 'ping' command for reliability.
    """
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(int(timeout * 1000)), host],
            capture_output=True, text=True, timeout=timeout + 1
        )
        output = result.stdout
        # Parse "Average = Xms" or "time=Xms"
        for line in output.splitlines():
            line = line.strip()
            if "Average" in line or "average" in line:
                parts = line.split("=")
                for p in parts:
                    p = p.strip().rstrip("ms").strip()
                    try:
                        return int(p)
                    except ValueError:
                        continue
            if "time=" in line.lower():
                idx = line.lower().index("time=") + 5
                val = ""
                for ch in line[idx:]:
                    if ch.isdigit():
                        val += ch
                    elif val:
                        break
                if val:
                    return int(val)
    except (subprocess.TimeoutExpired, Exception):
        pass
    return None


def ping_all_servers(callback: Optional[Callable] = None) -> dict:
    """Ping all PUBG servers and return {name: ms} dict."""
    results = {}
    threads = []

    def _ping_one(name, ip):
        ms = ping_host(ip)
        results[name] = ms
        if callback:
            callback(name, ms)

    for name, (ip, _) in PUBG_SERVERS.items():
        t = threading.Thread(target=_ping_one, args=(name, ip), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=5)

    return results


def get_best_server(results: dict) -> str:
    """Return the server name with the lowest ping."""
    valid = {k: v for k, v in results.items() if v is not None}
    if not valid:
        return "Asia (SG)"
    return min(valid, key=valid.get)


def check_packet_loss(host: str = "8.8.8.8", count: int = 10) -> float:
    """Send N pings and return packet loss percentage."""
    try:
        result = subprocess.run(
            ["ping", "-n", str(count), host],
            capture_output=True, text=True, timeout=count * 2 + 5
        )
        output = result.stdout
        for line in output.splitlines():
            if "Lost" in line or "loss" in line.lower():
                # e.g. "Packets: Sent = 10, Received = 9, Lost = 1 (10% loss)"
                if "%" in line:
                    idx = line.index("%")
                    val = ""
                    for ch in reversed(line[:idx]):
                        if ch.isdigit():
                            val = ch + val
                        elif val:
                            break
                    if val:
                        return float(val)
    except Exception:
        pass
    return 0.0


# ── DNS ───────────────────────────────────────────────────────────────────────

def get_active_adapters():
    """List active network adapter names."""
    adapters = []
    try:
        result = subprocess.run(
            ["netsh", "interface", "show", "interface"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[1].lower() == "connected":
                name = " ".join(parts[3:])
                adapters.append(name)
    except Exception:
        pass
    return adapters or ["Wi-Fi", "Ethernet"]


def set_dns(primary: str, secondary: str, adapter: str = None):
    """
    Change DNS servers on the active adapter.
    Requires admin rights for full effect.
    """
    if not adapter:
        adapters = get_active_adapters()
        adapter = adapters[0] if adapters else "Wi-Fi"

    results = []
    if not primary:
        # Reset to DHCP
        ok, out = _run_net(
            f'netsh interface ip set dns name="{adapter}" source=dhcp')
        return ok, f"DNS reset to DHCP on {adapter}"

    ok1, _ = _run_net(
        f'netsh interface ip set dns name="{adapter}" '
        f'static {primary} primary validate=no'
    )
    results.append(ok1)

    if secondary:
        ok2, _ = _run_net(
            f'netsh interface ip add dns name="{adapter}" '
            f'{secondary} index=2 validate=no'
        )
        results.append(ok2)

    success = any(results)
    msg = (f"DNS set to {primary}/{secondary} on {adapter}"
           if success else "Failed — try running as administrator")
    return success, msg


def flush_dns():
    """Flush Windows DNS cache."""
    ok, out = _run_net("ipconfig /flushdns")
    return ok, out


def optimize_tcp():
    """Apply TCP gaming optimizations."""
    commands = [
        "netsh int tcp set global autotuninglevel=normal",
        "netsh int tcp set global chimney=enabled",
        "netsh int tcp set global rss=enabled",
        "netsh int tcp set global timestamps=disabled",
        "netsh int tcp set global ecncapability=enabled",
    ]
    results = []
    for cmd in commands:
        ok, _ = _run_net(cmd)
        results.append(ok)
    return any(results)


# ── Connectivity ──────────────────────────────────────────────────────────────

def check_internet():
    """Quick internet connectivity check."""
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
            ("8.8.8.8", 53))
        return True
    except OSError:
        return False


def get_public_ip():
    """Get public IP address."""
    try:
        r = requests.get("https://api.ipify.org", timeout=3)
        return r.text.strip()
    except Exception:
        return "Unknown"


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


# ── Continuous Ping Monitor ───────────────────────────────────────────────────

class PingMonitor:
    """Background thread that continuously pings a host."""

    def __init__(self, host="8.8.8.8", interval=2.0, callback=None):
        self.host = host
        self.interval = interval
        self.callback = callback
        self._stop = threading.Event()
        self._thread = None
        self.last_ping = None
        self.history = []  # list of (timestamp, ms)

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def set_host(self, host):
        self.host = host
        self.history.clear()

    def _run(self):
        while not self._stop.is_set():
            ms = ping_host(self.host)
            self.last_ping = ms
            self.history.append((time.time(), ms))
            if len(self.history) > 120:
                self.history.pop(0)
            if self.callback:
                self.callback(ms)
            self._stop.wait(self.interval)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_net(cmd, timeout=5):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)
