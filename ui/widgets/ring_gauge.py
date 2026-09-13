"""
Ring Gauge Widget — RT Tool
Circular progress ring drawn with QPainter.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QConicalGradient, QBrush


class RingGauge(QWidget):
    """Animated circular progress ring with label."""

    def __init__(self, parent=None, label="", color="#FF6B00",
                 size=90, track_width=8, value=0):
        super().__init__(parent)
        self._label = label
        self._color = QColor(color)
        self._ring_size = size
        self._track_width = track_width
        self._value = value        # 0–100
        self._anim_value = 0.0
        self.setFixedSize(size, size)

        self._anim = QPropertyAnimation(self, b"anim_value", self)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.setDuration(600)

    @pyqtProperty(float)
    def anim_value(self):
        return self._anim_value

    @anim_value.setter
    def anim_value(self, v):
        self._anim_value = v
        self.update()

    def set_value(self, v):
        v = max(0, min(100, v))
        self._value = v
        self._anim.stop()
        self._anim.setStartValue(self._anim_value)
        self._anim.setEndValue(float(v))
        self._anim.start()

    def value(self):
        return self._value

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        tw = self._track_width
        margin = tw // 2 + 2
        rect = QRectF(margin, margin, w - margin * 2, h - margin * 2)

        # Track (background ring)
        p.setPen(QPen(QColor("#1A2740"), tw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(rect, 0, 360 * 16)

        # Active arc
        span = int(-self._anim_value / 100.0 * 360 * 16)
        if span != 0:
            color = QColor(self._color)
            pen = QPen(color, tw, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawArc(rect, 90 * 16, span)

        # Glow effect
        if self._anim_value > 5:
            glow_color = QColor(self._color)
            glow_color.setAlpha(40)
            gpen = QPen(glow_color, tw + 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(gpen)
            p.drawArc(rect, 90 * 16, span)

        # Center text — value
        pct_color = self._get_value_color()
        p.setPen(QPen(pct_color))
        font_size = max(1, int(w * 0.18))
        font = QFont("Segoe UI", font_size, QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(QRectF(0, -6, w, h), Qt.AlignmentFlag.AlignCenter,
                   f"{int(self._anim_value)}%")

        # Label below value
        p.setPen(QPen(QColor("#5A7090")))
        font2_size = max(1, int(w * 0.10))
        font2 = QFont("Segoe UI", font2_size)
        p.setFont(font2)
        p.drawText(QRectF(0, 10, w, h), Qt.AlignmentFlag.AlignCenter, self._label)

        p.end()

    def _get_value_color(self):
        v = self._anim_value
        if v < 50:
            return QColor("#00FF88")
        elif v < 75:
            return QColor("#FFD700")
        elif v < 90:
            return QColor("#FF6B00")
        else:
            return QColor("#FF3366")
