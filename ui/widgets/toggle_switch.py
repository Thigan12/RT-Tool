"""
Animated Toggle Switch Widget — RT Tool
Smooth sliding toggle with glow animation.
"""

from PyQt6.QtWidgets import QAbstractButton
from PyQt6.QtCore import (Qt, QPropertyAnimation, QEasingCurve,
                          pyqtProperty, QRectF, QPointF)
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient


class ToggleSwitch(QAbstractButton):
    """Custom animated toggle switch with neon glow effect."""

    def __init__(self, parent=None, color_on="#FF6B00", color_off="#1A2740",
                 label_on="", label_off=""):
        super().__init__(parent)
        self.setCheckable(True)
        self._color_on = QColor(color_on)
        self._color_off = QColor(color_off)
        self._label_on = label_on
        self._label_off = label_off
        self._handle_pos = 0.0  # 0.0 = off, 1.0 = on
        self._track_radius = 11
        self._thumb_radius = 9

        self._anim = QPropertyAnimation(self, b"handle_pos", self)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim.setDuration(200)

        self.setFixedSize(52, 26)
        self.toggled.connect(self._on_toggle)

    @pyqtProperty(float)
    def handle_pos(self):
        return self._handle_pos

    @handle_pos.setter
    def handle_pos(self, value):
        self._handle_pos = value
        self.update()

    def _on_toggle(self, checked):
        self._anim.stop()
        self._anim.setStartValue(self._handle_pos)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        r = self._track_radius

        # Track background
        if self.isChecked():
            track_color = QColor(self._color_on)
            track_color.setAlpha(180)
        else:
            track_color = QColor(self._color_off)

        # Draw track
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(track_color))
        p.drawRoundedRect(0, (h - r * 2) // 2, w, r * 2, r, r)

        # Draw glow when active
        if self.isChecked() and self._handle_pos > 0.5:
            glow = QColor(self._color_on)
            glow.setAlpha(int(60 * self._handle_pos))
            p.setBrush(QBrush(glow))
            p.drawRoundedRect(-2, (h - r * 2) // 2 - 2, w + 4, r * 2 + 4, r + 2, r + 2)

        # Thumb position
        thumb_x = (self._thumb_radius + 2) + self._handle_pos * (
            w - (self._thumb_radius + 2) * 2 - 2
        )
        thumb_y = h / 2

        # Thumb glow
        if self.isChecked() and self._handle_pos > 0.3:
            g = QColor(self._color_on)
            g.setAlpha(int(100 * self._handle_pos))
            p.setBrush(QBrush(g))
            p.drawEllipse(
                QPointF(thumb_x, thumb_y),
                self._thumb_radius + 3,
                self._thumb_radius + 3
            )

        # Thumb
        if self.isChecked():
            p.setBrush(QBrush(QColor(self._color_on)))
        else:
            p.setBrush(QBrush(QColor("#A0B8D0")))
        p.setPen(QPen(QColor("#00000020"), 1))
        p.drawEllipse(QPointF(thumb_x, thumb_y),
                      self._thumb_radius, self._thumb_radius)

        p.end()

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(52, 26)
