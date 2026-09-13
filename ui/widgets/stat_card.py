"""
Stat Card Widget — RT Tool
Compact live-metric display card.
Uses the professional vector icon system instead of emoji.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.icons import get_pixmap


class StatCard(QWidget):
    """A compact card showing a metric name, value, and unit."""

    def __init__(self, parent=None, title="", value="0", unit="",
                 color="#FF6B00", icon_name=""):
        super().__init__(parent)
        self._title = title
        self._value_str = value
        self._unit = unit
        self._color = color
        self._icon_name = icon_name
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        # Top row: icon + title
        top = QHBoxLayout()
        top.setSpacing(6)
        if self._icon_name:
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(14, 14)
            px = get_pixmap(self._icon_name, 14, self._color)
            icon_lbl.setPixmap(px)
            top.addWidget(icon_lbl)
        title_lbl = QLabel(self._title)
        title_lbl.setObjectName("labelMuted")
        title_lbl.setStyleSheet(
            "font-size: 10px; letter-spacing: 1.5px;")
        top.addWidget(title_lbl)
        top.addStretch()
        layout.addLayout(top)

        # Value
        self._val_label = QLabel(self._value_str)
        self._val_label.setStyleSheet(
            f"font-size: 24px; font-weight: 800; color: {self._color}; "
            "letter-spacing: -1px;"
        )
        layout.addWidget(self._val_label)

        # Unit
        self._unit_label = QLabel(self._unit)
        self._unit_label.setObjectName("labelMuted")
        self._unit_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(self._unit_label)

    def update_value(self, value, unit=None):
        self._val_label.setText(str(value))
        if unit is not None:
            self._unit_label.setText(unit)


class MiniStatBar(QWidget):
    """Horizontal mini-stat strip for the top bar — uses vector icons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        self._stats = {}
        # (display_label, dict_key, default, colour, icon_name)
        items = [
            ("FPS",  "fps",  "--",   "#FF6B00", "fps"),
            ("PING", "ping", "--",   "#00C8FF", "ping"),
            ("CPU",  "cpu",  "--%",  "#FFD700", "cpu"),
            ("GPU",  "gpu",  "--%",  "#00FF88", "gpu"),
            ("RAM",  "ram",  "--%",  "#A070FF", "ram"),
        ]
        for label, key, default, color, icon_name in items:
            grp = QHBoxLayout()
            grp.setSpacing(5)

            # Vector icon (12 px)
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(12, 12)
            px = get_pixmap(icon_name, 12, color)
            icon_lbl.setPixmap(px)

            lbl = QLabel(label)
            lbl.setStyleSheet(
                "font-size: 9px; color: #3A4F6A; letter-spacing: 1px;")
            val = QLabel(default)
            val.setStyleSheet(
                f"font-size: 12px; font-weight: 700; color: {color};")

            grp.addWidget(icon_lbl)
            grp.addWidget(lbl)
            grp.addWidget(val)
            layout.addLayout(grp)
            self._stats[key] = val

    def update_stats(self, fps=None, ping=None, cpu=None, gpu=None, ram=None):
        if fps is not None:
            self._stats["fps"].setText(str(fps))
        if ping is not None:
            self._stats["ping"].setText(f"{ping}ms")
        if cpu is not None:
            self._stats["cpu"].setText(f"{cpu}%")
        if gpu is not None:
            self._stats["gpu"].setText(f"{gpu}%")
        if ram is not None:
            self._stats["ram"].setText(f"{ram}%")
