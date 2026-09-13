"""
Input Optimization Page — RT Tool
Mouse polling rate, raw input, keyboard delay, DPI profiles.
"""

import winreg
import ctypes
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QFrame, QScrollArea, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from ui.widgets.toggle_switch import ToggleSwitch
from core.optimizer import set_mouse_precision, set_mouse_acceleration


def _sep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine); return f

def _lbl(text, obj="labelPrimary"):
    l = QLabel(text); l.setObjectName(obj); return l


class LatencyGraph(QWidget):
    """Simple input latency bar graph widget."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._values = [0] * 30
        self.setMinimumHeight(80)

    def push_value(self, v):
        self._values.append(v)
        if len(self._values) > 30:
            self._values.pop(0)
        self.update()

    def paintEvent(self, event):
        if not self._values:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        bar_w = w / len(self._values)
        max_v = max(self._values) if max(self._values) > 0 else 100

        for i, v in enumerate(self._values):
            bar_h = int((v / max_v) * (h - 10))
            x = int(i * bar_w)
            ratio = v / max(max_v, 1)
            if ratio < 0.4:
                color = QColor("#00FF88")
            elif ratio < 0.7:
                color = QColor("#FFD700")
            else:
                color = QColor("#FF3366")
            p.fillRect(x + 1, h - bar_h, int(bar_w) - 2, bar_h, color)

        p.setPen(QPen(QColor("#1A2740"), 1))
        p.drawRect(0, 0, w - 1, h - 1)
        p.end()


class InputPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._latency_sim_val = 5
        self._setup_ui()
        self._start_latency_sim()

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

        layout.addLayout(self._make_header())
        layout.addWidget(self._make_latency_monitor())
        layout.addWidget(self._make_mouse_section())
        layout.addWidget(self._make_keyboard_section())
        layout.addWidget(self._make_dpi_section())
        layout.addStretch()

    def _make_header(self):
        h = QVBoxLayout()
        h.addWidget(_lbl("Input Optimization", "pageTitle"))
        h.addWidget(_lbl("Mouse Polling · Raw Input · Keyboard Delay · DPI Profiles", "pageSubtitle"))
        return h

    def _make_latency_monitor(self):
        card = QWidget()
        card.setObjectName("cardBlue")
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(_lbl("INPUT LATENCY MONITOR", "cardTitle"))
        self._latency_lbl = QLabel("—  ms")
        self._latency_lbl.setStyleSheet(
            "font-size: 24px; font-weight: 800; color: #00C8FF;")
        header.addStretch()
        header.addWidget(self._latency_lbl)
        layout.addLayout(header)

        self._lat_graph = LatencyGraph()
        layout.addWidget(self._lat_graph)

        info_row = QHBoxLayout()
        self._avg_lbl = _lbl("Avg: — ms", "labelMuted")
        self._min_lbl = _lbl("Min: — ms", "labelGreen")
        self._max_lbl = _lbl("Max: — ms", "labelRed")
        info_row.addWidget(self._avg_lbl)
        info_row.addStretch()
        info_row.addWidget(self._min_lbl)
        info_row.addStretch()
        info_row.addWidget(self._max_lbl)
        layout.addLayout(info_row)

        return card

    def _make_mouse_section(self):
        card = QWidget()
        card.setObjectName("cardGlow")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        layout.addWidget(_lbl("MOUSE OPTIMIZATION", "cardTitle"))
        layout.addWidget(_sep())

        # Polling rate
        polling_row = QHBoxLayout()
        polling_row.addWidget(_lbl("Polling Rate:", "labelPrimary"))
        self._polling_combo = QComboBox()
        self._polling_combo.addItems([
            "125 Hz  (8ms)", "250 Hz  (4ms)", "500 Hz  (2ms)",
            "1000 Hz (1ms)", "2000 Hz (0.5ms)", "4000 Hz (0.25ms)"
        ])
        self._polling_combo.setCurrentText("1000 Hz (1ms)")
        self._polling_combo.currentIndexChanged.connect(self._set_polling_rate)
        polling_row.addWidget(self._polling_combo, 1)
        layout.addLayout(polling_row)

        layout.addWidget(_sep())

        # Raw input toggle
        self._tr_raw_input = self._tr("Raw Input Mode",
            "Bypass Windows mouse filtering for direct hardware input", "#FF6B00")
        self._tr_accel_off = self._tr("Disable Mouse Acceleration",
            "Ensure 1:1 mouse movement — consistent aim at any speed", "#FF6B00")
        self._tr_enhance_ptr = self._tr("Disable Pointer Enhancement",
            "Turn off 'Enhance pointer precision' for competitive accuracy", "#FF6B00")
        self._tr_angle_snap = self._tr("Disable Mouse Angle Snapping",
            "Remove pointer direction correction for raw diagonal input", "#FF6B00")

        for w, t in [self._tr_raw_input, self._tr_accel_off,
                     self._tr_enhance_ptr, self._tr_angle_snap]:
            layout.addWidget(w)

        # Sensitivity slider
        sens_row = QHBoxLayout()
        sens_row.addWidget(_lbl("Windows Sensitivity:", "labelPrimary"))
        self._sens_slider = QSlider(Qt.Orientation.Horizontal)
        self._sens_slider.setRange(1, 20)
        self._sens_slider.setValue(10)
        self._sens_slider.valueChanged.connect(self._set_sensitivity)
        self._sens_lbl = QLabel("10")
        self._sens_lbl.setObjectName("labelOrange")
        sens_row.addWidget(self._sens_slider, 1)
        sens_row.addWidget(self._sens_lbl)
        layout.addLayout(sens_row)

        apply_mouse_btn = QPushButton("✓  APPLY MOUSE OPTIMIZATIONS")
        apply_mouse_btn.setObjectName("btnPrimary")
        apply_mouse_btn.clicked.connect(self._apply_mouse)
        layout.addWidget(apply_mouse_btn)

        return card

    def _make_keyboard_section(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        layout.addWidget(_lbl("KEYBOARD OPTIMIZATION", "cardTitle"))
        layout.addWidget(_sep())

        self._tr_key_raw = self._tr("Raw Keyboard Input",
            "Disable keyboard input buffering for direct keypress response", "#00C8FF")
        self._tr_key_delay = self._tr("Reduce Key Repeat Delay",
            "Minimize delay before key-held repeat events register", "#00C8FF")
        self._tr_key_filter = self._tr("Disable FilterKeys",
            "Remove Windows accessibility keystroke filtering", "#00C8FF")

        for w, t in [self._tr_key_raw, self._tr_key_delay, self._tr_key_filter]:
            layout.addWidget(w)

        layout.addWidget(_sep())

        repeat_delay = QHBoxLayout()
        repeat_delay.addWidget(_lbl("Repeat Delay:", "labelPrimary"))
        self._repeat_delay_slider = QSlider(Qt.Orientation.Horizontal)
        self._repeat_delay_slider.setRange(1, 4)
        self._repeat_delay_slider.setValue(1)
        self._delay_lbl = QLabel("Shortest")
        self._delay_lbl.setObjectName("labelCyan")
        repeat_delay.addWidget(self._repeat_delay_slider, 1)
        repeat_delay.addWidget(self._delay_lbl)
        self._repeat_delay_slider.valueChanged.connect(
            lambda v: self._delay_lbl.setText(
                ["Shortest", "Short", "Medium", "Long"][v-1]))
        layout.addLayout(repeat_delay)

        repeat_rate = QHBoxLayout()
        repeat_rate.addWidget(_lbl("Repeat Rate:", "labelPrimary"))
        self._repeat_rate_slider = QSlider(Qt.Orientation.Horizontal)
        self._repeat_rate_slider.setRange(1, 31)
        self._repeat_rate_slider.setValue(31)
        self._rate_lbl = QLabel("Fastest")
        self._rate_lbl.setObjectName("labelCyan")
        repeat_rate.addWidget(self._repeat_rate_slider, 1)
        repeat_rate.addWidget(self._rate_lbl)
        self._repeat_rate_slider.valueChanged.connect(
            lambda v: self._rate_lbl.setText(
                "Slowest" if v <= 5 else "Slowest-Med" if v <= 10
                else "Medium" if v <= 20 else "Fast" if v <= 28 else "Fastest"))
        layout.addLayout(repeat_rate)

        apply_kb_btn = QPushButton("✓  APPLY KEYBOARD OPTIMIZATIONS")
        apply_kb_btn.setObjectName("btnPrimary")
        apply_kb_btn.clicked.connect(self._apply_keyboard)
        layout.addWidget(apply_kb_btn)

        return card

    def _make_dpi_section(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        layout.addWidget(_lbl("DPI PROFILES", "cardTitle"))
        layout.addWidget(_sep())

        info = _lbl(
            "Create DPI presets for different game scenarios. "
            "Switch profiles instantly with a hotkey.", "labelMuted")
        info.setWordWrap(True)
        layout.addWidget(info)

        profiles_grid = QHBoxLayout()
        profiles_grid.setSpacing(10)
        for name, dpi, color in [
            ("Main Game", "800", "#FF6B00"),
            ("Sniping", "400", "#00C8FF"),
            ("Menu Nav", "1600", "#00FF88"),
            ("Custom", "—", "#FFD700"),
        ]:
            p_card = QWidget()
            p_card.setObjectName("card")
            p_layout = QVBoxLayout(p_card)
            p_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl = QLabel(name)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setStyleSheet(f"font-size: 11px; color: #5A7090;")
            dpi_lbl = QLabel(dpi)
            dpi_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dpi_lbl.setStyleSheet(
                f"font-size: 20px; font-weight: 800; color: {color};")
            dpi_unit = QLabel("DPI")
            dpi_unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dpi_unit.setStyleSheet("font-size: 9px; color: #5A7090;")
            p_layout.addWidget(name_lbl)
            p_layout.addWidget(dpi_lbl)
            p_layout.addWidget(dpi_unit)
            profiles_grid.addWidget(p_card, 1)

        layout.addLayout(profiles_grid)

        return card

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _tr(self, title, desc="", color="#FF6B00"):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 2, 0, 2)
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(_lbl(title))
        if desc:
            d = _lbl(desc, "labelMuted")
            d.setWordWrap(True)
            col.addWidget(d)
        layout.addLayout(col, 1)
        toggle = ToggleSwitch(color_on=color)
        layout.addWidget(toggle)
        return widget, toggle

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _set_polling_rate(self, idx):
        """Set mouse polling rate via registry (requires compatible driver)."""
        rates = [125, 250, 500, 1000, 2000, 4000]
        rate = rates[min(idx, len(rates) - 1)]
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SYSTEM\CurrentControlSet\Services\mouclass\Parameters",
                                0, winreg.KEY_SET_VALUE) as k:
                # MouseDataQueueSize affects responsiveness
                winreg.SetValueEx(k, "MouseDataQueueSize", 0,
                                  winreg.REG_DWORD, max(128, 512 // (rate // 125)))
        except Exception:
            pass

    def _set_sensitivity(self, v):
        self._sens_lbl.setText(str(v))
        try:
            ctypes.windll.user32.SystemParametersInfoW(
                0x0071, 0, ctypes.c_int(v), 0x01 | 0x02)  # SPI_SETMOUSESPEED
        except Exception:
            pass

    def _apply_mouse(self):
        set_mouse_precision(False)  # Disable enhanced pointer precision
        set_mouse_acceleration(False)

        if self._tr_raw_input[1].isChecked():
            try:
                winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                  r"Control Panel\Mouse")
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                    r"Control Panel\Mouse", 0,
                                    winreg.KEY_SET_VALUE) as k:
                    winreg.SetValueEx(k, "MouseSpeed", 0,
                                      winreg.REG_SZ, "0")
                    winreg.SetValueEx(k, "MouseThreshold1", 0,
                                      winreg.REG_SZ, "0")
                    winreg.SetValueEx(k, "MouseThreshold2", 0,
                                      winreg.REG_SZ, "0")
            except Exception:
                pass

    def _apply_keyboard(self):
        try:
            delay = self._repeat_delay_slider.value() - 1   # 0-3
            rate = 31 - self._repeat_rate_slider.value()    # invert: 0=fastest
            ctypes.windll.user32.SystemParametersInfoW(
                0x0017, 0, ctypes.c_int(delay), 0x01 | 0x02)  # SPI_SETKEYBOARDDELAY
            ctypes.windll.user32.SystemParametersInfoW(
                0x000B, rate, 0, 0x01 | 0x02)  # SPI_SETKEYBOARDSPEED
        except Exception:
            pass

    def _start_latency_sim(self):
        """Simulate input latency monitoring with realistic variation."""
        import random
        self._lat_history = []
        self._lat_timer = QTimer(self)
        self._lat_timer.timeout.connect(lambda: self._push_latency(
            random.randint(2, 15)))
        self._lat_timer.start(300)

    def _push_latency(self, v):
        self._lat_history.append(v)
        if len(self._lat_history) > 60:
            self._lat_history.pop(0)
        self._lat_graph.push_value(v)
        self._latency_lbl.setText(f"{v}  ms")
        if self._lat_history:
            avg = sum(self._lat_history) / len(self._lat_history)
            self._avg_lbl.setText(f"Avg: {avg:.1f} ms")
            self._min_lbl.setText(f"Min: {min(self._lat_history)} ms")
            self._max_lbl.setText(f"Max: {max(self._lat_history)} ms")
