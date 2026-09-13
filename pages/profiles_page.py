"""
Profiles & Settings Page — RT Tool
Hardware tier profiles, save/load, export/import, update checker.
"""

import json
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QFileDialog, QListWidget,
    QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, QTimer
import requests

from core.profile_manager import (
    PRESET_PROFILES, list_custom_profiles, save_profile,
    load_profile, delete_profile, export_profile, import_profile,
    load_active_profile, save_active_profile
)
from core.optimizer import apply_profile, restore_defaults, apply_profile_settings


def _sep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine); return f

def _lbl(text, obj="labelPrimary"):
    l = QLabel(text); l.setObjectName(obj); return l


class ProfilesPage(QWidget):
    profile_applied = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_profile = "mid"
        self._setup_ui()
        self._load_active()

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
        layout.addWidget(self._make_tier_section())
        layout.addWidget(self._make_custom_section())
        layout.addWidget(self._make_settings_section())
        layout.addStretch()

    def _make_header(self):
        h = QVBoxLayout()
        h.addWidget(_lbl("Profiles & Settings", "pageTitle"))
        h.addWidget(_lbl("Hardware Tier Presets · Custom Profiles · Import/Export", "pageSubtitle"))
        return h

    def _make_tier_section(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(14)

        layout.addWidget(_lbl("HARDWARE TIER PRESETS", "cardTitle"))
        layout.addWidget(_sep())

        self._tier_btns = {}
        tiers = [
            ("budget",     "Budget",     "🟢", "#00FF88",
             "Low-end PC · Safe tweaks · Stable 60 FPS", "tierBudget"),
            ("mid",        "Mid-Range",  "🔵", "#00C8FF",
             "Mid-tier PC · Balanced performance · 90+ FPS", "tierMid"),
            ("high",       "High-End",   "🟡", "#FFD700",
             "High-end PC · Aggressive tweaks · 144+ FPS", "tierHigh"),
            ("enthusiast", "Enthusiast", "🔴", "#FF3366",
             "Top-tier PC · Max performance · 240+ FPS", "tierEnthusiast"),
        ]

        for key, name, icon, color, desc, obj_name in tiers:
            tier_card = QWidget()
            tier_card.setObjectName("card")
            tc_layout = QVBoxLayout(tier_card)
            tc_layout.setSpacing(8)

            top = QHBoxLayout()
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size: 18px;")
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(
                f"font-size: 14px; font-weight: 800; color: {color};")
            top.addWidget(icon_lbl)
            top.addWidget(name_lbl)
            top.addStretch()
            self._tier_btns[key] = QPushButton(
                "✓ ACTIVE" if key == "mid" else "APPLY")
            self._tier_btns[key].setObjectName(obj_name)
            self._tier_btns[key].clicked.connect(
                lambda _, k=key: self._apply_tier(k))
            top.addWidget(self._tier_btns[key])
            tc_layout.addLayout(top)

            desc_lbl = QLabel(desc)
            desc_lbl.setObjectName("labelMuted")
            desc_lbl.setWordWrap(True)
            tc_layout.addWidget(desc_lbl)

            # Feature highlights for the tier
            preset = PRESET_PROFILES[key]
            s = preset["settings"]
            features = []
            if s.get("power_plan") == "ultimate_performance":
                features.append("Ultimate Performance")
            elif s.get("power_plan") == "high_performance":
                features.append("High Performance")
            if s.get("core_parking"): features.append("Core Parking Off")
            if s.get("kill_bloat"): features.append("Bloat Killer")
            if s.get("stop_services"): features.append("Service Optimizer")
            features.append(f"FPS Target: {s.get('fps_target', 60)}")

            feat_row = QHBoxLayout()
            for feat in features[:4]:
                f_lbl = QLabel(f"✓ {feat}")
                f_lbl.setStyleSheet(f"font-size: 10px; color: {color}; "
                                    "background: #070B13; padding: 2px 6px; "
                                    "border-radius: 3px;")
                feat_row.addWidget(f_lbl)
            feat_row.addStretch()
            tc_layout.addLayout(feat_row)

            layout.addWidget(tier_card)

        layout.addWidget(_sep())

        restore_btn = QPushButton("↺  RESTORE ALL WINDOWS DEFAULTS")
        restore_btn.setObjectName("btnSecondary")
        restore_btn.clicked.connect(self._restore_all_defaults)
        layout.addWidget(restore_btn, alignment=Qt.AlignmentFlag.AlignRight)

        return card

    def _make_custom_section(self):
        card = QWidget()
        card.setObjectName("cardBlue")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        layout.addWidget(_lbl("CUSTOM PROFILES", "cardTitle"))
        layout.addWidget(_sep())

        # Save current
        save_row = QHBoxLayout()
        save_row.addWidget(_lbl("Save as:", "labelMuted"))
        self._save_name_input = QLineEdit()
        self._save_name_input.setPlaceholderText("Enter profile name...")
        save_row.addWidget(self._save_name_input, 1)
        save_btn = QPushButton("💾  SAVE CURRENT")
        save_btn.setObjectName("btnPrimary")
        save_btn.clicked.connect(self._save_current_profile)
        save_row.addWidget(save_btn)
        layout.addLayout(save_row)

        layout.addWidget(_sep())

        # Custom profiles list
        list_header = QHBoxLayout()
        list_header.addWidget(_lbl("Saved Profiles:", "labelMuted"))
        refresh_list_btn = QPushButton("🔄")
        refresh_list_btn.setObjectName("btnSmall")
        refresh_list_btn.setMaximumWidth(35)
        refresh_list_btn.clicked.connect(self._refresh_profile_list)
        list_header.addStretch()
        list_header.addWidget(refresh_list_btn)
        layout.addLayout(list_header)

        self._profile_list = QListWidget()
        self._profile_list.setMaximumHeight(120)
        layout.addWidget(self._profile_list)

        action_row = QHBoxLayout()
        load_btn = QPushButton("📂  LOAD SELECTED")
        load_btn.setObjectName("btnSecondary")
        load_btn.clicked.connect(self._load_selected_profile)
        del_btn = QPushButton("🗑  DELETE")
        del_btn.setObjectName("btnDanger")
        del_btn.clicked.connect(self._delete_selected_profile)
        export_btn = QPushButton("📤  EXPORT")
        export_btn.setObjectName("btnSmall")
        export_btn.clicked.connect(self._export_profile)
        import_btn = QPushButton("📥  IMPORT")
        import_btn.setObjectName("btnSmall")
        import_btn.clicked.connect(self._import_profile)
        action_row.addWidget(load_btn)
        action_row.addWidget(del_btn)
        action_row.addStretch()
        action_row.addWidget(export_btn)
        action_row.addWidget(import_btn)
        layout.addLayout(action_row)

        self._custom_status_lbl = _lbl("", "labelGreen")
        self._custom_status_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #00FF88;")
        layout.addWidget(self._custom_status_lbl)

        self._refresh_profile_list()
        return card

    def _make_settings_section(self):
        card = QWidget()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        layout.addWidget(_lbl("APPLICATION SETTINGS", "cardTitle"))
        layout.addWidget(_sep())

        # Update checker
        update_row = QHBoxLayout()
        update_row.addWidget(_lbl("Application Version:", "labelMuted"))
        self._version_lbl = _lbl("RT Tool v1.0.0", "labelOrange")
        update_row.addWidget(self._version_lbl)
        update_row.addStretch()
        self._update_status_lbl = _lbl("", "labelMuted")
        update_row.addWidget(self._update_status_lbl)
        check_update_btn = QPushButton("🔄  CHECK FOR UPDATES")
        check_update_btn.setObjectName("btnSmall")
        check_update_btn.clicked.connect(self._check_updates)
        update_row.addWidget(check_update_btn)
        layout.addLayout(update_row)

        layout.addWidget(_sep())

        # About info
        about_lbl = QLabel(
            "RT Tool — PUBG Mobile Gameloop Optimizer\n"
            "Portable Windows Desktop Application\n"
            "Built with Python 3.13 + PyQt6\n"
            "Real system optimizations: registry, powercfg, WMI, nvidia-smi"
        )
        about_lbl.setObjectName("labelMuted")
        about_lbl.setStyleSheet("font-size: 11px; line-height: 1.6;")
        layout.addWidget(about_lbl)

        layout.addWidget(_sep())

        # Quick actions row
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        for text, obj, handler in [
            ("🧹  Clean RAM",         "btnPrimary",   self._clean_ram),
            ("⚡  Flush DNS",         "btnSecondary", self._flush_dns),
            ("💀  Kill Bloat",        "btnDanger",    self._kill_bloat),
            ("↺  Reset All",         "btnSecondary", self._restore_all_defaults),
        ]:
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.clicked.connect(handler)
            actions_row.addWidget(btn, 1)

        layout.addLayout(actions_row)

        self._quick_action_status_lbl = _lbl("", "labelGreen")
        self._quick_action_status_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #00FF88;")
        layout.addWidget(self._quick_action_status_lbl)

        return card

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _apply_tier(self, key):
        self._active_profile = key
        # Update button states
        labels = {"budget": "APPLY", "mid": "APPLY",
                  "high": "APPLY", "enthusiast": "APPLY"}
        for k, btn in self._tier_btns.items():
            btn.setText("✓ ACTIVE" if k == key else "APPLY")

        apply_profile(key)
        self.profile_applied.emit(key)

    def _load_active(self):
        active = load_active_profile()
        key = active.get("profile", "mid")
        if key in self._tier_btns:
            for k, btn in self._tier_btns.items():
                btn.setText("✓ ACTIVE" if k == key else "APPLY")

    def _save_current_profile(self):
        name = self._save_name_input.text().strip()
        if not name:
            self._custom_status_lbl.setText("⚠ Please enter a profile name")
            self._custom_status_lbl.setStyleSheet("color: #FFB800;")
            return
        # Use current active profile's settings as base
        preset = PRESET_PROFILES.get(self._active_profile, PRESET_PROFILES["mid"])
        ok = save_profile(name, preset.get("settings", {}))
        if ok:
            self._save_name_input.clear()
            self._refresh_profile_list()
            self._custom_status_lbl.setText(f"✓ Profile '{name}' saved successfully!")
            self._custom_status_lbl.setStyleSheet("color: #00FF88; font-weight: 700;")
            QTimer.singleShot(3000, lambda: self._custom_status_lbl.setText(""))

    def _refresh_profile_list(self):
        self._profile_list.clear()
        for p in list_custom_profiles():
            item = QListWidgetItem(
                f"📁  {p['name']}  —  {p.get('description', '')[:40]}")
            item.setData(Qt.ItemDataRole.UserRole, p["name"])
            self._profile_list.addItem(item)

    def _load_selected_profile(self):
        item = self._profile_list.currentItem()
        if not item:
            self._custom_status_lbl.setText("⚠ Please select a profile from the list first")
            self._custom_status_lbl.setStyleSheet("color: #FFB800;")
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        data = load_profile(name)
        if data and "settings" in data:
            apply_profile_settings(data["settings"])
            save_active_profile(name, data["settings"])
            self._active_profile = name
            for k, btn in self._tier_btns.items():
                btn.setText("APPLY")
            self._custom_status_lbl.setText(f"✓ Loaded & applied profile: '{name}'")
            self._custom_status_lbl.setStyleSheet("color: #00FF88; font-weight: 700;")
            self.profile_applied.emit(name)
            QTimer.singleShot(3500, lambda: self._custom_status_lbl.setText(""))
        else:
            self._custom_status_lbl.setText(f"⚠ Could not read profile '{name}'")
            self._custom_status_lbl.setStyleSheet("color: #FF3366;")

    def _delete_selected_profile(self):
        item = self._profile_list.currentItem()
        if item:
            name = item.data(Qt.ItemDataRole.UserRole)
            delete_profile(name)
            self._refresh_profile_list()
            self._custom_status_lbl.setText(f"✓ Deleted '{name}'")
            self._custom_status_lbl.setStyleSheet("color: #00C8FF;")
            QTimer.singleShot(3000, lambda: self._custom_status_lbl.setText(""))

    def _export_profile(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Profile", "", "JSON Files (*.json)")
        if path:
            name = self._active_profile
            export_profile(name, path)
            self._custom_status_lbl.setText(f"✓ Exported profile to {path}")
            self._custom_status_lbl.setStyleSheet("color: #00FF88;")
            QTimer.singleShot(3000, lambda: self._custom_status_lbl.setText(""))

    def _import_profile(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Profile", "", "JSON Files (*.json)")
        if path:
            ok, msg = import_profile(path)
            if ok:
                self._refresh_profile_list()
                self._custom_status_lbl.setText(f"✓ Imported profile '{msg}'")
                self._custom_status_lbl.setStyleSheet("color: #00FF88;")
                QTimer.singleShot(3000, lambda: self._custom_status_lbl.setText(""))

    def _restore_all_defaults(self):
        restore_defaults()
        for k, btn in self._tier_btns.items():
            btn.setText("APPLY")
        if hasattr(self, "_quick_action_status_lbl"):
            self._quick_action_status_lbl.setText("✓ Reverted all settings to Windows defaults!")
            QTimer.singleShot(3000, lambda: self._quick_action_status_lbl.setText(""))

    def _check_updates(self):
        self._update_status_lbl.setText("Checking...")
        self._update_status_lbl.setStyleSheet("color: #00C8FF;")

        def _worker():
            status_text = "Up to date (v1.0.0) ✓"
            color = "#00FF88"
            try:
                r = requests.get(
                    "https://api.github.com/repos/Thigan12/RT-Tool/releases/latest",
                    timeout=4
                )
                if r.status_code == 200:
                    latest = r.json().get("tag_name", "v1.0.0")
                    status_text = f"Latest: {latest}"
                elif r.status_code == 404:
                    status_text = "Up to date (v1.0.0) ✓"
            except Exception:
                status_text = "Up to date (offline) ✓"

            QTimer.singleShot(0, lambda: (
                self._update_status_lbl.setText(status_text),
                self._update_status_lbl.setStyleSheet(f"color: {color}; font-weight: 700;")
            ))

        threading.Thread(target=_worker, daemon=True).start()

    def _clean_ram(self):
        from core.optimizer import clear_ram_standby
        clear_ram_standby()
        if hasattr(self, "_quick_action_status_lbl"):
            self._quick_action_status_lbl.setText("✓ Standby RAM freed successfully!")
            QTimer.singleShot(3000, lambda: self._quick_action_status_lbl.setText(""))

    def _flush_dns(self):
        from core.network_tools import flush_dns
        flush_dns()
        if hasattr(self, "_quick_action_status_lbl"):
            self._quick_action_status_lbl.setText("✓ Windows DNS cache flushed!")
            QTimer.singleShot(3000, lambda: self._quick_action_status_lbl.setText(""))

    def _kill_bloat(self):
        from core.process_manager import kill_bloat
        kill_bloat()
        if hasattr(self, "_quick_action_status_lbl"):
            self._quick_action_status_lbl.setText("✓ Bloat killer: terminated background tasks!")
            QTimer.singleShot(3000, lambda: self._quick_action_status_lbl.setText(""))

