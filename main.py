import sys
from PySide6.QtWidgets import QApplication, QMenuBar, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer
from ui.scaled_main_window import OverlayMainWindow  # or OverlayMainWindow
from utils.auto_updater import AutoUpdater
import os

# DeltaMon Version - UPDATE THIS WHEN RELEASING!
VERSION = "1.0.1"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("DeltaMon - OptionDelta Monitor")
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("TradingTools")

    # Set application icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'app_icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        print(f"Warning: Application icon not found at {icon_path}")

    # Create main window INSTANCE (not class!)
    window = OverlayMainWindow()  # <-- FIXED: Added parentheses!

    # Add auto-updater
    updater = AutoUpdater(VERSION, window)

    # Add update menu to main window
    if hasattr(window, 'menuBar'):
        # If main window has a menu bar, add update menu
        help_menu = window.menuBar().addMenu("Help")

        check_updates_action = QAction("🔍 Check for Updates", window)
        check_updates_action.triggered.connect(updater.check_for_updates_manual)
        help_menu.addAction(check_updates_action)

        about_action = QAction(f"About DeltaMon v{VERSION}", window)
        about_action.triggered.connect(lambda: show_about_dialog(window))
        help_menu.addAction(about_action)
    else:
        # If no menu bar, add update button to the UI
        print(f"💡 Add 'Check Updates' button to UI - version {VERSION}")

        # Example: Add to existing layout (adjust based on your UI structure)
        if hasattr(window, 'main_layout'):
            from PySide6.QtWidgets import QPushButton, QHBoxLayout

            update_layout = QHBoxLayout()

            update_button = QPushButton("🔍 Check Updates")
            update_button.clicked.connect(updater.check_for_updates_manual)
            update_layout.addWidget(update_button)

            version_label = QPushButton(f"v{VERSION}")
            version_label.setEnabled(False)
            update_layout.addWidget(version_label)

            update_layout.addStretch()

            # Add to the top of your main layout
            window.main_layout.insertLayout(0, update_layout)

    # Start automatic update checks (will check once on startup, then daily)
    QTimer.singleShot(5000, updater.start_periodic_checks)  # Start after 5 seconds

    # Show window and start app
    window.show()

    print(f"🚀 DeltaMon v{VERSION} started with auto-updater enabled")
    print(f"   📦 Update checks: Every 24 hours")
    print(f"   🔗 GitHub: https://github.com/carpsesdema/Delta_Mon")

    sys.exit(app.exec())


def show_about_dialog(parent):
    """Show about dialog"""
    from PySide6.QtWidgets import QMessageBox

    msg = QMessageBox(parent)
    msg.setWindowTitle("About DeltaMon")
    msg.setText(f"""
<h2>🚀 DeltaMon v{VERSION}</h2>
<p><b>OptionDelta Monitor for ThinkOrSwim</b></p>

<h3>Features:</h3>
<ul>
<li>✅ OptionDelta monitoring</li>
<li>✅ Account auto-discovery</li>
<li>✅ Discord/Telegram alerts</li>
<li>✅ Always-on-top overlay</li>
<li>✅ Bundled OCR (no setup required)</li>
<li>✅ Automatic updates</li>
</ul>

<p><b>GitHub:</b> <a href="https://github.com/carpsesdema/Delta_Mon">carpsesdema/Delta_Mon</a></p>
<p><b>Built with:</b> PySide6, OpenCV, Tesseract OCR</p>
""")
    msg.setTextFormat(1)  # Rich text
    msg.exec()