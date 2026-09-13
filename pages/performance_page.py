"""
Performance & Hardware Page — RT Tool
GPU, CPU, RAM, Latency optimization controls.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QFrame, QScrollArea, QGridLayout,
    QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from ui.widgets.toggle_switch import ToggleSwitch
from ui.widgets.ring_gauge import RingGauge
from core import optimizer, system_info


def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    return f


def _make_label(text, obj="labelPrimary"):
    l = QLabel(text)
    l.setObjectName(obj)
    return l


class ToggleRow(QWidget):
    """A row with label, description, and toggle."""
    toggled = pyqtSignal(bool)

    def __init__(self, title, desc="", color="#FF6B00", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("labelPrimary")
        text_col.addWidget(title_lbl)
        if desc:
            desc_lbl = QLabel(desc)
            desc_lbl.setObjectName("labelMuted")
            desc_lbl.setWordWrap(True)
            text_col.addWidget(desc_lbl)
        layout.addLayout(text_col, 1)

        self._toggle = ToggleSwitch(color_on=color)
        self._toggle.toggled.connect(self.toggled.emit)
        layout.addWidget(self._toggle)

    def is_checked(self):
        return self._toggle.isChecked()

    def set_checked(self, v, block=False):
        if block:
            self._toggle.blockSignals(True)
        self._toggle.setChecked(v)
        if block:
            self._toggle.blockSignals(False)


class SliderRow(QWidget):
    """A row with label, slider, and current value."""
    changed = pyqtSignal(int)

    def __init__(self, title, min_val=0, max_val=100, default=50,
                 unit="", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        lbl = QLabel(title)
        lbl.setObjectName("labelPrimary")
        lbl.setMinimumWidth(160)
        layout.addWidget(lbl)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setMinimum(min_val)
        self._slider.setMaximum(max_val)
        self._slider.setValue(default)
        self._slider.valueChanged.connect(self._on_change)
        layout.addWidget(self._slider, 1)

        self._val_lbl = QLabel(f"{default}{unit}")
        self._val_lbl.setObjectName("labelOrange")
        self._val_lbl.setMinimumWidth(55)
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._val_lbl)
        self._unit = unit

    def _on_change(self, v):
        self._val_lbl.setText(f"{v}{self._unit}")
        self.changed.emit(v)

    def value(self):
        return self._slider.value()


class PerformancePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._start_timer()
        self._connect_signals()

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
        hdr = QVBoxLayout()
        hdr.addWidget(_make_label("Performance & Hardware", "pageTitle"))
        hdr.addWidget(_make_label(
            "GPU · CPU · RAM · Latency optimization controls", "pageSubtitle"))
        layout.addLayout(hdr)

        # Live gauges row
        layout.addWidget(self._make_live_gauges())

        # GPU Section
        layout.addWidget(self._make_gpu_section())

        # CPU Section
        layout.addWidget(self._make_cpu_section())

        # RAM Section
        layout.addWidget(self._make_ram_section())

        # Latency Section
        layout.addWidget(self._make_latency_section())

        # Apply / Reset buttons
        layout.addLayout(self._make_apply_row())

        layout.addStretch()

    def _make_live_gauges(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QHBoxLayout(card)
        layout.setSpacing(20)

        # CPU gauge
        cpu_col = QVBoxLayout()
        cpu_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cpu_gauge = RingGauge(label="CPU", color="#FFD700", size=90, track_width=9)
        self._cpu_pb = QProgressBar()
        self._cpu_pb.setObjectName("pbCyan")
        cpu_col.addWidget(self._cpu_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        self._cpu_info_lbl = QLabel("Loading...")
        self._cpu_info_lbl.setObjectName("labelMuted")
        self._cpu_info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cpu_col.addWidget(self._cpu_info_lbl)
        layout.addLayout(cpu_col, 1)

        # GPU gauge
        gpu_col = QVBoxLayout()
        gpu_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._gpu_gauge = RingGauge(label="GPU", color="#FF6B00", size=90, track_width=9)
        gpu_col.addWidget(self._gpu_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        self._gpu_info_lbl = QLabel("Loading...")
        self._gpu_info_lbl.setObjectName("labelMuted")
        self._gpu_info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gpu_col.addWidget(self._gpu_info_lbl)
        layout.addLayout(gpu_col, 1)

        # RAM gauge
        ram_col = QVBoxLayout()
        ram_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ram_gauge = RingGauge(label="RAM", color="#A070FF", size=90, track_width=9)
        ram_col.addWidget(self._ram_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        self._ram_info_lbl = QLabel("Loading...")
        self._ram_info_lbl.setObjectName("labelMuted")
        self._ram_info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ram_col.addWidget(self._ram_info_lbl)
        layout.addLayout(ram_col, 1)

        # Temp / Freq info
        info_col = QVBoxLayout()
        info_col.setSpacing(10)
        lbl = _make_label("LIVE METRICS", "cardTitle")
        info_col.addWidget(lbl)

        self._metric_labels = {}
        for key in ["CPU Temp", "GPU Temp", "CPU Freq", "GPU VRAM", "Power Plan"]:
            row = QHBoxLayout()
            k = QLabel(key + ":")
            k.setObjectName("labelMuted")
            k.setStyleSheet("font-size: 11px;")
            v = QLabel("—")
            v.setStyleSheet("font-size: 12px; font-weight: 600; color: #DCE8FF;")
            row.addWidget(k)
            row.addStretch()
            row.addWidget(v)
            info_col.addLayout(row)
            self._metric_labels[key] = v

        info_col.addStretch()
        layout.addLayout(info_col, 1)

        return card

    def _make_gpu_section(self):
        card = QWidget()
        card.setObjectName("cardGlow")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("GPU OPTIMIZATION")
        title.setObjectName("cardTitle")
        self._gpu_name_lbl = QLabel("Detecting...")
        self._gpu_name_lbl.setObjectName("labelOrange")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._gpu_name_lbl)
        layout.addLayout(header)
        layout.addWidget(_sep())

        self._tr_force_gpu = ToggleRow(
            "Force Dedicated GPU",
            "Override Windows GPU selection — always use your NVIDIA/AMD card",
            "#FF6B00"
        )
        self._tr_gpu_priority = ToggleRow(
            "High Priority GPU Scheduling",
            "Reduce render latency via HAGS (Windows 10 2004+)",
            "#FF6B00"
        )
        self._tr_cuda = ToggleRow(
            "CUDA Optimization (NVIDIA)",
            "Optimize CUDA workload scheduling for emulator rendering",
            "#FF6B00"
        )

        self._sl_vram = SliderRow(
            "VRAM Allocation Priority", 50, 100, 80, "%"
        )
        self._sl_gpu_power = SliderRow(
            "GPU Power Limit", 50, 100, 100, "%"
        )

        for w in [self._tr_force_gpu, self._tr_gpu_priority, self._tr_cuda,
                  _sep(), self._sl_vram, self._sl_gpu_power]:
            layout.addWidget(w)

        return card

    def _make_cpu_section(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        title = QLabel("CPU OPTIMIZATION")
        title.setObjectName("cardTitle")
        layout.addWidget(title)
        layout.addWidget(_sep())

        self._tr_core_park = ToggleRow(
            "Disable Core Parking",
            "Keep all CPU cores active — prevents thread scheduling delays",
            "#FFD700"
        )
        self._tr_priority = ToggleRow(
            "Process Priority Boost",
            "Set Gameloop to HIGH priority in Windows Task Scheduler",
            "#FFD700"
        )
        self._tr_gamemode = ToggleRow(
            "Windows Game Mode",
            "Allocate maximum CPU/GPU resources to the foreground game",
            "#FFD700"
        )
        self._tr_hpet = ToggleRow(
            "High Resolution Timer",
            "Set 0.5ms timer resolution for precise CPU scheduling",
            "#FFD700"
        )
        self._tr_visual_fx = ToggleRow(
            "Disable Visual Effects",
            "Turn off Windows animations/effects to free CPU cycles",
            "#FFD700"
        )

        self._sl_threads = SliderRow(
            "Emulator Thread Count", 2, 16, 4, " threads"
        )

        self._priority_combo = QComboBox()
        self._priority_combo.addItems(["Normal", "Above Normal", "High", "Realtime"])
        self._priority_combo.setCurrentText("High")

        priority_row = QHBoxLayout()
        priority_row.addWidget(_make_label("Priority Level:"))
        priority_row.addStretch()
        priority_row.addWidget(self._priority_combo)

        for w in [self._tr_core_park, self._tr_priority, self._tr_gamemode,
                  self._tr_hpet, self._tr_visual_fx, _sep(),
                  self._sl_threads]:
            layout.addWidget(w)
        layout.addLayout(priority_row)

        return card

    def _make_ram_section(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        title = QLabel("💾  RAM OPTIMIZATION")
        title.setObjectName("cardTitle")
        layout.addWidget(title)
        layout.addWidget(_sep())

        # RAM info bar
        ram_info = QHBoxLayout()
        self._ram_used_lbl = QLabel("Used: — GB")
        self._ram_used_lbl.setObjectName("labelOrange")
        self._ram_total_lbl = QLabel("Total: — GB")
        self._ram_total_lbl.setObjectName("labelMuted")
        self._ram_avail_lbl = QLabel("Available: — GB")
        self._ram_avail_lbl.setObjectName("labelGreen")
        ram_info.addWidget(self._ram_used_lbl)
        ram_info.addStretch()
        ram_info.addWidget(self._ram_avail_lbl)
        ram_info.addStretch()
        ram_info.addWidget(self._ram_total_lbl)
        layout.addLayout(ram_info)

        self._ram_pb = QProgressBar()
        self._ram_pb.setObjectName("pbCyan")
        self._ram_pb.setValue(0)
        layout.addWidget(self._ram_pb)
        layout.addWidget(_sep())

        self._tr_ram_clean = ToggleRow(
            "Auto RAM Cleanup",
            "Periodically clear standby memory to free RAM for emulator",
            "#A070FF"
        )
        self._sl_ram_alloc = SliderRow(
            "Emulator RAM Allocation", 512, 8192, 2048, " MB"
        )

        for w in [self._tr_ram_clean, self._sl_ram_alloc]:
            layout.addWidget(w)

        btn_row = QHBoxLayout()
        clean_now_btn = QPushButton("🧹  CLEAN RAM NOW")
        clean_now_btn.setObjectName("btnPrimary")
        clean_now_btn.clicked.connect(self._clean_ram_now)
        btn_row.addStretch()
        btn_row.addWidget(clean_now_btn)
        layout.addLayout(btn_row)

        return card

    def _make_latency_section(self):
        card = QWidget()
        card.setObjectName("cardBlue")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        title = QLabel("LATENCY REDUCTION PIPELINE")
        title.setObjectName("cardTitle")
        layout.addWidget(title)
        layout.addWidget(_sep())

        self._tr_sys_latency = ToggleRow(
            "System Latency Reduction",
            "Optimize Windows scheduler interrupt timing (bcdedit tweaks)",
            "#00C8FF"
        )
        self._tr_input_latency = ToggleRow(
            "Input Latency Reduction",
            "Raw input mode + disable input buffering",
            "#00C8FF"
        )
        self._tr_net_latency = ToggleRow(
            "Network Latency Reduction",
            "Disable Nagle algorithm, optimize TCP ACK frequency",
            "#00C8FF"
        )
        self._tr_render_latency = ToggleRow(
            "Render Latency Reduction",
            "Frame pacing + pre-rendered frame limit",
            "#00C8FF"
        )
        self._tr_stutter = ToggleRow(
            "Stutter Elimination",
            "Frame time smoothing + GPU scheduler optimization",
            "#00C8FF"
        )

        for w in [self._tr_sys_latency, self._tr_input_latency,
                  self._tr_net_latency, self._tr_render_latency,
                  self._tr_stutter]:
            layout.addWidget(w)

        return card

    def _make_apply_row(self):
        row = QHBoxLayout()
        row.setSpacing(10)

        apply_btn = QPushButton("Apply All Optimizations")
        apply_btn.setObjectName("btnPrimary")
        apply_btn.setMinimumHeight(38)
        apply_btn.clicked.connect(self._apply_all)

        reset_btn = QPushButton("Restore Defaults")
        reset_btn.setObjectName("btnSecondary")
        reset_btn.setMinimumHeight(38)
        reset_btn.clicked.connect(self._restore_defaults)

        self._apply_status_lbl = QLabel("")
        self._apply_status_lbl.setStyleSheet("color: #00FF88; font-size: 11px;")

        row.addWidget(apply_btn, 2)
        row.addWidget(reset_btn, 1)
        row.addWidget(self._apply_status_lbl)
        return row

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self._tr_force_gpu.toggled.connect(
            lambda v: optimizer.force_dedicated_gpu(enable=v))
        self._tr_core_park.toggled.connect(
            lambda v: optimizer.set_core_parking(disabled=v))
        self._tr_gamemode.toggled.connect(optimizer.set_game_mode)
        self._tr_hpet.toggled.connect(optimizer.set_timer_resolution)
        self._tr_visual_fx.toggled.connect(optimizer.optimize_visual_effects)
        self._tr_net_latency.toggled.connect(
            lambda v: optimizer.disable_nagle_algorithm(v))
        self._tr_priority.toggled.connect(
            lambda v: optimizer.set_gameloop_priority("high" if v else "normal"))
        self._tr_ram_clean.toggled.connect(
            lambda v: optimizer.clear_ram_standby() if v else None)
        self._tr_sys_latency.toggled.connect(
            lambda v: optimizer.set_timer_resolution(v))

    def _clean_ram_now(self):
        ok, msg = optimizer.clear_ram_standby()

    def _apply_all(self):
        from PyQt6.QtCore import QThread
        self._apply_status_lbl.setText("Applying...")

        def _do_apply():
            optimizer.apply_ultimate_power_plan()
            optimizer.set_game_mode(True)
            optimizer.set_core_parking(True)
            optimizer.force_dedicated_gpu(enable=True)
            optimizer.set_mouse_precision(False)
            optimizer.disable_nagle_algorithm(True)
            optimizer.optimize_visual_effects(True)
            optimizer.set_timer_resolution(True)
            optimizer.optimize_network_adapter()

        import threading
        t = threading.Thread(target=_do_apply, daemon=True)
        t.start()

        # Sync toggles immediately (UI doesn't wait for thread)
        for tr in [self._tr_core_park, self._tr_priority, self._tr_gamemode,
                   self._tr_hpet, self._tr_visual_fx, self._tr_force_gpu,
                   self._tr_sys_latency, self._tr_net_latency,
                   self._tr_stutter]:
            tr.set_checked(True, block=True)
        self._apply_status_lbl.setText("Applied!")
        QTimer.singleShot(3000, lambda: self._apply_status_lbl.setText(""))

    def _restore_defaults(self):
        import threading
        self._apply_status_lbl.setText("Restoring...")

        def _do_restore():
            optimizer.restore_defaults()

        threading.Thread(target=_do_restore, daemon=True).start()

        for tr in [self._tr_core_park, self._tr_priority, self._tr_gamemode,
                   self._tr_hpet, self._tr_visual_fx, self._tr_force_gpu,
                   self._tr_sys_latency, self._tr_net_latency,
                   self._tr_stutter, self._tr_cuda, self._tr_gpu_priority,
                   self._tr_input_latency, self._tr_render_latency,
                   self._tr_ram_clean]:
            tr.set_checked(False, block=True)
        self._apply_status_lbl.setText("Defaults Restored")
        QTimer.singleShot(3000, lambda: self._apply_status_lbl.setText(""))

    def _start_timer(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_live)
        self._timer.start(2500)
        self._update_live()

    def _update_live(self):
        # CPU
        cpu_info = system_info.get_cpu_info()
        self._cpu_gauge.set_value(int(cpu_info["usage"]))
        self._cpu_info_lbl.setText(
            f"{cpu_info['cores_physical']}C/{cpu_info['cores_logical']}T · "
            f"{cpu_info['freq_mhz']} MHz")
        self._metric_labels["CPU Temp"].setText(
            f"{cpu_info['temp']}°C" if cpu_info['temp'] else "N/A")
        self._metric_labels["CPU Freq"].setText(f"{cpu_info['freq_mhz']} MHz")

        # GPU
        gpu_info = system_info.get_gpu_info()
        self._gpu_gauge.set_value(int(gpu_info["usage"]))
        self._gpu_name_lbl.setText(gpu_info["name"][:30])
        self._gpu_info_lbl.setText(
            f"{gpu_info['vram_used']}/{gpu_info['vram_total']} MB VRAM")
        self._metric_labels["GPU Temp"].setText(
            f"{gpu_info['temp']}°C" if gpu_info['temp'] else "N/A")
        self._metric_labels["GPU VRAM"].setText(
            f"{gpu_info['vram_used']}/{gpu_info['vram_total']} MB")

        # RAM
        ram_info = system_info.get_ram_info()
        self._ram_gauge.set_value(int(ram_info["percent"]))
        self._ram_used_lbl.setText(f"Used: {ram_info['used_gb']} GB")
        self._ram_total_lbl.setText(f"Total: {ram_info['total_gb']} GB")
        self._ram_avail_lbl.setText(f"Available: {ram_info['available_gb']} GB")
        self._ram_pb.setValue(int(ram_info["percent"]))

        # Power plan
        from core.system_info import get_power_plan
        self._metric_labels["Power Plan"].setText(get_power_plan()[:20])
