"""
RT Tool — PUBG Mobile Gameloop Optimizer
Main Entry Point
Portable Windows Desktop Application
Python 3.13 + PyQt6
"""

import sys
import os

# Ensure the app directory is in the path
_app_dir = os.path.dirname(os.path.abspath(__file__))
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPixmap, QPainter, QLinearGradient, QBrush

from ui.main_window import MainWindow


def create_splash() -> QSplashScreen:
    """Create a custom splash screen."""
    pixmap = QPixmap(500, 280)
    pixmap.fill(QColor("#070B13"))

    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Gradient background
    grad = QLinearGradient(0, 0, 500, 280)
    grad.setColorAt(0, QColor("#070B13"))
    grad.setColorAt(0.5, QColor("#0C1422"))
    grad.setColorAt(1, QColor("#070B13"))
    p.fillRect(0, 0, 500, 280, QBrush(grad))

    # Border
    from PyQt6.QtGui import QPen
    p.setPen(QPen(QColor("#FF6B00"), 2))
    p.drawRect(1, 1, 498, 278)

    # Title
    p.setPen(QColor("#FF6B00"))
    font = QFont("Segoe UI", 36, QFont.Weight.Black)
    p.setFont(font)
    p.drawText(0, 60, 500, 80, Qt.AlignmentFlag.AlignCenter, "RT TOOL")

    # Subtitle
    p.setPen(QColor("#5A7090"))
    font2 = QFont("Segoe UI", 10, QFont.Weight.Normal)
    font2.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
    p.setFont(font2)
    p.drawText(0, 120, 500, 40, Qt.AlignmentFlag.AlignCenter,
               "PUBG MOBILE  ·  GAMELOOP  ·  OPTIMIZER")

    # Loading bar background
    p.setPen(QColor("#1A2740"))
    p.setBrush(QBrush(QColor("#1A2740")))
    p.drawRoundedRect(50, 200, 400, 6, 3, 3)

    # Loading bar fill
    bar_grad = QLinearGradient(50, 0, 450, 0)
    bar_grad.setColorAt(0, QColor("#FF6B00"))
    bar_grad.setColorAt(1, QColor("#FF9500"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(bar_grad))
    p.drawRoundedRect(50, 200, 350, 6, 3, 3)

    # Loading text
    p.setPen(QColor("#5A7090"))
    font3 = QFont("Segoe UI", 9)
    p.setFont(font3)
    p.drawText(0, 218, 500, 30, Qt.AlignmentFlag.AlignCenter,
               "Initializing system modules...")

    # Version
    p.setPen(QColor("#2A3D5A"))
    font4 = QFont("Segoe UI", 8)
    p.setFont(font4)
    p.drawText(0, 255, 500, 20, Qt.AlignmentFlag.AlignCenter, "v1.0.0  —  Portable Edition")

    p.end()

    splash = QSplashScreen(pixmap)
    splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
    return splash


def main():
    # High DPI support
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("QT_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("RT Tool")
    app.setApplicationDisplayName("RT Tool — PUBG Mobile Gameloop Optimizer")
    app.setApplicationVersion("1.0.0")

    # Dark palette for fallback
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor("#070B13"))
    palette.setColor(palette.ColorRole.WindowText, QColor("#DCE8FF"))
    palette.setColor(palette.ColorRole.Base, QColor("#0C1422"))
    palette.setColor(palette.ColorRole.AlternateBase, QColor("#0D1828"))
    palette.setColor(palette.ColorRole.Text, QColor("#DCE8FF"))
    palette.setColor(palette.ColorRole.Button, QColor("#12213A"))
    palette.setColor(palette.ColorRole.ButtonText, QColor("#DCE8FF"))
    palette.setColor(palette.ColorRole.Highlight, QColor("#FF6B00"))
    palette.setColor(palette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)

    # Show splash
    splash = create_splash()
    splash.show()
    app.processEvents()

    # Load main window after brief delay
    def launch():
        window = MainWindow()
        window.show()
        splash.finish(window)

    QTimer.singleShot(1800, launch)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
