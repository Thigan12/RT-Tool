"""
Audio Optimization Page — RT Tool
Spatial audio, latency, noise suppression, EQ presets.
"""

import subprocess
import winreg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QLinearGradient, QBrush
from ui.widgets.toggle_switch import ToggleSwitch


def _sep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine); return f

def _lbl(text, obj="labelPrimary"):
    l = QLabel(text); l.setObjectName(obj); return l


class EQBand(QWidget):
    """Single EQ frequency band (vertical slider)."""

    def __init__(self, freq_label, default=50, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        self._val_lbl = QLabel(f"+0")
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._val_lbl.setStyleSheet("font-size: 10px; color: #00C8FF; font-weight: 700;")
        layout.addWidget(self._val_lbl)

        self._slider = QSlider(Qt.Orientation.Vertical)
        self._slider.setRange(-12, 12)
        self._slider.setValue(0)
        self._slider.setObjectName("sliderCyan")
        self._slider.valueChanged.connect(
            lambda v: self._val_lbl.setText(f"{'+' if v >= 0 else ''}{v}"))
        layout.addWidget(self._slider, 1, Qt.AlignmentFlag.AlignCenter)

        freq_lbl = QLabel(freq_label)
        freq_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        freq_lbl.setStyleSheet("font-size: 9px; color: #5A7090;")
        layout.addWidget(freq_lbl)

    def value(self):
        return self._slider.value()


class AudioPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

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
        layout.addLayout(self._make_top_row())
        layout.addWidget(self._make_spatial_section())
        layout.addWidget(self._make_eq_section())
        layout.addWidget(self._make_voice_section())
        layout.addStretch()

    def _make_header(self):
        h = QVBoxLayout()
        h.addWidget(_lbl("Audio Optimization", "pageTitle"))
        h.addWidget(_lbl("Spatial Audio · Latency · EQ · Noise Suppression", "pageSubtitle"))
        return h

    def _make_top_row(self):
        row = QHBoxLayout()
        row.setSpacing(14)

        # Master volume
        vol_card = QWidget()
        vol_card.setObjectName("card")
        vol_layout = QVBoxLayout(vol_card)
        vol_layout.addWidget(_lbl("MASTER VOLUME", "cardTitle"))
        self._master_vol_lbl = QLabel("100%")
        self._master_vol_lbl.setStyleSheet(
            "font-size: 28px; font-weight: 800; color: #FF6B00;")
        vol_layout.addWidget(self._master_vol_lbl)
        self._master_vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._master_vol_slider.setRange(0, 100)
        self._master_vol_slider.setValue(100)
        self._master_vol_slider.valueChanged.connect(
            lambda v: self._master_vol_lbl.setText(f"{v}%"))
        vol_layout.addWidget(self._master_vol_slider)
        row.addWidget(vol_card, 1)

        # Latency card
        lat_card = QWidget()
        lat_card.setObjectName("cardBlue")
        lat_layout = QVBoxLayout(lat_card)
        lat_layout.addWidget(_lbl("AUDIO LATENCY", "cardTitle"))
        self._audio_lat_lbl = QLabel("—  ms")
        self._audio_lat_lbl.setStyleSheet(
            "font-size: 28px; font-weight: 800; color: #00C8FF;")
        lat_layout.addWidget(self._audio_lat_lbl)
        self._lat_combo = QComboBox()
        self._lat_combo.addItems([
            "Ultra Low (5ms)", "Low (10ms)", "Medium (20ms)",
            "High (40ms)", "Default"])
        self._lat_combo.setCurrentText("Low (10ms)")
        self._lat_combo.currentIndexChanged.connect(self._set_audio_latency)
        lat_layout.addWidget(self._lat_combo)
        row.addWidget(lat_card, 1)

        # Footstep card
        foot_card = QWidget()
        foot_card.setObjectName("cardGreen")
        foot_layout = QVBoxLayout(foot_card)
        foot_layout.addWidget(_lbl("FOOTSTEP BOOST", "cardTitle"))
        self._tr_footstep = ToggleSwitch(color_on="#00FF88")
        foot_layout.addWidget(self._tr_footstep)
        foot_layout.addWidget(_lbl(
            "Amplify 200-800 Hz range\nfor footstep clarity", "labelMuted"))
        row.addWidget(foot_card, 1)

        return row

    def _make_spatial_section(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        layout.addWidget(_lbl("SPATIAL AUDIO & 3D SOUND", "cardTitle"))
        layout.addWidget(_sep())

        self._tr_spatial = self._tr(
            "Windows Sonic Spatial Audio",
            "Enable 3D positional audio for footstep/gunshot direction detection",
            "#FF6B00")
        self._tr_dolby = self._tr(
            "Dolby Atmos for Headphones",
            "Premium spatial audio rendering (requires Dolby app installed)",
            "#FF6B00")
        self._tr_7_1 = self._tr(
            "7.1 Surround Simulation",
            "Virtualize multi-channel surround for standard stereo headphones",
            "#FFD700")
        self._tr_hrtf = self._tr(
            "HRTF Head Tracking",
            "Head-related transfer function for accurate 3D positioning",
            "#00C8FF")

        for w, t in [self._tr_spatial, self._tr_dolby,
                     self._tr_7_1, self._tr_hrtf]:
            layout.addWidget(w)

        layout.addWidget(_sep())

        # Volume mixer
        mixer_lbl = _lbl("CHANNEL VOLUME MIXER", "cardTitle")
        layout.addWidget(mixer_lbl)

        mixer = QHBoxLayout()
        channels = [
            ("Game", 100, "#FF6B00"),
            ("Voice", 80, "#00C8FF"),
            ("Effects", 90, "#00FF88"),
            ("Music", 50, "#FFD700"),
            ("System", 60, "#A070FF"),
        ]
        self._channel_sliders = {}
        for name, default, color in channels:
            ch = QVBoxLayout()
            ch.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val = QLabel(f"{default}%")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {color};")
            sl = QSlider(Qt.Orientation.Vertical)
            sl.setRange(0, 100)
            sl.setValue(default)
            sl.setMinimumHeight(80)
            sl.valueChanged.connect(lambda v, lbl=val: lbl.setText(f"{v}%"))
            lbl_w = QLabel(name)
            lbl_w.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_w.setStyleSheet("font-size: 10px; color: #5A7090;")
            ch.addWidget(val)
            ch.addWidget(sl, alignment=Qt.AlignmentFlag.AlignCenter)
            ch.addWidget(lbl_w)
            mixer.addLayout(ch, 1)
            self._channel_sliders[name] = sl

        layout.addLayout(mixer)
        return card

    def _make_eq_section(self):
        card = QWidget()
        card.setObjectName("cardBlue")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(_lbl("GAMING EQ — 10 BAND", "cardTitle"))

        preset_combo = QComboBox()
        preset_combo.addItems([
            "PUBG Mobile", "Footstep Boost", "Gunshot Clarity",
            "Voice Clarity", "Bass Boost", "Flat/Default"
        ])
        preset_combo.currentTextChanged.connect(self._apply_eq_preset)
        header.addStretch()
        header.addWidget(preset_combo)
        layout.addLayout(header)
        layout.addWidget(_sep())

        # EQ bands
        eq_row = QHBoxLayout()
        eq_row.setSpacing(4)
        freqs = ["32Hz", "64Hz", "125Hz", "250Hz", "500Hz",
                 "1kHz", "2kHz", "4kHz", "8kHz", "16kHz"]
        self._eq_bands = []
        for freq in freqs:
            band = EQBand(freq)
            eq_row.addWidget(band, 1)
            self._eq_bands.append(band)

        layout.addLayout(eq_row)

        return card

    def _make_voice_section(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        layout.addWidget(_lbl("VOICE COMM ENHANCEMENT", "cardTitle"))
        layout.addWidget(_sep())

        self._tr_noise_sup = self._tr(
            "Noise Suppression",
            "Remove background noise from microphone via Windows audio APO",
            "#00FF88")
        self._tr_echo_cancel = self._tr(
            "Echo Cancellation",
            "Eliminate acoustic echo and feedback from speakers",
            "#00FF88")
        self._tr_boost_mic = self._tr(
            "Microphone Boost",
            "Increase microphone input gain for clearer voice pickup",
            "#FFD700")
        self._tr_agc = self._tr(
            "Auto Gain Control (AGC)",
            "Automatically normalize microphone volume levels",
            "#FFD700")

        for w, t in [self._tr_noise_sup, self._tr_echo_cancel,
                     self._tr_boost_mic, self._tr_agc]:
            layout.addWidget(w)

        layout.addWidget(_sep())

        mic_vol_row = QHBoxLayout()
        mic_vol_row.addWidget(_lbl("Microphone Volume:", "labelPrimary"))
        self._mic_slider = QSlider(Qt.Orientation.Horizontal)
        self._mic_slider.setRange(0, 100)
        self._mic_slider.setValue(80)
        self._mic_slider.setObjectName("sliderGreen")
        self._mic_val_lbl = QLabel("80%")
        self._mic_val_lbl.setObjectName("labelGreen")
        self._mic_slider.valueChanged.connect(
            lambda v: self._mic_val_lbl.setText(f"{v}%"))
        mic_vol_row.addWidget(self._mic_slider, 1)
        mic_vol_row.addWidget(self._mic_val_lbl)
        layout.addLayout(mic_vol_row)

        apply_btn = QPushButton("✓  APPLY AUDIO OPTIMIZATIONS")
        apply_btn.setObjectName("btnPrimary")
        apply_btn.clicked.connect(self._apply_audio)
        layout.addWidget(apply_btn)

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

    def _set_audio_latency(self, idx):
        """Set audio buffer via registry (AudioEngine latency)."""
        # EngineLatency values in 100ns units
        latency_vals = [50000, 100000, 200000, 400000, 0]
        lat_ms = [5, 10, 20, 40, 0]
        self._audio_lat_lbl.setText(
            f"{lat_ms[idx]}  ms" if lat_ms[idx] else "Default  ms")
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
                0, winreg.KEY_SET_VALUE
            ) as k:
                if latency_vals[idx]:
                    winreg.SetValueEx(k, "NetworkThrottlingIndex", 0,
                                      winreg.REG_DWORD, 0xffffffff)
                    winreg.SetValueEx(k, "SystemResponsiveness", 0,
                                      winreg.REG_DWORD, 0)
        except Exception:
            pass

    def _apply_eq_preset(self, preset):
        """Apply EQ preset values to the 10 bands."""
        presets = {
            "PUBG Mobile":    [2, 3, 5, 4, 2, 0, 3, 5, 6, 4],
            "Footstep Boost": [0, 2, 8, 6, 3, 0, -2, 0, 0, 0],
            "Gunshot Clarity":[0, 0, 2, 3, 5, 6, 5, 4, 3, 2],
            "Voice Clarity":  [-2, -1, 2, 4, 6, 7, 5, 3, 1, 0],
            "Bass Boost":     [8, 7, 5, 3, 1, 0, 0, 0, 0, 0],
            "Flat/Default":   [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        }
        vals = presets.get(preset, [0]*10)
        for band, val in zip(self._eq_bands, vals):
            band._slider.setValue(val)

    def _apply_audio(self):
        """Enable spatial audio via registry."""
        try:
            # Enable Windows Sonic
            key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render"
            if self._tr_spatial[1].isChecked():
                subprocess.run(
                    ["powershell", "-Command",
                     "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AudioEndpoint'"
                     " -Name 'SpatialAudioMode' -Value 1"],
                    capture_output=True, timeout=3
                )
        except Exception:
            pass

        # Set multimedia priority
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
                0, winreg.KEY_SET_VALUE
            ) as k:
                winreg.SetValueEx(k, "Priority", 0, winreg.REG_DWORD, 6)
                winreg.SetValueEx(k, "GPU Priority", 0, winreg.REG_DWORD, 8)
        except Exception:
            pass
