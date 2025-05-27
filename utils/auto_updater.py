# Delta_Mon/utils/auto_updater.py

import requests
import json
import os
import sys
import subprocess
import tempfile
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QIcon


class UpdateChecker(QThread):
    """Background thread to check for updates"""
    update_available = Signal(dict)  # Emits update info
    no_update = Signal()
    error_occurred = Signal(str)

    def __init__(self, current_version: str, github_repo: str = "carpsesdema/Delta_Mon"):
        super().__init__()
        self.current_version = current_version
        self.github_repo = github_repo
        self.api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"

    def run(self):
        try:
            print(f"🔍 Checking for updates...")

            headers = {
                'User-Agent': 'DeltaMon-UpdateChecker',
                'Accept': 'application/vnd.github.v3+json'
            }

            response = requests.get(self.api_url, headers=headers, timeout=10)

            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name'].lstrip('v')

                print(f"   Current: v{self.current_version}")
                print(f"   Latest: v{latest_version}")

                if self._is_newer_version(latest_version, self.current_version):
                    # Get download URL for .exe file
                    download_url = None
                    file_size = 0

                    for asset in release_data.get('assets', []):
                        if asset['name'].endswith('.exe'):
                            download_url = asset['browser_download_url']
                            file_size = asset['size']
                            break

                    if download_url:
                        update_info = {
                            'version': latest_version,
                            'current_version': self.current_version,
                            'changelog': release_data.get('body', 'No changelog available'),
                            'download_url': download_url,
                            'file_size': file_size,
                            'published_at': release_data.get('published_at'),
                            'release_url': release_data.get('html_url')
                        }
                        print(f"✅ Update available: v{latest_version}")
                        self.update_available.emit(update_info)
                    else:
                        print(f"⚠️ Update available but no .exe file found")
                        self.no_update.emit()
                else:
                    print(f"✅ Already up to date")
                    self.no_update.emit()
            else:
                self.error_occurred.emit(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            print(f"❌ Update check failed: {e}")
            self.error_occurred.emit(str(e))

    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings (semantic versioning)"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]

            # Ensure both have 3 parts
            while len(latest_parts) < 3:
                latest_parts.append(0)
            while len(current_parts) < 3:
                current_parts.append(0)

            return latest_parts > current_parts
        except Exception:
            return False


class UpdateDialog(QDialog):
    """Dialog to show update information and options"""

    def __init__(self, update_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setWindowTitle("DeltaMon Update Available")
        self.setFixedSize(500, 400)

        # Dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                padding: 5px;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #5a5a5a;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton#updateButton {
                background-color: #27ae60;
            }
            QPushButton#updateButton:hover {
                background-color: #2ecc71;
            }
            QPushButton#skipButton {
                background-color: #e74c3c;
            }
            QPushButton#skipButton:hover {
                background-color: #c0392b;
            }
        """)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("🚀 DeltaMon Update Available!")
        header.setStyleSheet("font-size: 16pt; font-weight: bold; color: #3498db;")
        layout.addWidget(header)

        # Version info
        current_version = self.update_info['current_version']
        new_version = self.update_info['version']

        version_info = QLabel(f"📦 New Version: v{new_version}\n📋 Current: v{current_version}")
        version_info.setStyleSheet("font-size: 12pt; padding: 10px;")
        layout.addWidget(version_info)

        # File size
        file_size_mb = self.update_info['file_size'] / (1024 * 1024)
        size_label = QLabel(f"📏 Download Size: {file_size_mb:.1f} MB")
        layout.addWidget(size_label)

        # Changelog
        changelog_label = QLabel("📝 What's New:")
        changelog_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(changelog_label)

        changelog_text = self.update_info['changelog']
        if len(changelog_text) > 200:
            changelog_text = changelog_text[:200] + "..."

        changelog = QLabel(changelog_text)
        changelog.setWordWrap(True)
        changelog.setStyleSheet("padding: 10px; background-color: #3c3c3c; border-radius: 4px;")
        layout.addWidget(changelog)

        # Buttons
        button_layout = QHBoxLayout()

        view_release_btn = QPushButton("🌐 View Release")
        view_release_btn.clicked.connect(self.view_release_page)
        button_layout.addWidget(view_release_btn)

        skip_btn = QPushButton("⏭️ Skip")
        skip_btn.setObjectName("skipButton")
        skip_btn.clicked.connect(self.reject)
        button_layout.addWidget(skip_btn)

        remind_btn = QPushButton("⏰ Remind Later")
        remind_btn.clicked.connect(self.remind_later)
        button_layout.addWidget(remind_btn)

        update_btn = QPushButton("⬇️ Download Update")
        update_btn.setObjectName("updateButton")
        update_btn.clicked.connect(self.download_update)
        button_layout.addWidget(update_btn)

        layout.addLayout(button_layout)

    def view_release_page(self):
        """Open the GitHub release page"""
        webbrowser.open(self.update_info['release_url'])

    def remind_later(self):
        """Remind in 24 hours"""
        self.done(2)  # Custom result code for "remind later"

    def download_update(self):
        """Open download URL in browser"""
        webbrowser.open(self.update_info['download_url'])

        # Show instructions
        instructions = QMessageBox(self)
        instructions.setWindowTitle("Download Instructions")
        instructions.setText(
            "🎉 Download Started!\n\n"
            "Instructions:\n"
            "1. Save the .exe file to your desired location\n"
            "2. Close DeltaMon completely\n"
            "3. Run the new .exe file\n"
            "4. Your settings will be preserved!\n\n"
            "The download should start automatically in your browser."
        )
        instructions.setIcon(QMessageBox.Icon.Information)
        instructions.exec()

        self.accept()


class AutoUpdater:
    """Main auto-updater class for DeltaMon"""

    def __init__(self, current_version: str, parent_widget=None):
        self.current_version = current_version
        self.parent_widget = parent_widget
        self.github_repo = "carpsesdema/Delta_Mon"

        # Settings
        self.check_interval_hours = 24  # Check daily
        self.auto_check_enabled = True
        self.last_check_file = Path("last_update_check.json")

        # Timer for periodic checks
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_for_updates_background)

        print(f"🔄 AutoUpdater initialized for DeltaMon v{current_version}")

    def start_periodic_checks(self):
        """Start automatic periodic update checks"""
        if not self.auto_check_enabled:
            return

        # Check if we should check now
        if self._should_check_for_updates():
            print("🔍 Starting initial update check...")
            self.check_for_updates_background()

        # Set up periodic checks (every hour, but only actually check if enough time has passed)
        self.check_timer.start(60 * 60 * 1000)  # 1 hour in milliseconds
        print(f"⏰ Periodic update checks enabled (every {self.check_interval_hours} hours)")

    def stop_periodic_checks(self):
        """Stop automatic update checks"""
        self.check_timer.stop()

    def check_for_updates_manual(self):
        """Manual update check triggered by user"""
        print("🔍 Manual update check requested...")
        self._check_for_updates(show_no_update_message=True)

    def check_for_updates_background(self):
        """Background update check (no message if no update)"""
        if not self._should_check_for_updates():
            return

        print("🔍 Background update check...")
        self._check_for_updates(show_no_update_message=False)

    def _should_check_for_updates(self) -> bool:
        """Check if enough time has passed since last check"""
        try:
            if not self.last_check_file.exists():
                return True

            with open(self.last_check_file, 'r') as f:
                data = json.load(f)

            last_check = datetime.fromisoformat(data.get('last_check', '2020-01-01'))
            time_since_check = datetime.now() - last_check

            return time_since_check.total_seconds() > (self.check_interval_hours * 3600)

        except Exception:
            return True

    def _update_last_check_time(self):
        """Update the last check timestamp"""
        try:
            data = {'last_check': datetime.now().isoformat()}
            with open(self.last_check_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Warning: Could not save last check time: {e}")

    def _check_for_updates(self, show_no_update_message: bool = False):
        """Perform the actual update check"""
        self.checker = UpdateChecker(self.current_version, self.github_repo)
        self.checker.update_available.connect(lambda info: self._handle_update_available(info))
        self.checker.no_update.connect(lambda: self._handle_no_update(show_no_update_message))
        self.checker.error_occurred.connect(lambda error: self._handle_update_error(error, show_no_update_message))
        self.checker.start()

    def _handle_update_available(self, update_info: Dict[str, Any]):
        """Handle when an update is available"""
        print(f"✅ Update available: v{update_info['version']}")

        self._update_last_check_time()

        # Show update dialog
        dialog = UpdateDialog(update_info, self.parent_widget)
        result = dialog.exec()

        if result == 2:  # Remind later
            print("⏰ User chose to be reminded later")
            # Don't update last check time so we'll check again sooner

    def _handle_no_update(self, show_message: bool):
        """Handle when no update is available"""
        self._update_last_check_time()

        if show_message:
            print("✅ No updates available")
            if self.parent_widget:
                msg = QMessageBox(self.parent_widget)
                msg.setWindowTitle("No Updates")
                msg.setText("✅ You're running the latest version of DeltaMon!")
                msg.setIcon(QMessageBox.Icon.Information)
                msg.exec()

    def _handle_update_error(self, error: str, show_message: bool):
        """Handle update check errors"""
        print(f"❌ Update check error: {error}")

        if show_message:
            if self.parent_widget:
                msg = QMessageBox(self.parent_widget)
                msg.setWindowTitle("Update Check Failed")
                msg.setText(f"❌ Could not check for updates:\n\n{error}\n\nPlease check your internet connection.")
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.exec()

    def get_current_version(self) -> str:
        """Get the current version"""
        return self.current_version

    def set_auto_check_enabled(self, enabled: bool):
        """Enable/disable automatic update checks"""
        self.auto_check_enabled = enabled
        if enabled:
            self.start_periodic_checks()
        else:
            self.stop_periodic_checks()


# Example usage and testing
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Test update checker
    updater = AutoUpdater("1.0.0")  # Simulate older version
    updater.check_for_updates_manual()

    sys.exit(app.exec())