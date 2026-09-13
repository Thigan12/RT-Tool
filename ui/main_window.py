"""
Main Window — RT Tool
QMainWindow shell with sidebar navigation, top bar, and stacked pages.
"""

import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette

from ui.widgets.stat_card import MiniStatBar
from ui.icons import get_pixmap, get_icon, get_dual_state_icon
from pages.home_page import HomePage
from pages.performance_page import PerformancePage
from pages.network_page import NetworkPage
from pages.display_page import DisplayPage
from pages.input_page import InputPage
from pages.audio_page import AudioPage
from pages.gaming_page import GamingPage
from pages.profiles_page import ProfilesPage
from pages.registry_page import RegistryPage
from core.system_info import get_cpu_usage, get_ram_usage, get_gpu_usage_simple


# (key, display_label, icon_name)
NAV_ITEMS = [
    ("home",        "Launch Hub",       "launch"),
    ("performance", "Performance",      "performance"),
    ("network",     "Network",          "network"),
    ("display",     "Display",          "display"),
    ("input",       "Input",            "input"),
    ("audio",       "Audio",            "audio"),
    ("gaming",      "Gaming Features",  "gaming"),
    ("profiles",    "Profiles",         "profiles"),
    ("registry",    "Registry Tweaks",  "registry"),
]

PAGE_TITLES = {
    "home":        ("Launch Hub",       "launch",      "Detect · Optimize · Launch"),
    "performance": ("Performance",      "performance", "GPU · CPU · RAM · Latency"),
    "network":     ("Network",          "network",     "Ping · DNS · Servers · TCP"),
    "display":     ("Display",          "display",     "Resolution · FPS · Color"),
    "input":       ("Input",            "input",       "Mouse · Keyboard · Raw Input"),
    "audio":       ("Audio",            "audio",       "Spatial · EQ · Latency"),
    "gaming":      ("Gaming Features",  "gaming",      "Crosshair · Recoil · HUD"),
    "profiles":    ("Profiles",         "profiles",    "Presets · Custom · Settings"),
    "registry":    ("Registry Tweaks",  "registry",    "GameLoop · Engine · Reference"),
}

# Colour constants
_ICON_MUTED  = "#3A4F6A"
_ICON_ACTIVE = "#FF6B00"
_ICON_SIZE   = 18


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RT Tool — PUBG Mobile Gameloop Optimizer")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self._current_page = "home"
        self._nav_buttons = {}
        self._nav_icons = {}       # key → icon_name string
        self._setup_ui()
        self._apply_style()
        self._start_stat_timer()

    # ── UI Setup ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        main_layout.addWidget(self._make_sidebar())

        # Right panel (top bar + content)
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._make_topbar())
        right.addWidget(self._make_content_area(), 1)
        right_widget = QWidget()
        right_widget.setObjectName("contentArea")
        right_widget.setLayout(right)
        main_layout.addWidget(right_widget, 1)

    def _make_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo area
        logo_widget = QWidget()
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(16, 20, 16, 14)
        logo_layout.setSpacing(2)

        logo_lbl = QLabel("RT TOOL")
        logo_lbl.setObjectName("sidebarLogo")
        sub_lbl = QLabel("PUBG · GAMELOOP · BOOST")
        sub_lbl.setObjectName("sidebarSubtitle")
        logo_layout.addWidget(logo_lbl)
        logo_layout.addWidget(sub_lbl)
        layout.addWidget(logo_widget)

        # Divider
        div = QFrame()
        div.setObjectName("sidebarDivider")
        div.setFixedHeight(1)
        layout.addWidget(div)

        # Spacer
        layout.addSpacing(6)

        # Nav buttons
        nav_section_lbl = QLabel("MAIN MENU")
        nav_section_lbl.setStyleSheet(
            "font-size: 9px; color: #2A3D5A; letter-spacing: 3px; "
            "padding: 8px 16px 4px 16px;")
        layout.addWidget(nav_section_lbl)

        for key, label, icon_name in NAV_ITEMS:
            # Build dual-state icon (muted ↔ active orange)
            dual_icon = get_dual_state_icon(
                icon_name, _ICON_SIZE, _ICON_MUTED, _ICON_ACTIVE)
            btn = QPushButton(f"  {label}")
            btn.setObjectName("navBtn")
            btn.setIcon(dual_icon)
            btn.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
            btn.setProperty("active", key == "home")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self._navigate(k))
            layout.addWidget(btn)
            self._nav_buttons[key] = btn
            self._nav_icons[key] = icon_name

        layout.addStretch()

        # Bottom info
        div2 = QFrame()
        div2.setObjectName("sidebarDivider")
        div2.setFixedHeight(1)
        layout.addWidget(div2)

        self._active_profile_lbl = QLabel("Profile: Mid-Range")
        self._active_profile_lbl.setStyleSheet(
            "font-size: 10px; color: #5A7090; padding: 10px 16px 4px 16px;")
        layout.addWidget(self._active_profile_lbl)

        self._sidebar_status_lbl = QLabel("● System Ready")
        self._sidebar_status_lbl.setStyleSheet(
            "font-size: 10px; color: #00FF88; padding: 0px 16px 16px 16px;")
        layout.addWidget(self._sidebar_status_lbl)

        return sidebar

    def _make_topbar(self):
        topbar = QWidget()
        topbar.setObjectName("topBar")
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(10)

        # Page icon (vector, 18px, orange)
        self._topbar_icon = QLabel()
        self._topbar_icon.setFixedSize(20, 20)
        px = get_pixmap("launch", 18, "#FF6B00")
        self._topbar_icon.setPixmap(px)
        layout.addWidget(self._topbar_icon)

        # Page title
        self._page_title_lbl = QLabel("Launch Hub")
        self._page_title_lbl.setObjectName("topBarTitle")
        layout.addWidget(self._page_title_lbl)

        # Separator dot
        dot = QLabel("•")
        dot.setStyleSheet("color: #1A2740; font-size: 16px;")
        layout.addWidget(dot)

        # Breadcrumb
        self._page_sub_lbl = QLabel("Detect · Optimize · Launch")
        self._page_sub_lbl.setObjectName("labelMuted")
        self._page_sub_lbl.setStyleSheet("font-size: 11px; color: #2A3D5A;")
        layout.addWidget(self._page_sub_lbl)

        layout.addStretch()

        # Mini stat bar
        self._mini_stats = MiniStatBar()
        layout.addWidget(self._mini_stats)

        layout.addSpacing(16)

        # Active badge
        self._active_badge = QLabel("MID-RANGE PROFILE")
        self._active_badge.setObjectName("topBarBadge")
        layout.addWidget(self._active_badge)

        return topbar

    def _make_content_area(self):
        self._stack = QStackedWidget()
        self._stack.setObjectName("pageContainer")

        # Instantiate all pages
        self._pages = {
            "home":        HomePage(),
            "performance": PerformancePage(),
            "network":     NetworkPage(),
            "display":     DisplayPage(),
            "input":       InputPage(),
            "audio":       AudioPage(),
            "gaming":      GamingPage(),
            "profiles":    ProfilesPage(),
            "registry":    RegistryPage(),
        }

        for page in self._pages.values():
            self._stack.addWidget(page)

        # Connect profile_applied signal
        self._pages["profiles"].profile_applied.connect(self._on_profile_applied)

        return self._stack

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate(self, key):
        if key == self._current_page:
            return
        self._current_page = key

        # Update sidebar buttons (QSS active property)
        for k, btn in self._nav_buttons.items():
            btn.setProperty("active", k == key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Update top bar: title, icon, subtitle
        title, icon_name, sub = PAGE_TITLES.get(
            key, (key.title(), "launch", ""))
        self._page_title_lbl.setText(title)
        self._page_sub_lbl.setText(sub)
        # Swap the top-bar icon
        px = get_pixmap(icon_name, 18, "#FF6B00")
        self._topbar_icon.setPixmap(px)

        # Show page
        self._stack.setCurrentWidget(self._pages[key])

    # ── Live Stats ────────────────────────────────────────────────────────────

    def _start_stat_timer(self):
        self._stat_timer = QTimer(self)
        self._stat_timer.timeout.connect(self._update_stats)
        self._stat_timer.start(3000)
        self._update_stats()

    def _update_stats(self):
        cpu = int(get_cpu_usage())
        ram = int(get_ram_usage())
        gpu = int(get_gpu_usage_simple())
        self._mini_stats.update_stats(fps=60, cpu=cpu, gpu=gpu, ram=ram)

    def _on_profile_applied(self, key):
        names = {"budget": "BUDGET", "mid": "MID-RANGE",
                 "high": "HIGH-END", "enthusiast": "ENTHUSIAST"}
        name = names.get(key, key.upper())
        self._active_badge.setText(f"{name} PROFILE")
        self._active_profile_lbl.setText(f"Profile: {name.title()}")

    # ── Styling ───────────────────────────────────────────────────────────────

    def _apply_style(self):
        """Load the QSS stylesheet."""
        qss_path = os.path.join(os.path.dirname(__file__), "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            # Minimal fallback
            self.setStyleSheet("""
                QWidget { background: #070B13; color: #DCE8FF; }
                QPushButton { background: #12213A; color: #DCE8FF;
                              padding: 6px 14px; border-radius: 5px; }
            """)
