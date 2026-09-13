"""
RT Tool — Professional Vector Icon System
Thin-line Feather/Lucide-style icons drawn with QPainter.

Design spec:
  - 16×16 px base size (scalable)
  - 1.5 px stroke width
  - Rounded line caps and joins
  - Single colour (caller supplies hex string)
  - No fills — outline only (except solid variants)
"""

from PyQt6.QtGui import (
    QPainter, QPixmap, QColor, QPen, QPainterPath, QIcon, QFont
)
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize
import math


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _new_pixmap(size: int) -> tuple:
    """Return (pixmap, painter) ready to draw on, transparent background."""
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    return px, p


def _pen(color: str, width: float = 1.5) -> QPen:
    pen = QPen(QColor(color), width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _icon_from_pixmap(px: QPixmap) -> QIcon:
    return QIcon(px)


# ── Icon Drawers ──────────────────────────────────────────────────────────────

def _draw_launch(p: QPainter, size: int, color: str):
    """Power button: circle with vertical stem at top."""
    pen = _pen(color, size * 0.09)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    cx, cy = size / 2, size / 2
    r = size * 0.33
    gap = 60   # degrees
    start_deg = 90 + gap / 2
    span_deg = -(360 - gap)

    p.drawArc(
        QRectF(cx - r, cy - r, r * 2, r * 2),
        int(start_deg * 16),
        int(span_deg * 16)
    )
    # stem
    stem_top = cy - r * 1.32
    stem_bot = cy - r * 0.45
    p.drawLine(QPointF(cx, stem_top), QPointF(cx, stem_bot))


def _draw_performance(p: QPainter, size: int, color: str):
    """Speedometer: semicircle + tick marks + needle."""
    pen = _pen(color, size * 0.09)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    cx, cy = size / 2, size * 0.58
    r = size * 0.36

    # Outer arc (180°)
    p.drawArc(QRectF(cx - r, cy - r, r * 2, r * 2), 0, 180 * 16)

    # Tick marks at 0°, 45°, 90°, 135°, 180°
    for deg in (0, 45, 90, 135, 180):
        rad = math.radians(deg)
        ox = cx + r * math.cos(math.pi - rad)
        oy = cy - r * math.sin(math.pi - rad)
        ix = cx + (r - size * 0.10) * math.cos(math.pi - rad)
        iy = cy - (r - size * 0.10) * math.sin(math.pi - rad)
        p.drawLine(QPointF(ox, oy), QPointF(ix, iy))

    # Needle pointing at ~135° (fast)
    needle_pen = _pen(color, size * 0.07)
    p.setPen(needle_pen)
    ang = math.radians(135)
    nx = cx + r * 0.68 * math.cos(math.pi - ang)
    ny = cy - r * 0.68 * math.sin(math.pi - ang)
    p.drawLine(QPointF(cx, cy), QPointF(nx, ny))

    # Center dot
    dot_pen = _pen(color, size * 0.07)
    p.setPen(dot_pen)
    p.setBrush(QColor(color))
    d = size * 0.09
    p.drawEllipse(QRectF(cx - d, cy - d, d * 2, d * 2))


def _draw_network(p: QPainter, size: int, color: str):
    """Wifi: three concentric arcs + dot."""
    pen = _pen(color, size * 0.09)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    cx, cy = size / 2, size * 0.56
    start = 135 * 16
    span = -90 * 16          # 90° arc centred upward

    for i, frac in enumerate((0.80, 0.52, 0.26)):
        r = size * frac / 2
        rect = QRectF(cx - r, cy - r, r * 2, r * 2)
        p.drawArc(rect, start, span)

    # dot
    p.setBrush(QColor(color))
    d = size * 0.09
    p.drawEllipse(QRectF(cx - d, cy - d, d * 2, d * 2))


def _draw_display(p: QPainter, size: int, color: str):
    """Monitor: rectangle frame + bottom stand + base."""
    pen = _pen(color, size * 0.09)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    pad = size * 0.06
    screen_h = size * 0.60
    screen_w = size * 0.84
    rx = (size - screen_w) / 2
    ry = pad + size * 0.04

    # Screen bezel (rounded rect)
    path = QPainterPath()
    path.addRoundedRect(QRectF(rx, ry, screen_w, screen_h), size * 0.06, size * 0.06)
    p.drawPath(path)

    # Stand stem
    cx = size / 2
    stand_top = ry + screen_h
    stand_bot = ry + screen_h + size * 0.14
    p.drawLine(QPointF(cx, stand_top), QPointF(cx, stand_bot))

    # Base
    base_w = size * 0.44
    bx = cx - base_w / 2
    p.drawLine(QPointF(bx, stand_bot), QPointF(bx + base_w, stand_bot))


def _draw_input(p: QPainter, size: int, color: str):
    """Mouse: pill body + center dividing line + scroll wheel."""
    pen = _pen(color, size * 0.09)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    mw = size * 0.40
    mh = size * 0.64
    mx = (size - mw) / 2
    my = size * 0.12
    r = mw / 2

    # Body (pill)
    path = QPainterPath()
    path.addRoundedRect(QRectF(mx, my, mw, mh), r, r)
    p.drawPath(path)

    # Center dividing line (left/right buttons)
    mid_y = my + mh * 0.38
    p.drawLine(QPointF(mx + mw / 2, my), QPointF(mx + mw / 2, mid_y))

    # Scroll wheel (small rect in center)
    ww, wh = size * 0.08, size * 0.18
    wx = mx + mw / 2 - ww / 2
    wy = my + size * 0.10
    wheel_pen = _pen(color, size * 0.07)
    p.setPen(wheel_pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    path2 = QPainterPath()
    path2.addRoundedRect(QRectF(wx, wy, ww, wh), size * 0.03, size * 0.03)
    p.drawPath(path2)


def _draw_audio(p: QPainter, size: int, color: str):
    """Speaker: body + cone + two sound arcs."""
    pen = _pen(color, size * 0.09)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    cx, cy = size / 2, size / 2
    # Speaker box (left side)
    bw, bh = size * 0.26, size * 0.32
    bx = cx - size * 0.36
    by = cy - bh / 2
    p.drawRect(QRectF(bx, by, bw, bh))

    # Cone (trapezoid via path)
    cone_path = QPainterPath()
    cone_path.moveTo(bx + bw, by)
    cone_path.lineTo(bx + bw + size * 0.24, cy - size * 0.38)
    cone_path.lineTo(bx + bw + size * 0.24, cy + size * 0.38)
    cone_path.lineTo(bx + bw, by + bh)
    p.drawPath(cone_path)

    # Sound arcs
    arc_cx = bx + bw + size * 0.24 + size * 0.04
    for r_frac in (0.22, 0.34):
        r = size * r_frac
        p.drawArc(
            QRectF(arc_cx - r, cy - r, r * 2, r * 2),
            -40 * 16, 80 * 16
        )


def _draw_gaming(p: QPainter, size: int, color: str):
    """Gamepad: oval body + d-pad cross + two buttons."""
    pen = _pen(color, size * 0.09)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    cx, cy = size / 2, size / 2
    bw, bh = size * 0.82, size * 0.52
    # Body
    path = QPainterPath()
    path.addRoundedRect(QRectF(cx - bw / 2, cy - bh / 2, bw, bh),
                        size * 0.22, size * 0.22)
    p.drawPath(path)

    # D-pad cross (left side)
    dpad_cx = cx - size * 0.22
    arm = size * 0.12
    t = size * 0.06
    p.drawLine(QPointF(dpad_cx - arm, cy), QPointF(dpad_cx + arm, cy))
    p.drawLine(QPointF(dpad_cx, cy - arm), QPointF(dpad_cx, cy + arm))

    # Action buttons (right side — two small circles)
    btn_cx = cx + size * 0.22
    dot_pen = _pen(color, size * 0.07)
    p.setPen(dot_pen)
    r = size * 0.065
    for dx, dy in ((-r * 1.3, 0), (r * 1.3, 0)):
        p.drawEllipse(QRectF(btn_cx + dx - r, cy - r, r * 2, r * 2))

    # Shoulder bumps (top-left and top-right arcs)
    bump_pen = _pen(color, size * 0.08)
    p.setPen(bump_pen)
    bump_w = size * 0.24
    bump_h = size * 0.14
    for bx in (cx - bw / 2, cx + bw / 2 - bump_w):
        p.drawArc(QRectF(bx, cy - bh / 2 - bump_h, bump_w, bump_h * 2),
                  0, 180 * 16)


def _draw_profiles(p: QPainter, size: int, color: str):
    """Person: circle head + shoulder arc."""
    pen = _pen(color, size * 0.09)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    cx = size / 2
    head_r = size * 0.20
    head_cy = size * 0.32
    p.drawEllipse(QRectF(cx - head_r, head_cy - head_r, head_r * 2, head_r * 2))

    # Shoulder arc
    sh_r = size * 0.36
    sh_cy = size * 0.90
    p.drawArc(
        QRectF(cx - sh_r, sh_cy - sh_r, sh_r * 2, sh_r * 2),
        0, 180 * 16
    )


# ── Stat bar icons ────────────────────────────────────────────────────────────

def _draw_fps(p: QPainter, size: int, color: str):
    """FPS: Three vertical rising bars."""
    pen = _pen(color, size * 0.09)
    p.setPen(pen)
    p.setBrush(QColor(color))

    bar_w = size * 0.14
    heights = [size * 0.32, size * 0.52, size * 0.72]
    gap = (size - 3 * bar_w) / 4
    bottom = size * 0.86

    for i, h in enumerate(heights):
        x = gap + i * (bar_w + gap)
        y = bottom - h
        path = QPainterPath()
        path.addRoundedRect(QRectF(x, y, bar_w, h), size * 0.03, size * 0.03)
        p.fillPath(path, QColor(color))


def _draw_ping(p: QPainter, size: int, color: str):
    """Ping: three concentric arcs (like _draw_network but smaller)."""
    _draw_network(p, size, color)


def _draw_cpu(p: QPainter, size: int, color: str):
    """CPU chip: square + grid lines + leg ticks."""
    pen = _pen(color, size * 0.09)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    pad = size * 0.24
    chip_size = size - 2 * pad
    p.drawRect(QRectF(pad, pad, chip_size, chip_size))

    # Inner grid (2x2)
    m = pad + chip_size * 0.30
    mw = chip_size * 0.40
    inner_pen = _pen(color, size * 0.07)
    p.setPen(inner_pen)
    p.drawRect(QRectF(m, m, mw, mw))

    # Leg ticks (top and bottom, 3 each)
    p.setPen(pen)
    leg_len = size * 0.10
    spacing = chip_size / 4
    for i in range(1, 4):
        x = pad + i * spacing
        # top
        p.drawLine(QPointF(x, pad), QPointF(x, pad - leg_len))
        # bottom
        p.drawLine(QPointF(x, pad + chip_size), QPointF(x, pad + chip_size + leg_len))
        # left
        p.drawLine(QPointF(pad, x), QPointF(pad - leg_len, x))
        # right
        p.drawLine(QPointF(pad + chip_size, x), QPointF(pad + chip_size + leg_len, x))


def _draw_gpu(p: QPainter, size: int, color: str):
    """GPU: wide card + fan circle + vents."""
    pen = _pen(color, size * 0.09)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    # Card body
    cw, ch = size * 0.82, size * 0.46
    cx_off = (size - cw) / 2
    cy_off = (size - ch) / 2
    p.drawRoundedRect(QRectF(cx_off, cy_off, cw, ch), size * 0.05, size * 0.05)

    # Fan circle
    fan_r = ch * 0.34
    fan_cx = cx_off + cw * 0.28
    fan_cy = cy_off + ch / 2
    p.drawEllipse(QRectF(fan_cx - fan_r, fan_cy - fan_r, fan_r * 2, fan_r * 2))

    # Vent lines (right side)
    vent_x = cx_off + cw * 0.60
    vent_pen = _pen(color, size * 0.07)
    p.setPen(vent_pen)
    for i in range(3):
        vy = cy_off + ch * (0.22 + i * 0.24)
        p.drawLine(QPointF(vent_x, vy), QPointF(cx_off + cw - size * 0.04, vy))


def _draw_ram(p: QPainter, size: int, color: str):
    """RAM: tall rectangle + notch + contact lines."""
    pen = _pen(color, size * 0.09)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    rw = size * 0.44
    rh = size * 0.68
    rx = (size - rw) / 2
    ry = size * 0.06

    # Main body
    p.drawRect(QRectF(rx, ry, rw, rh))

    # Notch (small cutout at bottom center)
    notch_w = rw * 0.20
    notch_h = rh * 0.06
    nx = rx + rw / 2 - notch_w / 2
    ny = ry + rh - notch_h
    p.setBrush(QColor("#070B13"))   # fill notch with BG color
    p.drawRect(QRectF(nx, ny, notch_w, notch_h))
    p.setBrush(Qt.BrushStyle.NoBrush)

    # Contact pins (3 lines at bottom)
    pin_pen = _pen(color, size * 0.07)
    p.setPen(pin_pen)
    pin_top = ry + rh
    pin_bot = ry + rh + size * 0.12
    for i in range(3):
        px_ = rx + rw * (0.20 + i * 0.27)
        p.drawLine(QPointF(px_, pin_top), QPointF(px_, pin_bot))


def _draw_temp(p: QPainter, size: int, color: str):
    """Thermometer: tube + bulb."""
    pen = _pen(color, size * 0.09)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    cx = size / 2
    tube_w = size * 0.14
    tube_top = size * 0.08
    tube_bot = size * 0.66
    bulb_r = size * 0.18

    # Tube (rounded rect)
    path = QPainterPath()
    path.addRoundedRect(
        QRectF(cx - tube_w / 2, tube_top, tube_w, tube_bot - tube_top),
        tube_w / 2, tube_w / 2
    )
    p.drawPath(path)

    # Bulb
    p.drawEllipse(QRectF(cx - bulb_r, tube_bot - bulb_r * 0.5,
                         bulb_r * 2, bulb_r * 2))

    # Tick marks (right side of tube)
    tick_pen = _pen(color, size * 0.07)
    p.setPen(tick_pen)
    for i in range(3):
        ty = tube_top + size * 0.10 + i * size * 0.14
        p.drawLine(QPointF(cx + tube_w / 2, ty),
                   QPointF(cx + tube_w / 2 + size * 0.12, ty))


def _draw_registry(p: QPainter, size: int, color: str):
    """Registry / System Tweaks icon: horizontal tuning sliders with adjustment nodes."""
    pen = _pen(color, size * 0.08)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    l = size * 0.16
    r = size * 0.84

    # 3 track lines
    y1 = size * 0.28
    y2 = size * 0.50
    y3 = size * 0.72

    p.drawLine(QPointF(l, y1), QPointF(r, y1))
    p.drawLine(QPointF(l, y2), QPointF(r, y2))
    p.drawLine(QPointF(l, y3), QPointF(r, y3))

    # Knobs (small rounded nodes)
    p.setBrush(QColor("#070B13"))
    knob_w = size * 0.16
    knob_h = size * 0.20

    # Knob 1 at x = 0.40
    k1_x = size * 0.40
    p.drawRoundedRect(QRectF(k1_x - knob_w / 2, y1 - knob_h / 2, knob_w, knob_h), 2, 2)

    # Knob 2 at x = 0.68
    k2_x = size * 0.68
    p.drawRoundedRect(QRectF(k2_x - knob_w / 2, y2 - knob_h / 2, knob_w, knob_h), 2, 2)

    # Knob 3 at x = 0.32
    k3_x = size * 0.32
    p.drawRoundedRect(QRectF(k3_x - knob_w / 2, y3 - knob_h / 2, knob_w, knob_h), 2, 2)


# ── Public API ────────────────────────────────────────────────────────────────

_DRAWERS = {
    "launch":      _draw_launch,
    "performance": _draw_performance,
    "network":     _draw_network,
    "display":     _draw_display,
    "input":       _draw_input,
    "audio":       _draw_audio,
    "gaming":      _draw_gaming,
    "profiles":    _draw_profiles,
    "registry":    _draw_registry,
    "fps":         _draw_fps,
    "ping":        _draw_ping,
    "cpu":         _draw_cpu,
    "gpu":         _draw_gpu,
    "ram":         _draw_ram,
    "temp":        _draw_temp,
}


def get_pixmap(name: str, size: int = 16, color: str = "#5A7090") -> QPixmap:
    """Return a QPainter-drawn icon as a QPixmap."""
    drawer = _DRAWERS.get(name)
    if not drawer:
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        return px
    px, p = _new_pixmap(size)
    drawer(p, size, color)
    p.end()
    return px


def get_icon(name: str, size: int = 16, color: str = "#5A7090") -> QIcon:
    """Return a QIcon built from a vector-drawn pixmap."""
    return QIcon(get_pixmap(name, size, color))


def get_dual_state_icon(name: str, size: int = 16,
                        color_normal: str = "#5A7090",
                        color_active: str = "#FF6B00") -> QIcon:
    """Return a QIcon with Normal and Active states."""
    icon = QIcon()
    icon.addPixmap(get_pixmap(name, size, color_normal), QIcon.Mode.Normal)
    icon.addPixmap(get_pixmap(name, size, color_active), QIcon.Mode.Active)
    icon.addPixmap(get_pixmap(name, size, color_active), QIcon.Mode.Selected)
    return icon
