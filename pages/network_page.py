"""
Network & Connectivity Page — RT Tool
Ping monitor, DNS optimizer, server selection, packet loss.
"""

import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QScrollArea, QGridLayout, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import pyqtgraph as pg

from ui.widgets.toggle_switch import ToggleSwitch
from core.network_tools import (
    PUBG_SERVERS, DNS_PRESETS, PingMonitor,
    ping_all_servers, set_dns, flush_dns,
    optimize_tcp, check_packet_loss, get_local_ip,
    get_public_ip, check_internet
)


def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    return f


class NetworkPage(QWidget):
    ping_updated     = pyqtSignal(int)
    servers_scanned  = pyqtSignal(dict)
    server_ping_result = pyqtSignal(str, object)   # name, ms|None
    packet_loss_result = pyqtSignal(float)          # loss %

    def __init__(self, parent=None):
        super().__init__(parent)
        self._monitor = PingMonitor(callback=self._on_ping)
        self._ping_data = []
        self._scanning_servers = False
        self._setup_ui()
        # wire thread-safe signals before starting anything
        self.server_ping_result.connect(self._apply_server_ping)
        self.packet_loss_result.connect(self._apply_packet_loss)
        self._start_monitor()
        self._check_info()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(20)

        # Header
        layout.addLayout(self._make_header())

        # Top row: connection status + quick stats
        layout.addLayout(self._make_status_row())

        # Ping chart + server list side by side
        content_row = QHBoxLayout()
        content_row.setSpacing(16)
        content_row.addWidget(self._make_ping_chart(), 3)
        content_row.addWidget(self._make_server_panel(), 2)
        layout.addLayout(content_row)

        # DNS Optimizer
        layout.addWidget(self._make_dns_section())

        # TCP / Advanced
        layout.addWidget(self._make_tcp_section())

        layout.addStretch()

    def _make_header(self):
        h = QVBoxLayout()
        h.addWidget(self._lbl("Network & Connectivity", "pageTitle"))
        h.addWidget(self._lbl("Ping Monitor · DNS · Server Selection · TCP Tweaks", "pageSubtitle"))
        return h

    def _make_status_row(self):
        row = QHBoxLayout()
        row.setSpacing(14)

        # Status card
        status_card = QWidget()
        status_card.setObjectName("card")
        sc_layout = QVBoxLayout(status_card)
        sc_layout.setSpacing(6)
        sc_layout.addWidget(self._lbl("CONNECTION STATUS", "cardTitle"))
        self._conn_status_lbl = QLabel("● Checking...")
        self._conn_status_lbl.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #5A7090;")
        sc_layout.addWidget(self._conn_status_lbl)
        self._local_ip_lbl = self._lbl("Local IP: —", "labelMuted")
        self._public_ip_lbl = self._lbl("Public IP: —", "labelMuted")
        sc_layout.addWidget(self._local_ip_lbl)
        sc_layout.addWidget(self._public_ip_lbl)
        row.addWidget(status_card, 1)

        # Ping card
        ping_card = QWidget()
        ping_card.setObjectName("cardBlue")
        pc_layout = QVBoxLayout(ping_card)
        pc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ping_big_lbl = QLabel("—")
        self._ping_big_lbl.setStyleSheet(
            "font-size: 40px; font-weight: 800; color: #00C8FF; letter-spacing: -2px;")
        self._ping_big_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pc_layout.addWidget(self._lbl("CURRENT PING", "cardTitle"))
        pc_layout.addWidget(self._ping_big_lbl)
        self._ping_host_lbl = self._lbl("Target: 8.8.8.8", "labelMuted")
        pc_layout.addWidget(self._ping_host_lbl)
        row.addWidget(ping_card, 1)

        # Packet loss card
        loss_card = QWidget()
        loss_card.setObjectName("card")
        lc_layout = QVBoxLayout(loss_card)
        lc_layout.addWidget(self._lbl("PACKET LOSS", "cardTitle"))
        self._loss_lbl = QLabel("—%")
        self._loss_lbl.setStyleSheet(
            "font-size: 30px; font-weight: 800; color: #00FF88;")
        lc_layout.addWidget(self._loss_lbl)
        check_loss_btn = QPushButton("📊  CHECK NOW")
        check_loss_btn.setObjectName("btnSmall")
        check_loss_btn.clicked.connect(self._check_packet_loss)
        lc_layout.addStretch()
        lc_layout.addWidget(check_loss_btn)
        row.addWidget(loss_card, 1)

        # VPN / Tunnel card
        vpn_card = QWidget()
        vpn_card.setObjectName("card")
        vc_layout = QVBoxLayout(vpn_card)
        vc_layout.addWidget(self._lbl("ROUTING OPTIMIZER", "cardTitle"))
        self._tr_tcp_opt = self._make_toggle_row(
            "TCP Gaming Optimizations", "#00C8FF")
        self._tr_nagle = self._make_toggle_row("Disable Nagle Algorithm", "#00C8FF")
        vc_layout.addWidget(self._tr_tcp_opt[0])
        vc_layout.addWidget(self._tr_nagle[0])
        row.addWidget(vpn_card, 1)

        return row

    def _make_ping_chart(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.addWidget(self._lbl("PING HISTORY", "cardTitle"))
        self._ping_quality_lbl = QLabel("Excellent")
        self._ping_quality_lbl.setObjectName("labelGreen")
        header.addStretch()
        header.addWidget(self._ping_quality_lbl)
        layout.addLayout(header)

        # pyqtgraph chart
        pg.setConfigOption('background', '#070B13')
        pg.setConfigOption('foreground', '#5A7090')
        self._plot = pg.PlotWidget()
        self._plot.setMinimumHeight(180)
        self._plot.setLabel('left', 'ms', color='#5A7090', size='9pt')
        self._plot.showGrid(x=True, y=True, alpha=0.1)
        self._plot.setMouseEnabled(x=False, y=False)
        self._plot.setXRange(0, 60)
        self._plot.setYRange(0, 200)
        self._curve = self._plot.plot(
            pen=pg.mkPen(color='#00C8FF', width=2),
            fillLevel=0,
            brush=pg.mkBrush(color=(0, 200, 255, 20))
        )
        layout.addWidget(self._plot)

        # Target host selector
        host_row = QHBoxLayout()
        host_row.addWidget(self._lbl("Ping Target:", "labelMuted"))
        self._host_combo = QComboBox()
        self._host_combo.addItems(["8.8.8.8 (Google)", "1.1.1.1 (Cloudflare)",
                                    "13.209.0.0 (PUBG Asia)", "18.184.0.0 (PUBG EU)"])
        self._host_combo.currentIndexChanged.connect(self._change_ping_target)
        host_row.addWidget(self._host_combo, 1)
        layout.addLayout(host_row)

        return card

    def _make_server_panel(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.addWidget(self._lbl("SERVER REGIONS", "cardTitle"))
        scan_btn = QPushButton("⚡ SCAN ALL")
        scan_btn.setObjectName("scanBtn")
        scan_btn.clicked.connect(self._scan_servers)
        header.addStretch()
        header.addWidget(scan_btn)
        layout.addLayout(header)
        layout.addWidget(_sep())

        self._server_rows = {}
        for name, (ip, location) in PUBG_SERVERS.items():
            row = QHBoxLayout()
            name_lbl = QLabel(name)
            name_lbl.setObjectName("labelPrimary")
            name_lbl.setStyleSheet("font-size: 11px;")
            ping_lbl = QLabel("—")
            ping_lbl.setObjectName("labelCyan")
            ping_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            ping_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #5A7090;")
            row.addWidget(name_lbl, 1)
            row.addWidget(ping_lbl)
            layout.addLayout(row)
            self._server_rows[name] = ping_lbl

        layout.addStretch()

        best_row = QHBoxLayout()
        best_row.addWidget(self._lbl("Best Server:", "labelMuted"))
        self._best_server_lbl = QLabel("Not scanned")
        self._best_server_lbl.setObjectName("labelGreen")
        best_row.addStretch()
        best_row.addWidget(self._best_server_lbl)
        layout.addLayout(best_row)

        return card

    def _make_dns_section(self):
        card = QWidget()
        card.setObjectName("cardGlow")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(self._lbl("DNS OPTIMIZER", "cardTitle"))
        self._dns_status_lbl = QLabel("DNS: Default")
        self._dns_status_lbl.setObjectName("labelMuted")
        header.addStretch()
        header.addWidget(self._dns_status_lbl)
        layout.addLayout(header)
        layout.addWidget(_sep())

        # Preset row
        preset_row = QHBoxLayout()
        preset_row.addWidget(self._lbl("Gaming DNS:", "labelPrimary"))
        self._dns_combo = QComboBox()
        self._dns_combo.addItems(list(DNS_PRESETS.keys()))
        preset_row.addWidget(self._dns_combo, 1)
        apply_dns_btn = QPushButton("APPLY")
        apply_dns_btn.setObjectName("btnPrimary")
        apply_dns_btn.clicked.connect(self._apply_dns)
        reset_dns_btn = QPushButton("RESET")
        reset_dns_btn.setObjectName("btnSecondary")
        reset_dns_btn.clicked.connect(self._reset_dns)
        flush_btn = QPushButton("FLUSH CACHE")
        flush_btn.setObjectName("btnSmall")
        flush_btn.clicked.connect(self._flush_dns)
        preset_row.addWidget(apply_dns_btn)
        preset_row.addWidget(reset_dns_btn)
        preset_row.addWidget(flush_btn)
        layout.addLayout(preset_row)

        # DNS info
        dns_info = QGridLayout()
        dns_info.setSpacing(8)
        labels = [
            ("Cloudflare 1.1.1.1", "Ultra-fast, privacy-focused, gaming-optimized"),
            ("Google 8.8.8.8", "Reliable, fast global infrastructure"),
            ("Quad9 9.9.9.9", "Security-focused, blocks malicious domains"),
            ("OpenDNS", "Customizable, parental controls, low latency"),
        ]
        for i, (name, desc) in enumerate(labels):
            n = QLabel(f"◆ {name}")
            n.setStyleSheet("font-size: 11px; color: #00C8FF;")
            d = QLabel(desc)
            d.setStyleSheet("font-size: 10px; color: #5A7090;")
            dns_info.addWidget(n, i, 0)
            dns_info.addWidget(d, i, 1)
        layout.addLayout(dns_info)

        return card

    def _make_tcp_section(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        layout.addWidget(self._lbl("TCP / NETWORK TWEAKS", "cardTitle"))
        layout.addWidget(_sep())

        tweaks = [
            ("TCP Auto-Tuning", "Optimize TCP receive window scaling"),
            ("RSS (Receive Side Scaling)", "Distribute network processing across CPU cores"),
            ("Chimney Offload", "Offload TCP processing to network adapter"),
            ("Timestamp Disabled", "Remove TCP timestamp overhead for lower latency"),
            ("ECN Capability", "Enable Explicit Congestion Notification"),
        ]
        self._tcp_toggles = []
        for name, desc in tweaks:
            row = self._make_toggle_row(name, "#00FF88", desc)
            layout.addWidget(row[0])
            self._tcp_toggles.append(row[1])

        apply_tcp_btn = QPushButton("⚡  APPLY TCP OPTIMIZATIONS")
        apply_tcp_btn.setObjectName("btnPrimary")
        apply_tcp_btn.clicked.connect(self._apply_tcp)
        layout.addWidget(apply_tcp_btn)

        return card

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _lbl(self, text, obj="labelPrimary"):
        l = QLabel(text)
        l.setObjectName(obj)
        return l

    def _make_toggle_row(self, title, color="#FF6B00", desc=""):
        widget = QWidget()
        row_layout = QHBoxLayout(widget)
        row_layout.setContentsMargins(0, 2, 0, 2)
        lbl = QLabel(title)
        lbl.setObjectName("labelPrimary")
        row_layout.addWidget(lbl)
        if desc:
            d = QLabel(desc)
            d.setObjectName("labelMuted")
            d.setStyleSheet("font-size: 10px;")
            row_layout.addWidget(d, 1)
        else:
            row_layout.addStretch()
        toggle = ToggleSwitch(color_on=color)
        row_layout.addWidget(toggle)
        return widget, toggle

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _start_monitor(self):
        self._monitor.start()
        self._chart_timer = QTimer(self)
        self._chart_timer.timeout.connect(self._update_chart)
        self._chart_timer.start(2000)

    def _on_ping(self, ms):
        self.ping_updated.emit(ms if ms is not None else -1)
        if ms is not None:
            self._ping_data.append(ms)
            if len(self._ping_data) > 60:
                self._ping_data.pop(0)

    def _update_chart(self):
        last = self._ping_data[-1] if self._ping_data else None
        if last is not None:
            self._ping_big_lbl.setText(f"{last}")
            # Color code
            if last < 50:
                color = "#00FF88"
                quality = "Excellent"
            elif last < 100:
                color = "#FFD700"
                quality = "Good"
            elif last < 150:
                color = "#FF6B00"
                quality = "Fair"
            else:
                color = "#FF3366"
                quality = "Poor"
            self._ping_big_lbl.setStyleSheet(
                f"font-size: 40px; font-weight: 800; color: {color}; letter-spacing: -2px;")
            self._ping_quality_lbl.setText(quality)
            self._ping_quality_lbl.setStyleSheet(
                f"font-size: 13px; font-weight: 700; color: {color};")
        else:
            self._ping_big_lbl.setText("—")

        if self._ping_data:
            self._curve.setData(self._ping_data)

    def _change_ping_target(self, idx):
        hosts = ["8.8.8.8", "1.1.1.1", "13.209.0.0", "18.184.0.0"]
        if idx < len(hosts):
            self._monitor.set_host(hosts[idx])
            self._ping_data.clear()

    def _scan_servers(self):
        if self._scanning_servers:
            return
        self._scanning_servers = True
        self._best_server_lbl.setText("Scanning...")
        for lbl in self._server_rows.values():
            lbl.setText("...")
            lbl.setStyleSheet("font-size: 11px; color: #5A7090;")

        def do_scan():
            results = ping_all_servers(callback=self._on_server_ping_thread)
            self.servers_scanned.emit(results)

        self.servers_scanned.connect(self._on_servers_done)
        threading.Thread(target=do_scan, daemon=True).start()

    def _on_server_ping_thread(self, name, ms):
        """Called from background thread — emit signal to update UI safely."""
        self.server_ping_result.emit(name, ms)

    def _apply_server_ping(self, name, ms):
        """Runs on main thread via signal — safe to update QLabel."""
        lbl = self._server_rows.get(name)
        if lbl:
            if ms is not None:
                color = "#00FF88" if ms < 60 else "#FFD700" if ms < 120 else "#FF3366"
                lbl.setText(f"{ms} ms")
                lbl.setStyleSheet(
                    f"font-size: 11px; font-weight: 700; color: {color};")
            else:
                lbl.setText("timeout")
                lbl.setStyleSheet("font-size: 11px; color: #FF3366;")

    def _on_servers_done(self, results):
        from core.network_tools import get_best_server
        best = get_best_server(results)
        self._best_server_lbl.setText(best)
        self._scanning_servers = False
        try:
            self.servers_scanned.disconnect(self._on_servers_done)
        except Exception:
            pass

    def _check_packet_loss(self):
        self._loss_lbl.setText("...")

        def do_check():
            loss = check_packet_loss()
            self.packet_loss_result.emit(loss)

        threading.Thread(target=do_check, daemon=True).start()

    def _apply_packet_loss(self, loss):
        """Runs on main thread via signal."""
        color = "#00FF88" if loss == 0 else "#FFD700" if loss < 5 else "#FF3366"
        self._loss_lbl.setText(f"{loss:.0f}%")
        self._loss_lbl.setStyleSheet(
            f"font-size: 30px; font-weight: 800; color: {color};")

    def _apply_dns(self):
        preset_name = self._dns_combo.currentText()
        primary, secondary = DNS_PRESETS.get(preset_name, ("", ""))
        ok, msg = set_dns(primary, secondary)
        self._dns_status_lbl.setText(
            f"DNS: {preset_name}" if ok else "DNS: Failed (need admin)")
        color = "#00FF88" if ok else "#FF3366"
        self._dns_status_lbl.setStyleSheet(f"font-size: 11px; color: {color};")

    def _reset_dns(self):
        set_dns("", "")
        self._dns_status_lbl.setText("DNS: Reset to DHCP")

    def _flush_dns(self):
        ok, msg = flush_dns()

    def _apply_tcp(self):
        optimize_tcp()
        for toggle in self._tcp_toggles:
            toggle.setChecked(True)

    def _check_info(self):
        def do_check():
            connected = check_internet()
            if connected:
                self._conn_status_lbl.setText("● Online")
                self._conn_status_lbl.setStyleSheet(
                    "font-size: 15px; font-weight: 700; color: #00FF88;")
                local = get_local_ip()
                pub = get_public_ip()
                self._local_ip_lbl.setText(f"Local IP: {local}")
                self._public_ip_lbl.setText(f"Public IP: {pub}")
            else:
                self._conn_status_lbl.setText("● Offline")
                self._conn_status_lbl.setStyleSheet(
                    "font-size: 15px; font-weight: 700; color: #FF3366;")

        threading.Thread(target=do_check, daemon=True).start()

    def closeEvent(self, event):
        self._monitor.stop()
        super().closeEvent(event)
