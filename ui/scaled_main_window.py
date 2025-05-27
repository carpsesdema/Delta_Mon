from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QAbstractItemView,
    QHeaderView, QLabel, QTableWidgetItem, QApplication,
    QProgressBar, QTextEdit, QSplitter, QGroupBox, QGridLayout,
    QSpinBox, QCheckBox, QScrollArea, QFrame, QDialog
)
from PySide6.QtCore import Qt, Slot, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QIcon

import time
import os
from datetime import datetime

from utils.config_manager import ConfigManager
from core.enhanced_window_manager import EnhancedWindowManager
from core.tos_navigator import TosNavigator
from utils.credential_manager import CredentialManager
from utils.tos_launcher import TosLauncher
from ui.login_dialog import LoginDialog

OVERLAY_DARK_STYLE_SHEET = """
    QWidget {
        background-color: #1a1a1a;
        color: #ffffff;
        font-size: 9pt;
    }
    QMainWindow {
        background-color: #1a1a1a;
        border: 2px solid #3498db;
    }
    QPushButton {
        background-color: #2c3e50;
        color: #ffffff;
        border: 1px solid #34495e;
        padding: 4px;
        min-height: 16px;
        border-radius: 3px;
        font-size: 8pt;
    }
    QPushButton:hover {
        background-color: #34495e;
    }
    QPushButton:pressed {
        background-color: #4a6fa5;
    }
    QPushButton:disabled {
        background-color: #2c3e50;
        color: #7f8c8d;
    }
    QPushButton#setupButton {
        background-color: #2980b9;
    }
    QPushButton#setupButton:hover {
        background-color: #3498db;
    }
    QPushButton#criticalButton {
        background-color: #e74c3c;
        font-weight: bold;
    }
    QPushButton#criticalButton:hover {
        background-color: #c0392b;
    }
    QPushButton#warningButton {
        background-color: #f39c12;
        color: #2c3e50;
        font-weight: bold;
    }
    QPushButton#warningButton:hover {
        background-color: #e67e22;
    }
    QPushButton#successButton {
        background-color: #27ae60;
        font-weight: bold;
    }
    QPushButton#successButton:hover {
        background-color: #2ecc71;
    }
    QPushButton#editButton {
        background-color: #8e44ad;
        font-weight: bold;
    }
    QPushButton#editButton:hover {
        background-color: #9b59b6;
    }
    QTableWidget {
        background-color: #2c3e50;
        color: #ffffff;
        gridline-color: #34495e;
        border: 1px solid #34495e;
        border-radius: 3px;
        alternate-background-color: #34495e;
    }
    QHeaderView::section {
        background-color: #34495e;
        color: #ffffff;
        padding: 2px;
        border: 1px solid #4a6fa5;
        font-weight: bold;
        font-size: 8pt;
    }
    QTableWidget::item {
        padding: 2px;
        font-size: 8pt;
    }
    QTableWidget::item:selected {
        background-color: #3498db;
        color: #ffffff;
    }
    QLabel#statusLabel {
        font-weight: bold;
        padding: 3px;
        color: #ecf0f1;
        border: 1px solid #3498db;
        border-radius: 3px;
        background-color: #2c3e50;
    }
    QLabel#alertCount {
        background-color: #e74c3c;
        color: white;
        font-weight: bold;
        padding: 3px 6px;
        border-radius: 8px;
        font-size: 9pt;
    }
    QLabel#alertCountGreen {
        background-color: #27ae60;
        color: white;
        font-weight: bold;
        padding: 3px 6px;
        border-radius: 8px;
        font-size: 9pt;
    }
    QGroupBox {
        font-weight: bold;
        border: 1px solid #34495e;
        border-radius: 4px;
        margin: 3px 0px;
        padding-top: 8px;
        font-size: 8pt;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px 0 4px;
    }
    QProgressBar {
        background-color: #2c3e50;
        border: 1px solid #34495e;
        border-radius: 3px;
        text-align: center;
        font-size: 8pt;
        max-height: 15px;
    }
    QProgressBar::chunk {
        background-color: #3498db;
        border-radius: 2px;
    }
    QSpinBox {
        background-color: #2c3e50;
        border: 1px solid #34495e;
        border-radius: 3px;
        padding: 2px;
        font-size: 8pt;
    }
    QTextEdit {
        background-color: #2c3e50;
        border: 1px solid #34495e;
        border-radius: 3px;
        color: #ffffff;
        font-family: 'Consolas', monospace;
        font-size: 8pt;
    }
"""


class AutoLoginWorker(QThread):
    status_update = Signal(str)
    progress_update = Signal(int)
    login_complete = Signal(bool)

    def __init__(self, username, password, executable_path, tos_launcher, window_manager):
        super().__init__()
        self.username = username
        self.password = password
        self.executable_path = executable_path
        self.tos_launcher = tos_launcher
        self.window_manager = window_manager

    def run(self):
        try:
            self.status_update.emit("🚀 Starting automatic ToS login...")
            self.progress_update.emit(10)

            self.status_update.emit("🔍 Checking current ToS status...")
            status_report = self.window_manager.get_tos_status_report()
            self.progress_update.emit(15)

            if status_report['main_trading_available']:
                self.status_update.emit("✅ Main trading window already available! Login successful.")
                self.progress_update.emit(100)
                self.login_complete.emit(True)
                return

            if status_report['total_tos_windows'] == 0 or status_report['launcher_open']:
                if not self.executable_path or not os.path.exists(self.executable_path):
                    self.status_update.emit(f"❌ Invalid or missing ToS executable path: {self.executable_path}")
                    self.login_complete.emit(False)
                    return

                self.status_update.emit(f"🚀 Launching Thinkorswim from: {os.path.basename(self.executable_path)}...")
                self.progress_update.emit(20)

                launch_success = self.tos_launcher.launch_tos(self.executable_path)
                if not launch_success:
                    self.status_update.emit("❌ Failed to launch ToS application.")
                    self.login_complete.emit(False)
                    return

                self.status_update.emit("✅ ToS launch command sent, waiting for interface...")
                self.progress_update.emit(40)
            elif not status_report['login_required']:
                self.status_update.emit("ℹ️ ToS state ambiguous, attempting login anyway...")

            self.status_update.emit("⏳ Waiting for ToS login screen to be ready...")
            self.progress_update.emit(50)

            login_sequence_initiated = self.tos_launcher.login_to_tos(self.username, self.password)
            self.progress_update.emit(70)

            if not login_sequence_initiated:
                self.status_update.emit("❌ Automatic login input sequence failed or login window not found.")
                self.login_complete.emit(False)
                return

            self.status_update.emit("✅ Login credentials submitted.")
            self.progress_update.emit(85)

            self.status_update.emit("⏳ Waiting for main trading window to appear post-login...")
            main_window_hwnd = self.window_manager.wait_for_main_trading_window(timeout_seconds=60)

            if main_window_hwnd:
                self.status_update.emit("🎉 Login successful! Main trading window is ready.")
                self.progress_update.emit(100)
                self.login_complete.emit(True)
            else:
                self.status_update.emit("❌ Main trading window did not appear after login attempt.")
                self.login_complete.emit(False)

        except Exception as e:
            self.status_update.emit(f"❌ AutoLoginWorker error: {str(e)}")
            self.login_complete.emit(False)


class ScaledTemplateSetupWorker(QThread):
    status_update = Signal(str)
    progress_update = Signal(int)
    finished_setup = Signal(bool)

    def __init__(self, tos_navigator):
        super().__init__()
        self.tos_navigator = tos_navigator
        if not self.tos_navigator:
            raise ValueError("TosNavigator cannot be None for ScaledTemplateSetupWorker")

    def run(self):
        try:
            self.status_update.emit("🚀 Starting template setup...")
            self.progress_update.emit(5)

            if not self.tos_navigator or not self.tos_navigator.hwnd:
                self.status_update.emit("❌ Critical Error: ToS Navigator not properly initialized or HWND missing.")
                self.finished_setup.emit(False)
                return

            capture_width_ratio = 0.4
            capture_height_ratio = 0.5

            self.status_update.emit(
                f"ℹ️ Using capture region: {capture_width_ratio * 100:.0f}% width, {capture_height_ratio * 100:.0f}% height of ToS window (upper-left).")
            self.progress_update.emit(10)

            self.status_update.emit("📸 Capturing initial state (BEFORE your click)...")
            before_path = self.tos_navigator.capture_upper_left_region(
                "template_setup_before_click.png",
                width_ratio=capture_width_ratio,
                height_ratio=capture_height_ratio
            )
            if not before_path:
                self.status_update.emit(
                    "❌ Failed to capture 'before click' state. Check ToS window visibility and focus.")
                self.finished_setup.emit(False)
                return
            self.status_update.emit(f"✅ 'Before click' state captured: {os.path.basename(before_path)}")
            self.progress_update.emit(35)

            self.status_update.emit("‼️ USER ACTION REQUIRED ‼️")
            self.status_update.emit(
                "👉 In the ToS window, please CLICK the 'Account: <TOTAL>...' bar (or your account dropdown trigger) NOW!")
            self.status_update.emit(
                "⏳ You have 10 seconds. Ensure the account list dropdown EXPANDS and is fully visible.")

            for i in range(10, 0, -1):
                self.status_update.emit(
                    f"   Waiting for click... {i}s remaining. (Dropdown should be open and visible)")
                time.sleep(1)
                current_progress = 35 + int((10 - i) * 4.5)
                self.progress_update.emit(current_progress)

            self.status_update.emit("📸 Capturing 'after click' state (dropdown should be open)...")
            after_path = self.tos_navigator.capture_upper_left_region(
                "template_setup_after_click.png",
                width_ratio=capture_width_ratio,
                height_ratio=capture_height_ratio
            )
            if not after_path:
                self.status_update.emit(
                    "❌ Failed to capture 'after click' state. Was the dropdown opened and visible within the capture area?")
                self.finished_setup.emit(False)
                return
            self.status_update.emit(f"✅ 'After click' state captured: {os.path.basename(after_path)}")
            self.progress_update.emit(85)

            self.status_update.emit("🔍 Creating 'account_dropdown_template.png' from difference...")
            template_created = self.tos_navigator._create_template_from_difference(
                before_path,
                after_path,
                output_template_name="account_dropdown_template.png"
            )

            if template_created:
                self.progress_update.emit(95)
                self.status_update.emit("🧪 Validating new template...")
                time.sleep(1)

                self.tos_navigator.click_somewhere_else_to_close_dropdown()
                time.sleep(1.5)

                result = self.tos_navigator.find_element_in_upper_left(
                    "account_dropdown_template.png",
                    confidence=0.6,
                    region_width_ratio=capture_width_ratio,
                    region_height_ratio=capture_height_ratio
                )
                if result:
                    self.status_update.emit(f"✅ Template validated successfully! Found with test.")
                else:
                    self.status_update.emit(
                        "⚠️ Template created, but initial validation test failed. It might still work with different confidence. Check 'assets/templates/account_dropdown_template.png'.")

                self.progress_update.emit(100)
                self.finished_setup.emit(True)
            else:
                self.status_update.emit(
                    "❌ Failed to create account dropdown template. Check captured images in 'assets/captures/'. The 'before' and 'after' images should be the same size.")
                self.finished_setup.emit(False)

        except Exception as e:
            self.status_update.emit(f"❌ Critical error during template setup: {e}")
            import traceback
            self.status_update.emit(traceback.format_exc())
            self.finished_setup.emit(False)


class OverlayMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeltaMon - Trading Monitor Overlay")
        self.setGeometry(50, 50, 900, 600)

        # Set always on top and other overlay flags
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'app_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet(OVERLAY_DARK_STYLE_SHEET)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._monitoring_active = False
        self.config_manager = ConfigManager()
        self.window_manager = EnhancedWindowManager(
            main_window_title="Main@thinkorswim [build 1985]",
            exclude_title_substring="DeltaMon"
        )
        self.credential_manager = CredentialManager()
        self.tos_launcher = TosLauncher()
        self.tos_navigator = None
        self.discovered_accounts = []
        self.setup_worker = None
        self.login_worker = None
        self.tos_hwnd = None

        self.scan_stats = {
            'total_scans': 0,
            'successful_scans': 0,
            'average_scan_time': 0,
            'alerts_today': 0
        }

        self._setup_ui_elements()
        self.update_button_states()

        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_statistics_display)
        self.stats_timer.start(5000)

        self.overall_status_label.setText("Status: Ready - Click '🔑 Auto-Login ToS' to begin")
        self.log_monitoring_event("🚀 DeltaMon Overlay ready - Always on top of ToS!")

    def _setup_ui_elements(self):
        control_panel = self.create_control_panel()
        self.main_layout.addWidget(control_panel)

        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel = self.create_accounts_panel()
        content_splitter.addWidget(left_panel)
        right_panel = self.create_statistics_panel()
        content_splitter.addWidget(right_panel)
        content_splitter.setSizes([int(self.width() * 0.65), int(self.width() * 0.35)])
        self.main_layout.addWidget(content_splitter)

    def create_control_panel(self):
        control_frame = QGroupBox("Control Panel")
        control_layout = QVBoxLayout(control_frame)
        main_buttons_layout = QHBoxLayout()

        self.auto_login_button = QPushButton("🔑 Auto-Login")
        self.auto_login_button.setObjectName("successButton")
        self.auto_login_button.clicked.connect(self.start_auto_login_flow)
        main_buttons_layout.addWidget(self.auto_login_button)

        self.edit_credentials_button = QPushButton("✏️ Creds")
        self.edit_credentials_button.setObjectName("editButton")
        self.edit_credentials_button.clicked.connect(self.edit_credentials)
        main_buttons_layout.addWidget(self.edit_credentials_button)
        main_buttons_layout.addSpacing(5)

        self.check_tos_button = QPushButton("🔍 Status")
        self.check_tos_button.setObjectName("warningButton")
        self.check_tos_button.clicked.connect(self.check_tos_status)
        main_buttons_layout.addWidget(self.check_tos_button)
        main_buttons_layout.addSpacing(5)

        self.setup_template_button = QPushButton("🎯 Template")
        self.setup_template_button.setObjectName("setupButton")
        self.setup_template_button.clicked.connect(self.setup_template)
        main_buttons_layout.addWidget(self.setup_template_button)
        main_buttons_layout.addSpacing(5)

        self.discover_button = QPushButton("📋 Read Accounts")
        self.discover_button.clicked.connect(self.discover_accounts)
        main_buttons_layout.addWidget(self.discover_button)
        main_buttons_layout.addSpacing(10)

        self.start_button = QPushButton("🚀 Start Monitor")
        self.start_button.clicked.connect(self.start_monitoring)
        main_buttons_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("⏹️ Stop")
        self.stop_button.setObjectName("criticalButton")
        self.stop_button.clicked.connect(self.stop_monitoring)
        main_buttons_layout.addWidget(self.stop_button)
        main_buttons_layout.addStretch()

        status_layout = QHBoxLayout()
        self.overall_status_label = QLabel("Status: Ready")
        self.overall_status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.overall_status_label)
        status_layout.addStretch()
        self.alert_count_label = QLabel("0")
        self.alert_count_label.setObjectName("alertCountGreen")
        self.alert_count_label.setToolTip("Active alerts today")
        status_layout.addWidget(QLabel("Alerts:"))
        status_layout.addWidget(self.alert_count_label)

        self.setup_progress = QProgressBar()
        self.setup_progress.setVisible(False)
        self.setup_progress.setRange(0, 100)

        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Scan:"))
        self.scan_interval_spinner = QSpinBox()
        self.scan_interval_spinner.setRange(10, 300)
        self.scan_interval_spinner.setValue(60)
        self.scan_interval_spinner.setSuffix("s")
        settings_layout.addWidget(self.scan_interval_spinner)
        settings_layout.addSpacing(10)
        settings_layout.addWidget(QLabel("Fast:"))
        self.fast_mode_checkbox = QCheckBox()
        self.fast_mode_checkbox.setToolTip("Skip some validations for faster scanning")
        settings_layout.addWidget(self.fast_mode_checkbox)
        settings_layout.addStretch()

        control_layout.addLayout(main_buttons_layout)
        control_layout.addLayout(status_layout)
        control_layout.addWidget(self.setup_progress)
        control_layout.addLayout(settings_layout)
        return control_frame

    def create_accounts_panel(self):
        accounts_frame = QGroupBox("Account Monitoring")
        accounts_layout = QVBoxLayout(accounts_frame)
        self.account_count_label = QLabel("No accounts discovered")
        accounts_layout.addWidget(self.account_count_label)
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(5)
        self.accounts_table.setHorizontalHeaderLabels(["Account", "Status", "Delta", "Check", "Alerts"])
        self.accounts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.accounts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.verticalHeader().setVisible(False)
        header = self.accounts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.accounts_table.setColumnWidth(2, 60)
        self.accounts_table.setColumnWidth(3, 60)
        self.accounts_table.setColumnWidth(4, 50)
        self.accounts_table.setMaximumHeight(200)
        accounts_layout.addWidget(self.accounts_table)
        return accounts_frame

    def create_statistics_panel(self):
        stats_frame = QGroupBox("Stats & Logs")
        stats_layout = QVBoxLayout(stats_frame)
        perf_layout = QGridLayout()
        self.total_scans_label = QLabel("0")
        self.success_rate_label = QLabel("0%")
        self.avg_scan_time_label = QLabel("0s")
        self.accounts_online_label = QLabel("0/0")
        perf_layout.addWidget(QLabel("Scans:"), 0, 0)
        perf_layout.addWidget(self.total_scans_label, 0, 1)
        perf_layout.addWidget(QLabel("Success:"), 1, 0)
        perf_layout.addWidget(self.success_rate_label, 1, 1)
        perf_layout.addWidget(QLabel("Avg Time:"), 2, 0)
        perf_layout.addWidget(self.avg_scan_time_label, 2, 1)
        perf_layout.addWidget(QLabel("Online:"), 3, 0)
        perf_layout.addWidget(self.accounts_online_label, 3, 1)
        stats_layout.addLayout(perf_layout)

        self.setup_log = QTextEdit()
        self.setup_log.setMaximumHeight(120)
        self.setup_log.setVisible(False)
        self.setup_log.setPlaceholderText("Setup log will appear here...")
        self.setup_log_label = QLabel("Setup Log:")
        self.setup_log_label.setVisible(False)
        stats_layout.addWidget(self.setup_log_label)
        stats_layout.addWidget(self.setup_log)

        self.monitoring_log = QTextEdit()
        self.monitoring_log.setMaximumHeight(120)
        self.monitoring_log.setPlaceholderText("Monitoring events will appear here...")
        stats_layout.addWidget(QLabel("Monitor Log:"))
        stats_layout.addWidget(self.monitoring_log)
        return stats_frame

    # NO MORE POPUP DIALOGS! Everything goes to logs instead
    def show_status_message(self, title: str, message: str, is_error: bool = False):
        """Replace popup dialogs with log messages"""
        emoji = "❌" if is_error else "ℹ️"
        log_message = f"{emoji} {title}: {message}"
        self.log_monitoring_event(log_message)

        # Also update status label for important messages
        if is_error:
            self.overall_status_label.setText(f"Status: ❌ {title}")
        else:
            self.overall_status_label.setText(f"Status: ✅ {title}")

    @Slot()
    def edit_credentials(self):
        self.log_monitoring_event("✏️ Opening credential editor...")
        login_dialog = LoginDialog(self)
        login_dialog.login_successful.connect(self.on_credentials_saved_or_updated)
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            self.log_monitoring_event("✅ Credential dialog accepted. Credentials may have been updated.")
        else:
            self.log_monitoring_event("❌ Credential editing cancelled.")

    @Slot(str, str, str)
    def on_credentials_saved_or_updated(self, username, password, executable_path):
        self.log_monitoring_event(f"🔑 Credentials processed for user: {username}.")
        if executable_path:
            self.log_monitoring_event(f"🛠️ ToS Executable Path: {executable_path}")
        else:
            self.log_monitoring_event("⚠️ ToS Executable Path not set.")
        self.show_status_message("Credentials Saved", "Ready for Auto-Login")

    @Slot()
    def start_auto_login_flow(self):
        self.log_monitoring_event("🔑 Initiating Auto-Login ToS flow...")
        username, password, executable_path = self.credential_manager.get_credentials()
        if not username or not password or not executable_path or not os.path.exists(executable_path):
            self.log_monitoring_event("⚠️ Missing credentials or valid executable path. Opening setup dialog...")
            login_dialog = LoginDialog(self)
            login_dialog.login_successful.connect(self.on_credentials_saved_for_auto_login)
            if login_dialog.exec() != QDialog.DialogCode.Accepted:
                self.log_monitoring_event("❌ Credential setup for auto-login cancelled.")
                self.overall_status_label.setText("Status: Auto-Login cancelled.")
                return
        else:
            self.log_monitoring_event(f"✅ Found saved credentials and exec path. Proceeding to login.")
            self._execute_auto_login(username, password, executable_path)

    @Slot(str, str, str)
    def on_credentials_saved_for_auto_login(self, username, password, executable_path):
        self.log_monitoring_event("✅ Credentials saved/confirmed. Proceeding with auto-login.")
        if not executable_path or not os.path.exists(executable_path):
            self.log_monitoring_event(f"❌ Invalid or missing executable path after dialog: {executable_path}")
            self.show_status_message("Auto-Login Error", "Executable path missing", True)
            return
        self._execute_auto_login(username, password, executable_path)

    def _execute_auto_login(self, username: str, password: str, executable_path: str):
        if not executable_path or not os.path.exists(executable_path):
            self.log_monitoring_event(f"❌ Cannot execute auto-login: Invalid ToS executable path: {executable_path}")
            self.show_status_message("Auto-Login Error", "Invalid executable path", True)
            return

        self.log_monitoring_event(f"🚀 Starting AutoLoginWorker with exec: {os.path.basename(executable_path)}")
        self.update_button_states(login_active=True)
        self.setup_progress.setVisible(True)
        self.setup_progress.setValue(0)
        self.setup_log_label.setVisible(True)
        self.setup_log.setVisible(True)
        self.setup_log.clear()
        self.login_worker = AutoLoginWorker(username, password, executable_path,
                                            self.tos_launcher, self.window_manager)
        self.login_worker.status_update.connect(self.on_login_status_update)
        self.login_worker.progress_update.connect(self.on_login_progress_update)
        self.login_worker.login_complete.connect(self.on_login_complete)
        self.login_worker.start()

    @Slot()
    def check_tos_status(self):
        self.log_monitoring_event("🔍 Checking Thinkorswim status...")
        self.overall_status_label.setText("Status: Checking ToS...")
        QApplication.processEvents()
        status_report = self.window_manager.get_tos_status_report()

        if status_report['main_trading_available']:
            self.show_status_message("ToS Status", "Ready for monitoring!")
            self.tos_hwnd = self.window_manager.hwnd
            tos_is_ready = True
        elif status_report['login_required']:
            self.show_status_message("ToS Status", "Login required - use Auto-Login", True)
            tos_is_ready = False
        elif status_report['launcher_open']:
            self.show_status_message("ToS Status", "Launcher detected - use Auto-Login", True)
            tos_is_ready = False
        elif status_report['other_tos_windows'] > 0:
            self.show_status_message("ToS Status", "Main window not detected", True)
            tos_is_ready = False
        else:
            self.show_status_message("ToS Status", "ToS not running - use Auto-Login", True)
            tos_is_ready = False

        self.log_monitoring_event(f"📊 ToS Status: {status_report['recommended_action']}")
        self.update_button_states(tos_ready=tos_is_ready)

    @Slot()
    def setup_template(self):
        self.log_monitoring_event("🎯 Initiating template setup...")
        self.overall_status_label.setText("Status: Template Setup...")
        QApplication.processEvents()

        if not self.tos_hwnd:
            self.log_monitoring_event("⚠️ ToS HWND not confirmed. Running 'Check Status' first...")
            self.check_tos_status()
            if not self.tos_hwnd:
                self.show_status_message("Setup Failed", "ToS Not Ready", True)
                return
            self.log_monitoring_event(f"✅ ToS HWND confirmed: {self.tos_hwnd}. Proceeding with template setup.")

        if not self.tos_navigator:
            self.tos_navigator = TosNavigator(self.tos_hwnd)
            self.log_monitoring_event("🛠️ TosNavigator initialized.")

        if not self.window_manager.focus_tos_window():
            self.log_monitoring_event("⚠️ Could not focus ToS window. Template setup might be unreliable.")

        self.setup_progress.setVisible(True)
        self.setup_log_label.setVisible(True)
        self.setup_log.setVisible(True)
        self.setup_log.clear()
        self.update_button_states(setting_up_template=True)

        try:
            self.setup_worker = ScaledTemplateSetupWorker(self.tos_navigator)
            self.setup_worker.status_update.connect(self.on_setup_status_update)
            self.setup_worker.progress_update.connect(self.on_setup_progress_update)
            self.setup_worker.finished_setup.connect(self.on_setup_finished)
            self.setup_worker.start()
        except ValueError as ve:
            self.log_monitoring_event(f"❌ ERROR starting template setup worker: {ve}")
            self.show_status_message("Setup Error", str(ve), True)
            self.update_button_states(tos_ready=bool(self.tos_hwnd))

    @Slot()
    def discover_accounts(self):
        self.log_monitoring_event("🔍 Starting dropdown-based discovery for all accounts...")
        self.overall_status_label.setText("Status: Discovering Accounts...")
        QApplication.processEvents()

        if not self.tos_hwnd:
            self.log_monitoring_event("⚠️ ToS HWND not confirmed for discovery. Running 'Check Status' first...")
            self.check_tos_status()
            if not self.tos_hwnd:
                self.show_status_message("Discovery Failed", "ToS Not Ready", True)
                return

        if not self.tos_navigator:
            self.tos_navigator = TosNavigator(self.tos_hwnd)
            self.log_monitoring_event("🛠️ TosNavigator initialized for account discovery.")

        if not self.window_manager.focus_tos_window():
            self.log_monitoring_event("⚠️ Could not focus ToS window for account discovery. Proceeding with caution.")

        self.accounts_table.setRowCount(0)
        self.discovered_accounts = []
        self.update_button_states(discovering_accounts=True)
        self.overall_status_label.setText("Status: 🔍 Reading accounts...")
        QApplication.processEvents()

        try:
            from core.enhanced_dropdown_reader import DropdownAccountDiscovery
            dropdown_discovery = DropdownAccountDiscovery(self.tos_navigator)

            def status_update_for_discovery(message):
                self.overall_status_label.setText(f"Discovery: {message}")
                self.log_monitoring_event(f"[Discovery] {message}")
                QApplication.processEvents()

            discovered_account_names = dropdown_discovery.discover_all_accounts(
                status_callback=status_update_for_discovery)

            if discovered_account_names:
                for account_name in discovered_account_names:
                    self.add_account_to_table(account_name, "Ready", "N/A", "Never", "0")
                    self.discovered_accounts.append(account_name)
                total_found = len(discovered_account_names)
                self.account_count_label.setText(f"📊 {total_found} accounts discovered")
                self.show_status_message("Discovery Success", f"Found {total_found} accounts")
                self.log_monitoring_event(f"✅ Dropdown discovery successful! Found {total_found} accounts.")
            else:
                self.account_count_label.setText("❌ No accounts discovered")
                self.show_status_message("Discovery Failed", "No accounts found", True)
                self.log_monitoring_event(
                    "❌ Dropdown-based discovery failed. Check debug images in assets/captures/dropdown.")
        except Exception as e:
            error_msg = f"❌ Discovery error: {e}"
            self.account_count_label.setText("❌ Discovery error")
            self.show_status_message("Discovery Error", str(e), True)
            self.log_monitoring_event(error_msg)
        finally:
            self.update_button_states(tos_ready=bool(self.tos_hwnd))

    def add_account_to_table(self, account_name: str, status: str, delta: str, last_check: str, alerts: str):
        row_position = self.accounts_table.rowCount()
        self.accounts_table.insertRow(row_position)
        self.accounts_table.setItem(row_position, 0, QTableWidgetItem(account_name))
        self.accounts_table.setItem(row_position, 1, QTableWidgetItem(status))
        self.accounts_table.setItem(row_position, 2, QTableWidgetItem(delta))
        self.accounts_table.setItem(row_position, 3, QTableWidgetItem(last_check))
        self.accounts_table.setItem(row_position, 4, QTableWidgetItem(alerts))

    def log_monitoring_event(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.monitoring_log.append(formatted_message)
        scrollbar = self.monitoring_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_statistics_display(self):
        self.total_scans_label.setText(str(self.scan_stats['total_scans']))
        if self.scan_stats['total_scans'] > 0 and self.scan_stats['successful_scans'] > 0:
            success_rate = (self.scan_stats['successful_scans'] / self.scan_stats['total_scans']) * 100
            self.success_rate_label.setText(f"{success_rate:.1f}%")
        else:
            self.success_rate_label.setText("0.0%")
        self.avg_scan_time_label.setText(f"{self.scan_stats['average_scan_time']:.1f}s")
        online_accounts = 0
        total_accounts = len(self.discovered_accounts)
        self.accounts_online_label.setText(f"{online_accounts}/{total_accounts}")
        self.alert_count_label.setText(str(self.scan_stats['alerts_today']))
        self.alert_count_label.setObjectName(
            "alertCountGreen" if self.scan_stats['alerts_today'] == 0 else "alertCount")
        self.alert_count_label.setStyleSheet(self.styleSheet())

    @Slot()
    def start_monitoring(self):
        account_count = len(self.discovered_accounts)
        if account_count == 0:
            self.show_status_message("Start Failed", "No accounts discovered", True)
            return

        self._monitoring_active = True
        self.update_button_states(monitoring_active=True)
        scan_interval = self.scan_interval_spinner.value()
        fast_mode = self.fast_mode_checkbox.isChecked()
        self.overall_status_label.setText(f"Status: 🚀 Monitoring {account_count} accounts")
        mode_text = "Fast Mode" if fast_mode else "Standard Mode"
        self.log_monitoring_event(f"🚀 Started monitoring {account_count} accounts - {mode_text}")
        self.log_monitoring_event(f"⚙️ Scan interval: {scan_interval}s")

    @Slot()
    def stop_monitoring(self):
        self._monitoring_active = False
        self.update_button_states(monitoring_active=False)
        self.overall_status_label.setText("Status: ⏹️ Monitoring stopped")
        self.log_monitoring_event("⏹️ Monitoring stopped")

    def update_button_states(self, monitoring_active=None, tos_ready=None, setting_up_template=False,
                             discovering_accounts=False, login_active=False):
        if monitoring_active is None:
            self._monitoring_active = self._monitoring_active
        else:
            self._monitoring_active = monitoring_active

        if tos_ready is None: tos_ready = bool(self.tos_hwnd)

        login_worker_active = self.login_worker and self.login_worker.isRunning() if not login_active else login_active
        setup_worker_active = self.setup_worker and self.setup_worker.isRunning()

        self.auto_login_button.setEnabled(
            not self._monitoring_active and not login_worker_active and not setup_worker_active)
        self.edit_credentials_button.setEnabled(
            not self._monitoring_active and not login_worker_active and not setup_worker_active)
        self.check_tos_button.setEnabled(
            not self._monitoring_active and not login_worker_active and not setup_worker_active)
        self.setup_template_button.setEnabled(
            not self._monitoring_active and tos_ready and not login_worker_active and not setup_worker_active and not discovering_accounts)
        self.discover_button.setEnabled(
            not self._monitoring_active and tos_ready and not login_worker_active and not setup_worker_active and not setting_up_template)
        can_start_monitoring = bool(self.discovered_accounts) and tos_ready
        self.start_button.setEnabled(
            not self._monitoring_active and can_start_monitoring and not login_worker_active and not setup_worker_active and not setting_up_template and not discovering_accounts)
        self.stop_button.setEnabled(self._monitoring_active)

    @Slot(str)
    def on_login_status_update(self, message):
        self.overall_status_label.setText(f"Auto-Login: {message}")
        self.setup_log.append(f"[Login] {message}")
        scrollbar = self.setup_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        QApplication.processEvents()

    @Slot(int)
    def on_login_progress_update(self, value):
        self.setup_progress.setValue(value)
        QApplication.processEvents()

    @Slot(bool)
    def on_login_complete(self, success):
        QTimer.singleShot(2000, lambda: self.setup_progress.setVisible(False))
        if success:
            self.show_status_message("Auto-Login Complete", "ToS ready for monitoring!")
            self.log_monitoring_event("✅ Auto-login successful - ToS ready for monitoring!")
            self.tos_hwnd = self.window_manager.hwnd
        else:
            self.show_status_message("Auto-Login Failed", "Check logs for details", True)
            self.log_monitoring_event("❌ Auto-login failed - check credentials or ToS state.")
        self.update_button_states(tos_ready=success, login_active=False)

    @Slot(str)
    def on_setup_status_update(self, message):
        self.overall_status_label.setText(f"Template Setup: {message}")
        self.setup_log.append(f"[Setup] {message}")
        scrollbar = self.setup_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        QApplication.processEvents()

    @Slot(int)
    def on_setup_progress_update(self, value):
        self.setup_progress.setValue(value)
        QApplication.processEvents()

    @Slot(bool)
    def on_setup_finished(self, success):
        QTimer.singleShot(2000, lambda: self.setup_progress.setVisible(False))
        if success:
            self.show_status_message("Template Setup Complete", "Ready for account discovery!")
            self.log_monitoring_event("✅ Template setup completed - Ready for account discovery!")
        else:
            self.show_status_message("Template Setup Failed", "Check logs for details", True)
            self.log_monitoring_event("❌ Template setup failed. Review logs for details.")
        self.update_button_states(tos_ready=bool(self.tos_hwnd), setting_up_template=False)