"""
Gaming Features Page — RT Tool
Crosshair overlay, recoil patterns, macros, HUD, process killer.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QFrame, QScrollArea, QColorDialog,
    QSpinBox, QListWidget, QListWidgetItem, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
import psutil

from ui.widgets.toggle_switch import ToggleSwitch
from core import process_manager


def _sep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine); return f

def _lbl(text, obj="labelPrimary"):
    l = QLabel(text); l.setObjectName(obj); return l


class CrosshairCanvas(QWidget):
    """Live canvas crosshair designer preview."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 180)
        self._style = "cross"
        self._color = QColor("#FF0000")
        self._size = 20
        self._thickness = 2
        self._gap = 5

    def set_style(self, s): self._style = s; self.update()
    def set_color(self, c): self._color = QColor(c); self.update()
    def set_size(self, v): self._size = v; self.update()
    def set_thickness(self, v): self._thickness = v; self.update()
    def set_gap(self, v): self._gap = v; self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dark background
        p.fillRect(self.rect(), QColor("#070B13"))
        p.setPen(QPen(QColor("#1A2740"), 1))
        p.drawRect(0, 0, self.width()-1, self.height()-1)

        # Grid lines
        p.setPen(QPen(QColor("#0F1A2A"), 1))
        cx, cy = self.width()//2, self.height()//2
        for i in range(0, self.width(), 10):
            p.drawLine(i, 0, i, self.height())
            p.drawLine(0, i, self.width(), i)

        # Draw crosshair
        pen = QPen(self._color, self._thickness,
                   Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap)
        p.setPen(pen)
        s = self._size
        g = self._gap
        t = self._thickness

        if self._style == "cross":
            p.drawLine(cx - s, cy, cx - g, cy)
            p.drawLine(cx + g, cy, cx + s, cy)
            p.drawLine(cx, cy - s, cx, cy - g)
            p.drawLine(cx, cy + g, cx, cy + s)
        elif self._style == "dot":
            p.setBrush(QBrush(self._color))
            p.drawEllipse(cx - t*2, cy - t*2, t*4, t*4)
        elif self._style == "circle":
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(cx - s, cy - s, s*2, s*2)
        elif self._style == "t-shape":
            p.drawLine(cx - s, cy, cx + s, cy)
            p.drawLine(cx, cy - s, cx, cy)
        elif self._style == "x-shape":
            p.drawLine(cx-s, cy-s, cx-g, cy-g)
            p.drawLine(cx+g, cy+g, cx+s, cy+s)
            p.drawLine(cx+s, cy-s, cx+g, cy-g)
            p.drawLine(cx-g, cy+g, cx-s, cy+s)
        elif self._style == "cross+dot":
            p.drawLine(cx - s, cy, cx - g, cy)
            p.drawLine(cx + g, cy, cx + s, cy)
            p.drawLine(cx, cy - s, cx, cy - g)
            p.drawLine(cx, cy + g, cx, cy + s)
            p.setBrush(QBrush(self._color))
            p.drawEllipse(cx-t, cy-t, t*2, t*2)

        p.end()


class CrosshairOverlay(QWidget):
    """Always-on-top transparent crosshair overlay window."""
    def __init__(self, parent=None):
        super().__init__(None,
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)
        self._visible = False
        self._canvas_settings = {
            "style": "cross", "color": "#FF0000",
            "size": 20, "thickness": 2, "gap": 5
        }

    def show_overlay(self):
        screen = self.screen().geometry()
        self.setGeometry(screen)
        self._visible = True
        self.show()
        self.update()

    def hide_overlay(self):
        self._visible = False
        self.hide()

    def apply_settings(self, settings):
        self._canvas_settings.update(settings)
        self.update()

    def paintEvent(self, event):
        if not self._visible:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = self.width() // 2
        cy = self.height() // 2
        color = QColor(self._canvas_settings["color"])
        size = self._canvas_settings["size"]
        gap = self._canvas_settings["gap"]
        thick = self._canvas_settings["thickness"]
        style = self._canvas_settings["style"]
        pen = QPen(color, thick, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap)
        p.setPen(pen)

        if style in ("cross", "cross+dot"):
            p.drawLine(cx - size, cy, cx - gap, cy)
            p.drawLine(cx + gap, cy, cx + size, cy)
            p.drawLine(cx, cy - size, cx, cy - gap)
            p.drawLine(cx, cy + gap, cx, cy + size)
            if style == "cross+dot":
                p.setBrush(QBrush(color))
                p.drawEllipse(cx-thick, cy-thick, thick*2, thick*2)
        elif style == "dot":
            p.setBrush(QBrush(color))
            p.drawEllipse(cx - thick*2, cy - thick*2, thick*4, thick*4)
        elif style == "circle":
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(cx - size, cy - size, size*2, size*2)
        elif style == "t-shape":
            p.drawLine(cx - size, cy, cx + size, cy)
            p.drawLine(cx, cy - size, cx, cy)
        p.end()


class RecoilPattern(QWidget):
    """PUBG recoil pattern visualizer."""
    PATTERNS = {
        "AKM":  [(0,0),(2,5),(3,12),(2,20),(1,30),(0,40),(-1,50),(-2,60)],
        "M416": [(0,0),(1,4),(2,9),(2,15),(1,22),(0,30),(0,38),(0,46)],
        "SCAR-L":[(0,0),(1,3),(2,8),(2,14),(1,20),(0,28),(0,36)],
        "UZI":  [(0,0),(3,3),(5,7),(5,12),(3,18),(1,24)],
        "AWM":  [(0,0),(0,15)],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._gun = "AKM"
        self.setMinimumHeight(160)

    def set_gun(self, name):
        self._gun = name; self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#04080F"))

        pattern = self.PATTERNS.get(self._gun, [])
        if not pattern:
            p.end(); return

        w, h = self.width(), self.height()
        cx = w // 2
        scale_x = 8
        scale_y = (h - 40) / max(p2[1] for p2 in pattern) if len(pattern) > 1 else 1

        prev = None
        for i, (dx, dy) in enumerate(pattern):
            x = int(cx + dx * scale_x)
            y = int(20 + dy * scale_y)
            ratio = i / max(len(pattern) - 1, 1)
            color = QColor(
                int(255 * ratio),
                int(255 * (1 - ratio)),
                0
            )
            p.setPen(QPen(color, 2))
            p.setBrush(QBrush(color))
            p.drawEllipse(x - 3, y - 3, 6, 6)
            if prev:
                p.setPen(QPen(QColor(200, 200, 200, 80), 1))
                p.drawLine(prev[0], prev[1], x, y)
            prev = (x, y)

        p.setPen(QPen(QColor("#5A7090"), 1))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(5, 12, f"{self._gun} Recoil Pattern")
        p.end()


class GamingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._overlay = CrosshairOverlay()
        self._overlay_visible = False
        self._setup_ui()
        self._start_proc_timer()

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

        # Top row: crosshair + recoil
        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        top_row.addWidget(self._make_crosshair_section(), 3)
        top_row.addWidget(self._make_recoil_section(), 2)
        layout.addLayout(top_row)

        layout.addWidget(self._make_hud_section())
        layout.addWidget(self._make_process_killer())
        # NOTE: no addStretch() here — it was pushing the table below the visible area

    def _make_header(self):
        h = QVBoxLayout()
        h.addWidget(_lbl("Gaming Features", "pageTitle"))
        h.addWidget(_lbl("Crosshair Overlay · Recoil Assist · HUD · Process Killer", "pageSubtitle"))
        return h

    def _make_crosshair_section(self):
        card = QWidget()
        card.setObjectName("cardGlow")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(_lbl("CROSSHAIR OVERLAY DESIGNER", "cardTitle"))
        self._overlay_toggle = ToggleSwitch(color_on="#FF3366")
        self._overlay_toggle.toggled.connect(self._toggle_overlay)
        header.addStretch()
        self._overlay_status = _lbl("OFF", "labelRed")
        header.addWidget(self._overlay_status)
        header.addWidget(self._overlay_toggle)
        layout.addLayout(header)
        layout.addWidget(_sep())

        content = QHBoxLayout()
        content.setSpacing(16)

        # Canvas preview
        self._xhair_canvas = CrosshairCanvas()
        self._xhair_canvas.setStyleSheet(
            "border: 1px solid #1A2740; border-radius: 4px;")
        content.addWidget(self._xhair_canvas)

        # Controls
        ctrl = QVBoxLayout()
        ctrl.setSpacing(8)

        # Style
        style_row = QHBoxLayout()
        style_row.addWidget(_lbl("Style:", "labelMuted"))
        self._xhair_style = QComboBox()
        self._xhair_style.addItems(
            ["cross", "dot", "circle", "t-shape", "x-shape", "cross+dot"])
        self._xhair_style.currentTextChanged.connect(self._update_crosshair)
        style_row.addWidget(self._xhair_style, 1)
        ctrl.addLayout(style_row)

        # Color
        color_row = QHBoxLayout()
        color_row.addWidget(_lbl("Color:", "labelMuted"))
        self._color_btn = QPushButton("  ")
        self._color_btn.setStyleSheet(
            "background: #FF0000; border-radius: 4px; min-width: 40px;")
        self._color_btn.clicked.connect(self._pick_color)
        color_row.addWidget(self._color_btn)
        color_row.addStretch()
        ctrl.addLayout(color_row)

        # Sliders
        for title, attr, minv, maxv, defv in [
            ("Size", "_sl_size", 5, 50, 20),
            ("Thickness", "_sl_thick", 1, 8, 2),
            ("Gap", "_sl_gap", 0, 20, 5),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(title + ":"))
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setRange(minv, maxv)
            sl.setValue(defv)
            sl.valueChanged.connect(self._update_crosshair)
            setattr(self, attr, sl)
            vl = QLabel(str(defv))
            vl.setObjectName("labelOrange")
            vl.setMinimumWidth(25)
            sl.valueChanged.connect(lambda v, l=vl: l.setText(str(v)))
            row.addWidget(sl, 1)
            row.addWidget(vl)
            ctrl.addLayout(row)

        content.addLayout(ctrl, 1)
        layout.addLayout(content)

        # Presets
        presets_row = QHBoxLayout()
        presets_row.addWidget(_lbl("Presets:", "labelMuted"))
        for name, style, color, size, thick, gap in [
            ("Default", "cross", "#FF0000", 20, 2, 5),
            ("Tiny Dot", "dot", "#00FF00", 5, 3, 0),
            ("Pro", "cross", "#00FFFF", 12, 1, 3),
            ("Circle", "circle", "#FFFF00", 15, 2, 0),
        ]:
            btn = QPushButton(name)
            btn.setObjectName("btnSmall")
            btn.clicked.connect(
                lambda _, st=style, co=color, si=size, th=thick, ga=gap:
                self._apply_crosshair_preset(st, co, si, th, ga))
            presets_row.addWidget(btn)
        presets_row.addStretch()
        layout.addLayout(presets_row)

        return card

    def _make_recoil_section(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        layout.addWidget(_lbl("RECOIL PATTERN REFERENCE", "cardTitle"))
        layout.addWidget(_sep())

        gun_row = QHBoxLayout()
        gun_row.addWidget(_lbl("Weapon:", "labelMuted"))
        self._gun_combo = QComboBox()
        self._gun_combo.addItems(["AKM", "M416", "SCAR-L", "UZI", "AWM"])
        self._gun_combo.currentTextChanged.connect(self._update_recoil)
        gun_row.addWidget(self._gun_combo, 1)
        layout.addLayout(gun_row)

        self._recoil_widget = RecoilPattern()
        layout.addWidget(self._recoil_widget)

        info = _lbl(
            "● Green = initial shots\n● Red = later shots\n"
            "Pull crosshair opposite to pattern", "labelMuted")
        info.setStyleSheet("font-size: 10px; color: #5A7090;")
        layout.addWidget(info)

        return card

    def _make_hud_section(self):
        card = QWidget()
        card.setObjectName("cardBlue")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(_lbl("PERFORMANCE HUD OVERLAY", "cardTitle"))
        self._hud_toggle = ToggleSwitch(color_on="#00C8FF")
        self._hud_toggle.toggled.connect(self._toggle_hud)
        header.addStretch()
        self._hud_status = _lbl("OFF", "labelMuted")
        header.addWidget(self._hud_status)
        header.addWidget(self._hud_toggle)
        layout.addLayout(header)
        layout.addWidget(_sep())

        # HUD metrics checkboxes
        from PyQt6.QtWidgets import QCheckBox
        metrics_row = QHBoxLayout()
        self._hud_checks = {}
        for metric in ["FPS", "Ping", "CPU %", "GPU %", "RAM %", "Temp"]:
            cb = QCheckBox(metric)
            cb.setChecked(True)
            metrics_row.addWidget(cb)
            self._hud_checks[metric] = cb
        layout.addLayout(metrics_row)

        # Position
        pos_row = QHBoxLayout()
        pos_row.addWidget(_lbl("Position:", "labelMuted"))
        self._hud_pos = QComboBox()
        self._hud_pos.addItems(["Top Right", "Top Left", "Bottom Right", "Bottom Left"])
        pos_row.addWidget(self._hud_pos, 1)

        pos_row.addWidget(_lbl("Opacity:", "labelMuted"))
        self._hud_opacity = QSlider(Qt.Orientation.Horizontal)
        self._hud_opacity.setRange(20, 100)
        self._hud_opacity.setValue(80)
        self._hud_opacity_lbl = QLabel("80%")
        self._hud_opacity_lbl.setObjectName("labelCyan")
        self._hud_opacity.valueChanged.connect(
            lambda v: self._hud_opacity_lbl.setText(f"{v}%"))
        pos_row.addWidget(self._hud_opacity, 1)
        pos_row.addWidget(self._hud_opacity_lbl)
        layout.addLayout(pos_row)

        return card

    def _make_process_killer(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(_lbl("BACKGROUND PROCESS KILLER", "cardTitle"))
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("btnSmall")
        refresh_btn.clicked.connect(self._refresh_processes)
        kill_btn = QPushButton("Kill Selected")
        kill_btn.setObjectName("btnDanger")
        kill_btn.clicked.connect(self._kill_selected)
        kill_bloat_btn = QPushButton("Kill All Bloat")
        kill_bloat_btn.setObjectName("btnDanger")
        kill_bloat_btn.clicked.connect(self._kill_bloat)
        header.addStretch()
        header.addWidget(refresh_btn)
        header.addWidget(kill_btn)
        header.addWidget(kill_bloat_btn)
        layout.addLayout(header)

        self._proc_table = QTableWidget(0, 4)
        self._proc_table.setHorizontalHeaderLabels(["Process", "PID", "CPU %", "RAM MB"])
        self._proc_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self._proc_table.setMinimumHeight(180)   # always visible
        self._proc_table.setMaximumHeight(300)
        self._proc_table.setAlternatingRowColors(True)
        self._proc_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self._proc_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._proc_table)

        self._refresh_processes()
        return card

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _update_crosshair(self):
        self._xhair_canvas.set_style(self._xhair_style.currentText())
        self._xhair_canvas.set_size(self._sl_size.value())
        self._xhair_canvas.set_thickness(self._sl_thick.value())
        self._xhair_canvas.set_gap(self._sl_gap.value())
        settings = {
            "style": self._xhair_style.currentText(),
            "size": self._sl_size.value(),
            "thickness": self._sl_thick.value(),
            "gap": self._sl_gap.value(),
            "color": self._xhair_canvas._color.name(),
        }
        self._overlay.apply_settings(settings)

    def _pick_color(self):
        color = QColorDialog.getColor(self._xhair_canvas._color, self)
        if color.isValid():
            self._color_btn.setStyleSheet(
                f"background: {color.name()}; border-radius: 4px; min-width: 40px;")
            self._xhair_canvas.set_color(color.name())

    def _apply_crosshair_preset(self, style, color, size, thick, gap):
        self._xhair_style.setCurrentText(style)
        self._color_btn.setStyleSheet(
            f"background: {color}; border-radius: 4px; min-width: 40px;")
        self._xhair_canvas.set_color(color)
        self._sl_size.setValue(size)
        self._sl_thick.setValue(thick)
        self._sl_gap.setValue(gap)

    def _toggle_overlay(self, checked):
        if checked:
            self._overlay.apply_settings({
                "style": self._xhair_style.currentText(),
                "size": self._sl_size.value(),
                "thickness": self._sl_thick.value(),
                "gap": self._sl_gap.value(),
                "color": self._xhair_canvas._color.name(),
            })
            self._overlay.show_overlay()
            self._overlay_status.setText("ACTIVE")
            self._overlay_status.setObjectName("labelGreen")
        else:
            self._overlay.hide_overlay()
            self._overlay_status.setText("OFF")
            self._overlay_status.setObjectName("labelRed")
        self._overlay_status.style().unpolish(self._overlay_status)
        self._overlay_status.style().polish(self._overlay_status)

    def _toggle_hud(self, checked):
        if checked:
            self._hud_status.setText("ACTIVE")
            self._hud_status.setStyleSheet("color: #00C8FF; font-weight: 700;")
        else:
            self._hud_status.setText("OFF")
            self._hud_status.setStyleSheet("color: #5A7090;")

    def _update_recoil(self, gun):
        self._recoil_widget.set_gun(gun)

    def _refresh_processes(self):
        procs = process_manager.get_running_processes()[:30]
        self._proc_table.setRowCount(0)   # clear first to avoid stale rows
        self._proc_table.setRowCount(len(procs))
        for row, proc in enumerate(procs):
            name_item = QTableWidgetItem(proc["name"])
            pid_item  = QTableWidgetItem(str(proc["pid"]))
            cpu_val   = proc["cpu"]
            mem_val   = proc["mem"]   # percentage

            cpu_item = QTableWidgetItem(f"{cpu_val:.1f}%")
            if cpu_val > 30:
                cpu_item.setForeground(QColor("#FF3366"))
            elif cpu_val > 10:
                cpu_item.setForeground(QColor("#FF6B00"))
            else:
                cpu_item.setForeground(QColor("#DCE8FF"))

            # Convert % to approximate MB using total RAM
            try:
                import psutil as _ps
                total_mb = _ps.virtual_memory().total / 1024 / 1024
                mem_mb = mem_val * total_mb / 100
                mem_str = f"{mem_mb:.0f} MB"
            except Exception:
                mem_str = f"{mem_val:.1f}%"
            mem_item = QTableWidgetItem(mem_str)

            self._proc_table.setItem(row, 0, name_item)
            self._proc_table.setItem(row, 1, pid_item)
            self._proc_table.setItem(row, 2, cpu_item)
            self._proc_table.setItem(row, 3, mem_item)

    def _kill_selected(self):
        selected = self._proc_table.selectedItems()
        if not selected:
            return
        for row in set(item.row() for item in selected):
            pid_item = self._proc_table.item(row, 1)
            if pid_item:
                try:
                    process_manager.kill_process(pid=int(pid_item.text()))
                except Exception:
                    pass
        self._refresh_processes()

    def _kill_bloat(self):
        process_manager.kill_bloat()
        self._refresh_processes()

    def _start_proc_timer(self):
        self._proc_timer = QTimer(self)
        self._proc_timer.timeout.connect(self._refresh_processes)
        self._proc_timer.start(10000)
