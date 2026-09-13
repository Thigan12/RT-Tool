"""
Home Page — Launch Hub — RT Tool
Auto-scan, Gameloop status, PUBG status, quick launch.
"""

import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QSizePolicy, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont, QColor

from core.scanner import full_scan, launch_gameloop
from core.system_info import get_cpu_usage, get_ram_usage, get_gpu_usage_simple
from ui.widgets.ring_gauge import RingGauge


class ScanWorker(QObject):
    """Worker thread for scan operation."""
    log_line = pyqtSignal(str)
    finished = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        result = full_scan(callback=self.log_line.emit)
        self.finished.emit(result)


class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scan_result = None
        self._scan_thread = None
        self._scan_worker = None
        self._scanning = False   # guard flag — avoids QThread deleted crash
        self._setup_ui()
        self._start_hw_timer()

    # ── UI Setup ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(20)

        # Page header
        layout.addLayout(self._make_header())

        # Status + Scan row
        layout.addLayout(self._make_status_row())

        # Scan console
        layout.addWidget(self._make_console())

        # Hardware monitor row
        layout.addLayout(self._make_hw_row())

        # Launch section
        layout.addWidget(self._make_launch_card())

        layout.addStretch()

    def _make_header(self):
        h = QVBoxLayout()
        title = QLabel("  Launch Hub")
        title.setObjectName("pageTitle")
        sub = QLabel("Detect Gameloop · Optimize System · Launch PUBG Mobile")
        sub.setObjectName("pageSubtitle")
        h.addWidget(title)
        h.addWidget(sub)
        return h

    def _make_status_row(self):
        row = QHBoxLayout()
        row.setSpacing(14)

        # Gameloop status card
        self._gl_card = self._make_status_card(
            "GAMELOOP", "Not Scanned", "#5A7090", "")
        # PUBG status card
        self._pubg_card = self._make_status_card(
            "PUBG MOBILE", "Not Scanned", "#5A7090", "🎮")
        # Connection card
        self._conn_card = self._make_status_card(
            "CONNECTION", "Checking...", "#5A7090", "🌐")

        row.addWidget(self._gl_card[0], 1)
        row.addWidget(self._pubg_card[0], 1)
        row.addWidget(self._conn_card[0], 1)

        # Scan button card
        scan_card = QWidget()
        scan_card.setObjectName("cardBlue")
        scan_layout = QVBoxLayout(scan_card)
        scan_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scan_layout.setSpacing(8)

        scan_icon = QLabel("🔍")
        scan_icon.setStyleSheet("font-size: 24px;")
        scan_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._scan_btn = QPushButton("AUTO SCAN")
        self._scan_btn.setObjectName("scanBtn")
        self._scan_btn.clicked.connect(self._run_scan)

        scan_layout.addWidget(scan_icon)
        scan_layout.addWidget(self._scan_btn)
        row.addWidget(scan_card, 1)

        return row

    def _make_status_card(self, title, status, color, icon):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 18px;")
        title_lbl = QLabel(title)
        title_lbl.setObjectName("sectionHeader")
        title_lbl.setStyleSheet("font-size: 9px; letter-spacing: 2px; color: #5A7090;")
        top.addWidget(icon_lbl)
        top.addWidget(title_lbl)
        top.addStretch()
        layout.addLayout(top)

        dot_row = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"font-size: 10px; color: {color};")
        val_lbl = QLabel(status)
        val_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {color};")
        dot_row.addWidget(dot)
        dot_row.addWidget(val_lbl)
        dot_row.addStretch()
        layout.addLayout(dot_row)

        return card, dot, val_lbl

    def _make_console(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("SCAN CONSOLE")
        title.setObjectName("sectionHeader")
        clear_btn = QPushButton("CLEAR")
        clear_btn.setObjectName("btnSmall")
        clear_btn.clicked.connect(lambda: self._console.clear())
        header.addWidget(title)
        header.addStretch()
        header.addWidget(clear_btn)
        layout.addLayout(header)

        self._console = QTextEdit()
        self._console.setObjectName("console")
        self._console.setReadOnly(True)
        self._console.setMinimumHeight(160)
        self._console.setMaximumHeight(200)
        self._console.setPlaceholderText(
            "Click AUTO SCAN to detect Gameloop and PUBG Mobile...")
        layout.addWidget(self._console)

        return card

    def _make_hw_row(self):
        row = QHBoxLayout()
        row.setSpacing(14)

        # CPU
        self._cpu_card = self._make_gauge_card("CPU USAGE", "#FFD700")
        self._cpu_gauge = self._cpu_card[1]
        # GPU
        self._gpu_card = self._make_gauge_card("GPU USAGE", "#FF6B00")
        self._gpu_gauge = self._gpu_card[1]
        # RAM
        self._ram_card = self._make_gauge_card("RAM USAGE", "#A070FF")
        self._ram_gauge = self._ram_card[1]

        row.addWidget(self._cpu_card[0], 1)
        row.addWidget(self._gpu_card[0], 1)
        row.addWidget(self._ram_card[0], 1)

        # System info card
        info_card = QWidget()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(6)
        info_lbl = QLabel("SYSTEM INFO")
        info_lbl.setObjectName("sectionHeader")
        info_layout.addWidget(info_lbl)

        self._sys_labels = {}
        for key in ["Power Plan", "Active Profile", "Optimizations"]:
            row2 = QHBoxLayout()
            k = QLabel(key + ":")
            k.setObjectName("labelMuted")
            k.setStyleSheet("font-size: 11px;")
            v = QLabel("—")
            v.setStyleSheet("font-size: 11px; color: #DCE8FF; font-weight: 600;")
            row2.addWidget(k)
            row2.addStretch()
            row2.addWidget(v)
            info_layout.addLayout(row2)
            self._sys_labels[key] = v

        info_layout.addStretch()
        row.addWidget(info_card, 1)

        return row

    def _make_gauge_card(self, title, color):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        lbl = QLabel(title)
        lbl.setObjectName("sectionHeader")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        gauge = RingGauge(color=color, size=90, track_width=9)
        layout.addWidget(gauge, alignment=Qt.AlignmentFlag.AlignCenter)

        return card, gauge

    def _make_launch_card(self):
        card = QWidget()
        card.setObjectName("cardGlow")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # Title row
        title_row = QHBoxLayout()
        title_lbl = QLabel("  QUICK LAUNCH")
        title_lbl.setObjectName("cardTitle")
        self._profile_badge = QLabel("NO PROFILE ACTIVE")
        self._profile_badge.setObjectName("topBarBadge")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        title_row.addWidget(self._profile_badge)
        layout.addLayout(title_row)

        # Status message
        self._launch_status = QLabel(
            "Run AUTO SCAN first to detect Gameloop installation.")
        self._launch_status.setObjectName("labelMuted")
        layout.addWidget(self._launch_status)

        # Path display
        self._path_label = QLabel("Install Path: —")
        self._path_label.setStyleSheet(
            "font-size: 11px; color: #5A7090; font-family: Consolas;")
        layout.addWidget(self._path_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._launch_btn = QPushButton("  LAUNCH PUBG MOBILE")
        self._launch_btn.setObjectName("launchBtn")
        self._launch_btn.setEnabled(False)
        self._launch_btn.clicked.connect(self._launch_game)

        rescan_btn = QPushButton("🔄  RESCAN")
        rescan_btn.setObjectName("btnSecondary")
        rescan_btn.clicked.connect(self._run_scan)

        optimize_btn = QPushButton("  QUICK OPTIMIZE")
        optimize_btn.setObjectName("btnPrimary")
        optimize_btn.clicked.connect(self._quick_optimize)

        btn_row.addWidget(self._launch_btn, 2)
        btn_row.addWidget(optimize_btn, 1)
        btn_row.addWidget(rescan_btn, 1)
        layout.addLayout(btn_row)

        return card

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _run_scan(self):
        if self._scanning:
            return
        self._scanning = True

        self._console.clear()
        self._scan_btn.setEnabled(False)
        self._scan_btn.setText("SCANNING...")
        self._launch_btn.setEnabled(False)

        self._scan_thread = QThread()
        self._scan_worker = ScanWorker()
        self._scan_worker.moveToThread(self._scan_thread)

        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_worker.log_line.connect(self._append_console)
        self._scan_worker.finished.connect(self._scan_finished)
        self._scan_worker.finished.connect(self._scan_thread.quit)
        # Do NOT connect deleteLater here — it destroys the C++ object
        # while Python still holds a reference, causing isRunning() to crash.
        # The thread will be garbage-collected naturally when reassigned.

        self._scan_thread.start()

    def _append_console(self, line):
        self._console.append(line)
        self._console.verticalScrollBar().setValue(
            self._console.verticalScrollBar().maximum())

    def _scan_finished(self, result):
        self._scanning = False          # release the guard flag
        self._scan_result = result
        self._scan_btn.setEnabled(True)
        self._scan_btn.setText("AUTO SCAN")

        # Update Gameloop status
        if result["gameloop_found"]:
            self._update_status_card(self._gl_card, "FOUND", "#00FF88")
            self._path_label.setText(
                f"Install Path: {result['gameloop_path']}")
            self._launch_status.setText(
                "Gameloop detected. " +
                ("PUBG Mobile ready to launch! ✓" if result["pubg_found"]
                 else "PUBG Mobile not found — install via App Market.")
            )
        else:
            self._update_status_card(self._gl_card, "NOT FOUND", "#FF3366")
            self._launch_status.setText(
                "Gameloop not found. Please install Gameloop emulator first.")

        if result["pubg_found"]:
            self._update_status_card(self._pubg_card, "INSTALLED", "#00FF88")
            self._launch_btn.setEnabled(True)
        else:
            self._update_status_card(self._pubg_card, "NOT FOUND", "#FF3366")

    def _update_status_card(self, card_tuple, status, color):
        _, dot, val_lbl = card_tuple
        dot.setStyleSheet(f"font-size: 10px; color: {color};")
        val_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {color};")
        val_lbl.setText(status)

    def _launch_game(self):
        if not self._scan_result:
            return
        path = self._scan_result.get("gameloop_path")
        ok, msg = launch_gameloop(path)
        if ok:
            self._append_console(f"\n[✓] Launching Gameloop: {msg}")
            self._launch_status.setText("Gameloop launched! ✓ PUBG Mobile loading...")
        else:
            self._append_console(f"\n[✗] Launch failed: {msg}")
            self._launch_status.setText(f"Launch failed: {msg}")

    def _quick_optimize(self):
        from core.optimizer import (apply_ultimate_power_plan, set_game_mode,
                                     set_core_parking, set_mouse_precision,
                                     disable_nagle_algorithm)
        self._append_console("\n[] Applying quick optimizations...")
        apply_ultimate_power_plan()
        set_game_mode(True)
        set_core_parking(True)
        set_mouse_precision(False)
        disable_nagle_algorithm(True)
        self._append_console("[✓] Power plan → Ultimate Performance")
        self._append_console("[✓] Windows Game Mode enabled")
        self._append_console("[✓] Core parking disabled")
        self._append_console("[✓] Mouse acceleration disabled")
        self._append_console("[✓] Nagle algorithm disabled")
        self._append_console("[✓] Quick optimization complete!")
        self._sys_labels["Optimizations"].setText("Quick Optimize ✓")
        self._sys_labels["Optimizations"].setStyleSheet(
            "font-size: 11px; color: #00FF88; font-weight: 700;")

    def _start_hw_timer(self):
        """Start timer to update hardware gauges."""
        self._hw_timer = QTimer(self)
        self._hw_timer.timeout.connect(self._update_hw)
        self._hw_timer.start(2000)
        self._update_hw()

        # Connection check
        self._conn_timer = QTimer(self)
        self._conn_timer.timeout.connect(self._check_conn)
        self._conn_timer.start(5000)
        self._check_conn()

        # Power plan
        self._info_timer = QTimer(self)
        self._info_timer.timeout.connect(self._update_sys_info)
        self._info_timer.start(10000)
        self._update_sys_info()

    def _update_hw(self):
        cpu = get_cpu_usage()
        ram = get_ram_usage()
        gpu = get_gpu_usage_simple()
        self._cpu_gauge.set_value(int(cpu))
        self._ram_gauge.set_value(int(ram))
        self._gpu_gauge.set_value(int(gpu))

    def _check_conn(self):
        from core.network_tools import check_internet, ping_host
        if check_internet():
            ms = ping_host("8.8.8.8")
            txt = f"Online ({ms}ms)" if ms else "Online"
            self._update_status_card(self._conn_card, txt, "#00FF88")
        else:
            self._update_status_card(self._conn_card, "Offline", "#FF3366")

    def _update_sys_info(self):
        from core.system_info import get_power_plan
        plan = get_power_plan()
        self._sys_labels["Power Plan"].setText(plan)
        self._sys_labels["Active Profile"].setText("Mid-Range")
