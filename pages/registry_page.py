"""
GameLoop Registry Tweaks Page — RT Tool
Authoritative registry reference, direct tweak applicator, and .reg exporter.
"""

import os
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit, QFileDialog,
    QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QFont, QCursor

from core.registry_data import (
    REGISTRY_TWEAKS, CATEGORIES, SAFETY_LEVELS, SAFETY_COLORS,
    filter_tweaks, generate_reg_command, generate_ps_command,
    generate_reg_file_content, apply_tweak, open_regedit
)


def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    return f


def _lbl(text, obj="labelPrimary"):
    l = QLabel(text)
    l.setObjectName(obj)
    return l


class RegistryWorker(QObject):
    finished = pyqtSignal(bool, str)

    def __init__(self, tweak):
        super().__init__()
        self._tweak = tweak

    def run(self):
        success, msg = apply_tweak(self._tweak)
        self.finished.emit(success, msg)


class RegistryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_tweaks = list(REGISTRY_TWEAKS)
        self._selected_tweak = REGISTRY_TWEAKS[0] if REGISTRY_TWEAKS else None
        self._setup_ui()
        self._populate_table()
        if self._selected_tweak:
            self._update_inspector(self._selected_tweak)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Main scrollable container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(16)

        # Header
        layout.addLayout(self._make_header())

        # Warning / RegEdit Banner
        layout.addWidget(self._make_warning_banner())

        # Filter Bar
        layout.addWidget(self._make_filter_card())

        # Splitter with Table and Inspector
        layout.addWidget(self._make_main_splitter(), 1)

    def _make_header(self):
        h = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(_lbl("GameLoop Registry Tweaks", "pageTitle"))
        left.addWidget(_lbl("Authoritative Registry Engine Reference · Direct Modifications · .reg Exporter", "pageSubtitle"))
        h.addLayout(left)
        h.addStretch()

        # Stats badges
        safe_count = sum(1 for t in REGISTRY_TWEAKS if t["safety"] == "Safe")
        stats_widget = QWidget()
        stats_widget.setObjectName("card")
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(14, 8, 14, 8)
        stats_layout.setSpacing(16)

        s1 = QLabel(f"<b>{len(REGISTRY_TWEAKS)}</b> Tweaks")
        s1.setStyleSheet("color: #DCE8FF; font-size: 11px;")
        s2 = QLabel(f"<b>{safe_count}</b> 100% Safe")
        s2.setStyleSheet("color: #00FF88; font-size: 11px;")
        stats_layout.addWidget(s1)
        stats_layout.addWidget(s2)

        h.addWidget(stats_widget)
        return h

    def _make_warning_banner(self):
        banner = QWidget()
        banner.setObjectName("card")
        banner.setStyleSheet(
            "QWidget#card { background-color: #0F1626; border: 1px solid #FF6B00; border-radius: 8px; }"
        )
        l = QHBoxLayout(banner)
        l.setContentsMargins(18, 12, 18, 12)
        l.setSpacing(14)

        icon_lbl = QLabel("⚠")
        icon_lbl.setStyleSheet("font-size: 20px; color: #FF6B00;")
        l.addWidget(icon_lbl)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title = QLabel("ADMINISTRATOR PRIVILEGES & RESTART NOTICE")
        title.setStyleSheet("font-size: 11px; font-weight: 800; color: #FF6B00; letter-spacing: 1.5px;")
        desc = QLabel(
            "Registry adjustments fine-tune the Tencent VM hypervisor and Windows multimedia scheduler. "
            "Restart GameLoop (AndroidProcess.exe & AppMarket.exe) after modifications for settings to activate."
        )
        desc.setStyleSheet("font-size: 11px; color: #8A9FB8;")
        desc.setWordWrap(True)
        text_layout.addWidget(title)
        text_layout.addWidget(desc)
        l.addLayout(text_layout, 1)

        regedit_btn = QPushButton("Launch RegEdit")
        regedit_btn.setObjectName("btnGhost")
        regedit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        regedit_btn.clicked.connect(self._on_launch_regedit)
        l.addWidget(regedit_btn)

        return banner

    def _make_filter_card(self):
        card = QWidget()
        card.setObjectName("card")
        l = QHBoxLayout(card)
        l.setContentsMargins(16, 12, 16, 12)
        l.setSpacing(12)

        # Search box
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search tweaks, key names, registry paths, impact...")
        self._search_input.textChanged.connect(self._on_filter_changed)
        l.addWidget(self._search_input, 2)

        # Category dropdown
        self._cat_combo = QComboBox()
        self._cat_combo.addItems(CATEGORIES)
        self._cat_combo.currentTextChanged.connect(self._on_filter_changed)
        l.addWidget(self._cat_combo, 1)

        # Safety dropdown
        self._safety_combo = QComboBox()
        self._safety_combo.addItems(SAFETY_LEVELS)
        self._safety_combo.currentTextChanged.connect(self._on_filter_changed)
        l.addWidget(self._safety_combo, 1)

        # Export View button
        export_view_btn = QPushButton("Export Filtered (.reg)")
        export_view_btn.setObjectName("btnGhost")
        export_view_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        export_view_btn.clicked.connect(self._on_export_filtered)
        l.addWidget(export_view_btn)

        # Export All button
        export_all_btn = QPushButton("Export All (.reg)")
        export_all_btn.setObjectName("btnPrimary")
        export_all_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        export_all_btn.clicked.connect(self._on_export_all)
        l.addWidget(export_all_btn)

        return card

    def _make_main_splitter(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: Table card
        table_card = QWidget()
        table_card.setObjectName("card")
        tl = QVBoxLayout(table_card)
        tl.setContentsMargins(12, 12, 12, 12)
        tl.setSpacing(8)

        # Header row above table
        top_row = QHBoxLayout()
        self._table_count_lbl = QLabel(f"Showing {len(REGISTRY_TWEAKS)} tweaks")
        self._table_count_lbl.setStyleSheet("font-size: 11px; color: #5A7090;")
        top_row.addWidget(self._table_count_lbl)
        top_row.addStretch()
        tl.addLayout(top_row)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Setting Name", "Value Name", "Rec.", "Category", "Safety"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self._table.setColumnWidth(1, 130)
        self._table.setColumnWidth(2, 60)
        self._table.setColumnWidth(3, 120)
        self._table.setColumnWidth(4, 65)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setMinimumHeight(340)
        self._table.itemSelectionChanged.connect(self._on_row_selected)
        tl.addWidget(self._table)

        splitter.addWidget(table_card)

        # Right: Inspector card
        inspector_card = self._make_inspector_card()
        splitter.addWidget(inspector_card)

        splitter.setSizes([640, 460])
        return splitter

    def _make_inspector_card(self):
        self._insp_card = QWidget()
        self._insp_card.setObjectName("card")
        layout = QVBoxLayout(self._insp_card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        # Header: Name + Safety Badge
        top = QHBoxLayout()
        self._insp_name_lbl = QLabel("Tweak Inspector")
        self._insp_name_lbl.setStyleSheet("font-size: 14px; font-weight: 800; color: #DCE8FF;")
        self._insp_name_lbl.setWordWrap(True)
        top.addWidget(self._insp_name_lbl, 1)

        self._insp_safety_badge = QLabel("SAFE")
        self._insp_safety_badge.setStyleSheet(
            "background-color: #0B2217; color: #00FF88; font-size: 10px; "
            "font-weight: 800; padding: 3px 8px; border-radius: 4px; border: 1px solid #00FF88;"
        )
        top.addWidget(self._insp_safety_badge)
        layout.addLayout(top)

        # Category
        self._insp_cat_lbl = QLabel("Category")
        self._insp_cat_lbl.setStyleSheet("font-size: 11px; color: #5A7090; letter-spacing: 0.5px;")
        layout.addWidget(self._insp_cat_lbl)

        layout.addWidget(_sep())

        # Path & Value Grid
        props_grid = QVBoxLayout()
        props_grid.setSpacing(4)

        self._insp_path_val = QLabel("HKCU\\...")
        self._insp_path_val.setStyleSheet("font-family: Consolas, monospace; font-size: 11px; color: #00C8FF;")
        self._insp_path_val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._insp_path_val.setWordWrap(True)

        self._insp_key_val = QLabel("ValueName")
        self._insp_key_val.setStyleSheet("font-family: Consolas, monospace; font-size: 11px; color: #FFD700;")
        self._insp_key_val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self._insp_type_val = QLabel("REG_DWORD")
        self._insp_type_val.setStyleSheet("font-size: 11px; color: #8A9FB8;")

        self._insp_rec_val = QLabel("1")
        self._insp_rec_val.setStyleSheet("font-size: 12px; font-weight: 700; color: #00FF88;")

        self._insp_def_val = QLabel("0")
        self._insp_def_val.setStyleSheet("font-size: 11px; color: #5A7090;")

        def row(label, val_widget):
            rl = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 11px; color: #5A7090; min-width: 90px;")
            rl.addWidget(lbl)
            rl.addWidget(val_widget, 1)
            return rl

        props_grid.addLayout(row("Registry Path:", self._insp_path_val))
        props_grid.addLayout(row("Value Name:", self._insp_key_val))
        props_grid.addLayout(row("Data Type:", self._insp_type_val))
        props_grid.addLayout(row("Recommended:", self._insp_rec_val))
        props_grid.addLayout(row("Default:", self._insp_def_val))
        layout.addLayout(props_grid)

        layout.addWidget(_sep())

        # Explanation / Impact
        layout.addWidget(_lbl("PERFORMANCE IMPACT & MECHANISM", "cardTitle"))
        self._insp_impact_lbl = QLabel("")
        self._insp_impact_lbl.setStyleSheet("font-size: 11px; color: #DCE8FF; line-height: 1.4;")
        self._insp_impact_lbl.setWordWrap(True)
        layout.addWidget(self._insp_impact_lbl)

        layout.addWidget(_sep())

        # Command Preview Box
        layout.addWidget(_lbl("COMMAND PREVIEW (REG.EXE)", "cardTitle"))
        self._insp_cmd_box = QTextEdit()
        self._insp_cmd_box.setObjectName("console")
        self._insp_cmd_box.setReadOnly(True)
        self._insp_cmd_box.setFixedHeight(46)
        layout.addWidget(self._insp_cmd_box)

        # Status feedback label
        self._action_status_lbl = QLabel("")
        self._action_status_lbl.setStyleSheet("font-size: 11px; color: #00FF88;")
        layout.addWidget(self._action_status_lbl)

        # Action Buttons
        btn_row1 = QHBoxLayout()
        btn_row1.setSpacing(8)

        self._copy_path_btn = QPushButton("Copy Path")
        self._copy_path_btn.setObjectName("btnGhost")
        self._copy_path_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._copy_path_btn.clicked.connect(self._on_copy_path)
        btn_row1.addWidget(self._copy_path_btn)

        self._copy_cmd_btn = QPushButton("Copy reg.exe Command")
        self._copy_cmd_btn.setObjectName("btnGhost")
        self._copy_cmd_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._copy_cmd_btn.clicked.connect(self._on_copy_cmd)
        btn_row1.addWidget(self._copy_cmd_btn)
        layout.addLayout(btn_row1)

        self._apply_btn = QPushButton("Apply Tweak to Registry")
        self._apply_btn.setObjectName("btnPrimary")
        self._apply_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._apply_btn.clicked.connect(self._on_apply_selected)
        layout.addWidget(self._apply_btn)

        layout.addStretch()
        return self._insp_card

    # ── Table Data & Filtering ────────────────────────────────────────────────

    def _populate_table(self):
        self._table.setRowCount(0)
        self._table.setRowCount(len(self._current_tweaks))

        for row, tweak in enumerate(self._current_tweaks):
            # 0: Setting Name
            item_name = QTableWidgetItem(tweak["name"])
            item_name.setForeground(QColor("#DCE8FF"))
            self._table.setItem(row, 0, item_name)

            # 1: Value Name
            item_vname = QTableWidgetItem(tweak["value_name"])
            item_vname.setForeground(QColor("#FFD700"))
            self._table.setItem(row, 1, item_vname)

            # 2: Recommended Value
            rec_str = str(tweak["recommended"])
            item_rec = QTableWidgetItem(rec_str)
            item_rec.setForeground(QColor("#00FF88"))
            self._table.setItem(row, 2, item_rec)

            # 3: Category
            item_cat = QTableWidgetItem(tweak["category"])
            item_cat.setForeground(QColor("#8A9FB8"))
            self._table.setItem(row, 3, item_cat)

            # 4: Safety Level
            safety = tweak["safety"]
            item_safety = QTableWidgetItem(safety)
            color_hex = SAFETY_COLORS.get(safety, "#DCE8FF")
            item_safety.setForeground(QColor(color_hex))
            self._table.setItem(row, 4, item_safety)

        self._table_count_lbl.setText(f"Showing {len(self._current_tweaks)} of {len(REGISTRY_TWEAKS)} tweaks")

        if self._current_tweaks:
            self._table.selectRow(0)

    def _on_filter_changed(self):
        search = self._search_input.text()
        cat = self._cat_combo.currentText()
        safety = self._safety_combo.currentText()
        self._current_tweaks = filter_tweaks(cat, safety, search)
        self._populate_table()

    def _on_row_selected(self):
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if 0 <= row < len(self._current_tweaks):
            self._selected_tweak = self._current_tweaks[row]
            self._update_inspector(self._selected_tweak)

    def _update_inspector(self, tweak):
        self._action_status_lbl.setText("")
        self._insp_name_lbl.setText(tweak["name"])
        self._insp_cat_lbl.setText(f"{tweak['category'].upper()}")

        # Safety badge
        safety = tweak["safety"]
        color = SAFETY_COLORS.get(safety, "#00FF88")
        bg = "#0B2217" if safety == "Safe" else ("#26200A" if safety == "Cautious" else "#26130B")
        self._insp_safety_badge.setText(safety.upper())
        self._insp_safety_badge.setStyleSheet(
            f"background-color: {bg}; color: {color}; font-size: 10px; "
            f"font-weight: 800; padding: 3px 8px; border-radius: 4px; border: 1px solid {color};"
        )

        # Path details
        self._insp_path_val.setText(tweak["path"])
        self._insp_key_val.setText(tweak["value_name"])
        self._insp_type_val.setText(tweak["value_type"])
        self._insp_rec_val.setText(str(tweak["recommended"]))
        self._insp_def_val.setText(str(tweak["default_val"]))

        # Explanation
        self._insp_impact_lbl.setText(tweak["impact"])

        # Command Preview
        cmd = generate_reg_command(tweak)
        self._insp_cmd_box.setPlainText(cmd)

    # ── Action Handlers ───────────────────────────────────────────────────────

    def _on_copy_path(self):
        if not self._selected_tweak:
            return
        from PyQt6.QtWidgets import QApplication
        text = f"{self._selected_tweak['path']}\\{self._selected_tweak['value_name']}"
        QApplication.clipboard().setText(text)
        self._action_status_lbl.setText("✓ Path copied to clipboard")

    def _on_copy_cmd(self):
        if not self._selected_tweak:
            return
        from PyQt6.QtWidgets import QApplication
        cmd = generate_reg_command(self._selected_tweak)
        QApplication.clipboard().setText(cmd)
        self._action_status_lbl.setText("✓ reg.exe command copied to clipboard")

    def _on_apply_selected(self):
        if not self._selected_tweak:
            return
        tweak = self._selected_tweak
        safety = tweak["safety"]

        if safety in ("Advanced", "Danger"):
            confirm = QMessageBox.warning(
                self,
                f"Confirm {safety} Tweak",
                f"Setting '{tweak['name']}' is classified as {safety}.\n\n"
                f"Path: {tweak['path']}\n"
                f"Value: {tweak['value_name']} = {tweak['recommended']}\n\n"
                "Are you sure you want to write this to Windows Registry?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

        self._action_status_lbl.setText("Writing to registry...")
        self._apply_btn.setEnabled(False)

        def worker():
            success, msg = apply_tweak(tweak)
            self._on_apply_finished(success, msg)

        threading.Thread(target=worker, daemon=True).start()

    def _on_apply_finished(self, success: bool, msg: str):
        self._apply_btn.setEnabled(True)
        if success:
            self._action_status_lbl.setStyleSheet("font-size: 11px; color: #00FF88;")
            self._action_status_lbl.setText(f"✓ {msg}")
        else:
            self._action_status_lbl.setStyleSheet("font-size: 11px; color: #FF3366;")
            self._action_status_lbl.setText(f"✗ {msg}")

    def _on_export_filtered(self):
        if not self._current_tweaks:
            QMessageBox.information(self, "Export .reg", "No tweaks match current filter.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Filtered GameLoop Registry Script",
            "GameLoop_Filtered_Tweaks.reg",
            "Registry Files (*.reg)"
        )
        if not filename:
            return

        cat = self._cat_combo.currentText()
        content = generate_reg_file_content(self._current_tweaks, title=f"GameLoop Tweaks ({cat})")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Export Successful", f"Saved {len(self._current_tweaks)} tweaks to:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not write file: {e}")

    def _on_export_all(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save All GameLoop Registry Tweaks",
            "GameLoop_All_Performance_Tweaks.reg",
            "Registry Files (*.reg)"
        )
        if not filename:
            return

        content = generate_reg_file_content(REGISTRY_TWEAKS, title="All Recommended GameLoop Tweaks")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Export Successful", f"Saved all {len(REGISTRY_TWEAKS)} tweaks to:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not write file: {e}")

    def _on_launch_regedit(self):
        path = self._selected_tweak["path"] if self._selected_tweak else r"Software\Tencent\MobileGamePC"
        open_regedit(path)
        self._action_status_lbl.setText("Launched Windows Registry Editor")
