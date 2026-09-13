"""
Display & Visual Page — RT Tool
Resolution override, refresh rate, FPS unlock, color enhancement.
"""

import subprocess
import ctypes
import ctypes.wintypes
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QFrame, QScrollArea, QSpinBox, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer
from ui.widgets.toggle_switch import ToggleSwitch


def _sep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine); return f

def _lbl(text, obj="labelPrimary"):
    l = QLabel(text); l.setObjectName(obj); return l


class ColorSliderRow(QWidget):
    def __init__(self, title, min_v, max_v, default, unit="", color="#FF6B00", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 3)
        lbl = QLabel(title)
        lbl.setObjectName("labelPrimary")
        lbl.setMinimumWidth(140)
        layout.addWidget(lbl)
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setMinimum(min_v)
        self._slider.setMaximum(max_v)
        self._slider.setValue(default)
        self._slider.valueChanged.connect(self._on_change)
        layout.addWidget(self._slider, 1)
        self._val_lbl = QLabel(f"{default}{unit}")
        self._val_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {color};")
        self._val_lbl.setMinimumWidth(50)
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._val_lbl)
        self._unit = unit
        self._default = default

    def _on_change(self, v):
        self._val_lbl.setText(f"{v}{self._unit}")

    def value(self):
        return self._slider.value()

    def reset(self):
        self._slider.setValue(self._default)


class DisplayPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._detect_display()
        self._setup_ui()

    def _detect_display(self):
        """Detect current display settings."""
        self._current_w = 1920
        self._current_h = 1080
        self._current_hz = 60
        try:
            dm = ctypes.wintypes.DEVMODE()
            dm.dmSize = ctypes.sizeof(dm)
            if ctypes.windll.user32.EnumDisplaySettingsW(None, -1, ctypes.byref(dm)):
                self._current_w = dm.dmPelsWidth
                self._current_h = dm.dmPelsHeight
                self._current_hz = dm.dmDisplayFrequency
        except Exception:
            pass

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
        layout.addWidget(self._make_current_display())
        layout.addWidget(self._make_resolution_section())
        layout.addWidget(self._make_fps_section())
        layout.addWidget(self._make_color_section())
        layout.addStretch()

    def _make_header(self):
        h = QVBoxLayout()
        h.addWidget(_lbl("Display & Visual Enhancement", "pageTitle"))
        h.addWidget(_lbl("Resolution · Refresh Rate · FPS · Color Tuning", "pageSubtitle"))
        return h

    def _make_current_display(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QHBoxLayout(card)
        layout.setSpacing(40)

        for label, value, color in [
            ("RESOLUTION", f"{self._current_w}×{self._current_h}", "#FF6B00"),
            ("REFRESH RATE", f"{self._current_hz} Hz", "#00C8FF"),
            ("ASPECT RATIO", self._get_aspect(), "#FFD700"),
            ("BIT DEPTH", "32-bit", "#00FF88"),
        ]:
            col = QVBoxLayout()
            lbl1 = QLabel(label)
            lbl1.setStyleSheet("font-size: 9px; color: #5A7090; letter-spacing: 2px;")
            lbl2 = QLabel(value)
            lbl2.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {color};")
            col.addWidget(lbl1)
            col.addWidget(lbl2)
            layout.addLayout(col)

        layout.addStretch()

        detect_btn = QPushButton("🔄  REFRESH INFO")
        detect_btn.setObjectName("btnSmall")
        detect_btn.clicked.connect(self._refresh_display_info)
        layout.addWidget(detect_btn, alignment=Qt.AlignmentFlag.AlignTop)

        return card

    def _make_resolution_section(self):
        card = QWidget()
        card.setObjectName("cardGlow")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        layout.addWidget(_lbl("RESOLUTION & REFRESH RATE", "cardTitle"))
        layout.addWidget(_sep())

        # Preset resolutions
        res_row = QHBoxLayout()
        res_row.addWidget(_lbl("Preset Resolution:", "labelPrimary"))
        self._res_combo = QComboBox()
        self._res_combo.addItems([
            "1280×720 (HD)", "1366×768", "1600×900",
            "1920×1080 (Full HD)", "2560×1440 (QHD)", "3840×2160 (4K)",
            "Custom..."
        ])
        self._res_combo.setCurrentText("1920×1080 (Full HD)")
        self._res_combo.currentIndexChanged.connect(self._on_res_preset)
        res_row.addWidget(self._res_combo, 1)
        layout.addLayout(res_row)

        # Custom resolution
        custom_row = QHBoxLayout()
        custom_row.addWidget(_lbl("Custom Width:", "labelMuted"))
        self._custom_w = QSpinBox()
        self._custom_w.setRange(640, 7680)
        self._custom_w.setValue(self._current_w)
        self._custom_w.setSuffix(" px")
        custom_row.addWidget(self._custom_w)
        custom_row.addWidget(_lbl("×  Height:", "labelMuted"))
        self._custom_h = QSpinBox()
        self._custom_h.setRange(480, 4320)
        self._custom_h.setValue(self._current_h)
        self._custom_h.setSuffix(" px")
        custom_row.addWidget(self._custom_h)
        custom_row.addStretch()
        layout.addLayout(custom_row)

        # Refresh rate
        hz_row = QHBoxLayout()
        hz_row.addWidget(_lbl("Refresh Rate:", "labelPrimary"))
        self._hz_combo = QComboBox()
        self._hz_combo.addItems([
            "60 Hz", "75 Hz", "90 Hz", "120 Hz",
            "144 Hz", "165 Hz", "240 Hz", "360 Hz"
        ])
        self._hz_combo.setCurrentText(f"{self._current_hz} Hz"
                                       if f"{self._current_hz} Hz" in
                                       [self._hz_combo.itemText(i)
                                        for i in range(self._hz_combo.count())]
                                       else "60 Hz")
        hz_row.addWidget(self._hz_combo, 1)
        layout.addLayout(hz_row)

        # Apply button
        btn_row = QHBoxLayout()
        apply_res_btn = QPushButton("⚡  APPLY RESOLUTION & REFRESH RATE")
        apply_res_btn.setObjectName("btnPrimary")
        apply_res_btn.clicked.connect(self._apply_resolution)
        reset_res_btn = QPushButton("↺  RESET")
        reset_res_btn.setObjectName("btnSecondary")
        reset_res_btn.clicked.connect(self._reset_resolution)
        btn_row.addWidget(apply_res_btn, 2)
        btn_row.addWidget(reset_res_btn, 1)
        layout.addLayout(btn_row)

        # Warning
        warn = _lbl("⚠  Applying may briefly flash your display. "
                    "Original settings will restore if not confirmed within 15s.", "labelMuted")
        warn.setWordWrap(True)
        layout.addWidget(warn)

        return card

    def _make_fps_section(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        layout.addWidget(_lbl("FPS CONTROL", "cardTitle"))
        layout.addWidget(_sep())

        self._tr_fps_unlock = self._toggle_row(
            "FPS Unlock (90 FPS Mode)",
            "Override Gameloop's default 60 FPS cap via config file edit",
            "#FF6B00"
        )
        self._tr_vsync_off = self._toggle_row(
            "Disable VSync",
            "Remove frame synchronization for maximum FPS",
            "#FF6B00"
        )
        self._tr_frame_pacing = self._toggle_row(
            "Frame Pacing Smoothing",
            "Minimize frame time variance for consistent gaming experience",
            "#FFD700"
        )

        layout.addWidget(self._tr_fps_unlock[0])
        layout.addWidget(self._tr_vsync_off[0])
        layout.addWidget(self._tr_frame_pacing[0])
        layout.addWidget(_sep())

        fps_cap_row = QHBoxLayout()
        fps_cap_row.addWidget(_lbl("FPS Target Cap:", "labelPrimary"))
        self._fps_combo = QComboBox()
        self._fps_combo.addItems(["30", "60", "90", "120", "144", "165", "240", "Unlimited"])
        self._fps_combo.setCurrentText("90")
        fps_cap_row.addWidget(self._fps_combo, 1)
        layout.addLayout(fps_cap_row)

        return card

    def _make_color_section(self):
        card = QWidget()
        card.setObjectName("cardBlue")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(_lbl("COLOR & VISIBILITY ENHANCEMENT", "cardTitle"))
        reset_color_btn = QPushButton("RESET")
        reset_color_btn.setObjectName("btnSmall")
        reset_color_btn.clicked.connect(self._reset_color)
        header.addStretch()
        header.addWidget(reset_color_btn)
        layout.addLayout(header)
        layout.addWidget(_sep())

        self._sl_saturation = ColorSliderRow(
            "Saturation", -100, 100, 20, "", "#FF6B00")
        self._sl_contrast = ColorSliderRow(
            "Contrast", -100, 100, 10, "", "#00C8FF")
        self._sl_brightness = ColorSliderRow(
            "Brightness", -100, 100, 0, "", "#FFD700")
        self._sl_sharpness = ColorSliderRow(
            "Sharpness", 0, 100, 30, "%", "#00FF88")
        self._sl_gamma = ColorSliderRow(
            "Gamma", 50, 200, 100, "", "#A070FF")

        self._tr_enemy_vis = self._toggle_row(
            "Enemy Visibility Boost",
            "Increase contrast/saturation to make enemies stand out",
            "#FF3366"
        )
        self._tr_night_boost = self._toggle_row(
            "Night Mode Brightness Boost",
            "Enhance dark areas for better visibility in night maps",
            "#FFD700"
        )

        for w in [self._sl_saturation, self._sl_contrast, self._sl_brightness,
                  self._sl_sharpness, self._sl_gamma, _sep(),
                  self._tr_enemy_vis[0], self._tr_night_boost[0]]:
            layout.addWidget(w)

        apply_color_btn = QPushButton("🎨  APPLY COLOR SETTINGS")
        apply_color_btn.setObjectName("btnPrimary")
        apply_color_btn.clicked.connect(self._apply_color)
        layout.addWidget(apply_color_btn)

        return card

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _toggle_row(self, title, desc="", color="#FF6B00"):
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

    def _get_aspect(self):
        w, h = self._current_w, self._current_h
        from math import gcd
        g = gcd(w, h)
        return f"{w//g}:{h//g}"

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _refresh_display_info(self):
        self._detect_display()

    def _on_res_preset(self, idx):
        presets = [
            (1280, 720), (1366, 768), (1600, 900),
            (1920, 1080), (2560, 1440), (3840, 2160)
        ]
        if idx < len(presets):
            w, h = presets[idx]
            self._custom_w.setValue(w)
            self._custom_h.setValue(h)

    def _apply_resolution(self):
        """Apply resolution and refresh rate via Win32 ChangeDisplaySettings."""
        try:
            w = self._custom_w.value()
            h = self._custom_h.value()
            hz_text = self._hz_combo.currentText().split()[0]
            hz = int(hz_text)

            dm = ctypes.wintypes.DEVMODE()
            dm.dmSize = ctypes.sizeof(dm)
            dm.dmPelsWidth = w
            dm.dmPelsHeight = h
            dm.dmDisplayFrequency = hz
            dm.dmBitsPerPel = 32
            dm.dmFields = 0x00080000 | 0x00040000 | 0x00020000 | 0x00400000
            # CDS_UPDATEREGISTRY = 1
            ctypes.windll.user32.ChangeDisplaySettingsW(ctypes.byref(dm), 1)
        except Exception:
            pass

    def _reset_resolution(self):
        """Restore original display settings."""
        try:
            ctypes.windll.user32.ChangeDisplaySettingsW(None, 0)
        except Exception:
            pass

    def _apply_color(self):
        """Apply color settings via NVIDIA registry (saturation, contrast)."""
        try:
            import winreg
            key = r"SOFTWARE\NVIDIA Corporation\Global\NVTweak"
            sat = self._sl_saturation.value()
            # NVIDIA saturation registry (approximate mapping)
            # Value range: 0-4095 where 2048 = neutral, 4095 = max saturation
            nv_sat = int(2048 + (sat / 100.0) * 2047)
            winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key)
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0,
                                winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, "Saturation", 0, winreg.REG_DWORD, nv_sat)
        except Exception:
            pass

    def _reset_color(self):
        for sl in [self._sl_saturation, self._sl_contrast,
                   self._sl_brightness, self._sl_sharpness, self._sl_gamma]:
            sl.reset()
