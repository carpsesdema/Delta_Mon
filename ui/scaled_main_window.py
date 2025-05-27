# Delta_Mon/ui/scaled_main_window.py

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QAbstractItemView,
    QHeaderView, QLabel, QTableWidgetItem, QMessageBox, QApplication,
    QProgressBar, QTextEdit, QSplitter, QGroupBox, QGridLayout,
    QSpinBox, QCheckBox, QScrollArea, QFrame, QDialog
)
from PySide6.QtCore import Qt, Slot, QTimer, QThread, Signal
from PySide6.QtGui import QFont

import time
import os
from datetime import datetime

from utils.config_manager import ConfigManager
from core.enhanced_window_manager import EnhancedWindowManager
from core.tos_navigator import TosNavigator
from utils.credential_manager import CredentialManager
from utils.tos_launcher import TosLauncher
from ui.login_dialog import LoginDialog

# Enhanced Dark Theme for larger scale (style sheet remains the same)
SCALED_DARK_STYLE_SHEET = """
    QWidget {
        background-color: #2b2b2b;
        color: #ffffff;
        font-size: 9pt;
    }
    QMainWindow {
        background-color: #2b2b2b;
    }
    QPushButton {
        background-color: #4a4a4a;
        color: #ffffff;
        border: 1px solid #5a5a5a;
        padding: 6px;
        min-height: 18px;
        border-radius: 4px;
        font-size: 9pt;
    }
    QPushButton:hover {
        background-color: #5a5a5a;
    }
    QPushButton:pressed {
        background-color: #6a6a6a;
    }
    QPushButton:disabled {
        background-color: #3a3a3a;
        color: #888888;
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
        background-color: #3c3c3c;
        color: #ffffff;
        gridline-color: #5a5a5a;
        border: 1px solid #5a5a5a;
        border-radius: 4px;
        alternate-background-color: #3a3a3a;
    }
    QHeaderView::section {
        background-color: #4a4a4a;
        color: #ffffff;
        padding: 3px;
        border: 1px solid #5a5a5a;
        font-weight: bold;
        font-size: 9pt;
    }
    QTableWidget::item {
        padding: 3px;
        font-size: 8pt;
    }
    QTableWidget::item:selected {
        background-color: #5a6370;
        color: #ffffff;
    }
    QLabel#statusLabel {
        font-weight: bold;
        padding: 4px;
        color: #cccccc;
        border: 1px solid #4a4a4a;
        border-radius: 3px;
        background-color: #333333;
    }
    QLabel#alertCount {
        background-color: #e74c3c;
        color: white;
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 10px;
        font-size: 10pt;
    }
    QLabel#alertCountGreen {
        background-color: #27ae60;
        color: white;
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 10px;
        font-size: 10pt;
    }
    QGroupBox {
        font-weight: bold;
        border: 2px solid #5a5a5a;
        border-radius: 5px;
        margin: 5px 0px;
        padding-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
    }
    QProgressBar {
        background-color: #3c3c3c;
        border: 1px solid #5a5a5a;
        border-radius: 4px;
        text-align: center;
        font-size: 8pt;
    }
    QProgressBar::chunk {
        background-color: #2ecc71;
        border-radius: 3px;
    }
    QSpinBox {
        background-color: #4a4a4a;
        border: 1px solid #5a5a5a;
        border-radius: 3px;
        padding: 2px;
        font-size: 9pt;
    }
"""


class AutoLoginWorker(QThread):
    """Worker thread for automatic ToS login process."""

    status_update = Signal(str)
    progress_update = Signal(int)
    login_complete = Signal(bool)  # True if main window detected, False otherwise

    def __init__(self, username, password, executable_path, tos_launcher, window_manager):
        super().__init__()
        self.username = username
        self.password = password
        self.executable_path = executable_path  # Added
        self.tos_launcher = tos_launcher
        self.window_manager = window_manager

    def run(self):
        """Execute the automatic login process."""
        try:
            self.status_update.emit("🚀 Starting automatic ToS login...")
            self.progress_update.emit(10)

            # Check current ToS status
            self.status_update.emit("🔍 Checking current ToS status...")
            status_report = self.window_manager.get_tos_status_report()
            self.progress_update.emit(15)

            if status_report['main_trading_available']:
                self.status_update.emit("✅ Main trading window already available! Login successful.")
                self.progress_update.emit(100)
                self.login_complete.emit(True)
                return

            # If no ToS windows at all, or only launcher, launch ToS
            # The self.executable_path should be valid if we reach here from LoginDialog
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
                # Wait for launcher/login window to appear, TosLauncher.launch_tos already has a wait.
                self.progress_update.emit(40)

            # If login is required (login window is up)
            elif not status_report['login_required']:
                # This case means some ToS windows are open, but not the login or main one.
                # It's an ambiguous state. We might need to close existing ToS instances or guide user.
                # For now, assume we proceed to login attempt, it might focus an existing login window.
                self.status_update.emit("ℹ️ ToS state ambiguous, attempting login anyway...")

            self.status_update.emit("⏳ Waiting for ToS login screen to be ready...")
            # TosLauncher's login_to_tos has its own wait for login window.
            # No need for an explicit wait loop here if login_to_tos is robust.
            self.progress_update.emit(50)

            # Attempt login
            self.status_update.emit("🔑 Attempting automatic login with credentials...")
            # login_to_tos will wait for the login window itself.
            login_sequence_initiated = self.tos_launcher.login_to_tos(self.username, self.password)
            self.progress_update.emit(70)

            if not login_sequence_initiated:
                self.status_update.emit("❌ Automatic login input sequence failed or login window not found.")
                self.login_complete.emit(False)
                return

            self.status_update.emit("✅ Login credentials submitted.")
            self.progress_update.emit(85)

            # Wait for main trading window to appear
            self.status_update.emit("⏳ Waiting for main trading window to appear post-login...")
            main_window_hwnd = self.window_manager.wait_for_main_trading_window(timeout_seconds=60)  # Increased timeout

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
    """Enhanced setup worker for multi-account monitoring."""

    status_update = Signal(str)
    progress_update = Signal(int)
    finished_setup = Signal(bool)

    def __init__(self, tos_navigator):
        super().__init__()
        self.tos_navigator = tos_navigator

    def run(self):
        """Run the template setup process with enhanced validation."""
        try:
            self.status_update.emit("🚀 Starting multi-account template setup...")
            self.progress_update.emit(5)

            # Enhanced setup process for multiple account monitoring
            self.status_update.emit("📊 Optimizing for multi-account monitoring...")
            self.progress_update.emit(10)

            # Step 1: Multiple reference captures for robustness
            self.status_update.emit("📸 Capturing multiple reference states...")
            for i in range(3):
                ref_path = self.tos_navigator.capture_upper_left_region(f"reference_{i + 1}.png")
                if ref_path:
                    self.status_update.emit(f"✅ Reference {i + 1}/3 captured")
                time.sleep(0.5)
            self.progress_update.emit(25)

            # Step 2: Enhanced auto-capture with validation
            self.status_update.emit("🎯 Starting enhanced auto-capture process...")
            self.progress_update.emit(35)

            # Longer delay for user to prepare for multi-account workflow
            self.status_update.emit("👆 Get ready to click the account dropdown...")
            self.status_update.emit("📋 TIP: Ensure dropdown shows ALL your accounts!")
            time.sleep(3)

            self.progress_update.emit(45)

            # Capture before state
            before_path = self.tos_navigator.capture_upper_left_region("before_dropdown_multi.png")
            if not before_path:
                self.status_update.emit("❌ Failed to capture before state")
                self.finished_setup.emit(False)
                return

            # Extended countdown for user preparation
            self.status_update.emit("👆 CLICK DROPDOWN NOW! (10 seconds...)")
            for i in range(10, 0, -1):
                self.status_update.emit(f"👆 Click account dropdown! ({i}s) - Make sure ALL accounts are visible!")
                time.sleep(1)
                # Corrected progress calculation:
                # We want to go from 45 to approx 75-80 during these 10 seconds.
                # So, a range of 30-35 points over 10 steps.
                self.progress_update.emit(int(45 + (10 - i) * 3.0))


            # Capture after state
            self.status_update.emit("📸 Capturing expanded dropdown state...")
            after_path = self.tos_navigator.capture_upper_left_region("after_dropdown_multi.png",
                                                                      width_ratio=0.5,
                                                                      height_ratio=0.6)  # Larger capture for many accounts
            if not after_path:
                self.status_update.emit("❌ Failed to capture after state")
                self.finished_setup.emit(False)
                return

            self.progress_update.emit(85)

            # Create and validate template
            self.status_update.emit("🔍 Creating multi-account template...")
            template_created = self.tos_navigator._create_template_from_difference(before_path, after_path)

            if template_created:
                self.progress_update.emit(95)

                # Enhanced testing for multi-account scale
                self.status_update.emit("🧪 Running multi-account validation...")
                time.sleep(2)

                # Test template at different confidence levels
                test_results = []
                for confidence in [0.8, 0.7, 0.6, 0.5]:
                    result = self.tos_navigator.find_element_in_upper_left("account_dropdown_template.png",
                                                                           confidence=confidence)
                    test_results.append((confidence, result is not None))

                # Report test results
                working_confidences = [conf for conf, works in test_results if works]
                if working_confidences:
                    best_conf = max(working_confidences)
                    self.status_update.emit(f"✅ Template validated! Best confidence: {best_conf}")
                    self.status_update.emit("🏢 Ready for multi-account monitoring!")
                else:
                    self.status_update.emit("⚠️ Template created but validation inconclusive")

                self.progress_update.emit(100)
                self.finished_setup.emit(True)
            else:
                self.status_update.emit("❌ Failed to create multi-account template")
                self.finished_setup.emit(False)

        except Exception as e:
            self.status_update.emit(f"❌ Setup error: {e}")
            self.finished_setup.emit(False)


class ScaledMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeltaMon - Multi-Account Monitor")
        self.setGeometry(50, 50, 1200, 800)  # Larger window for more data

        self.setStyleSheet(SCALED_DARK_STYLE_SHEET)

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # State variables
        self._monitoring_active = False
        self.config_manager = ConfigManager()
        self.window_manager = EnhancedWindowManager(
            main_window_title="Main@thinkorswim [build 1985]",  # Ensure this is exact
            exclude_title_substring="DeltaMon"
        )
        self.credential_manager = CredentialManager()
        self.tos_launcher = TosLauncher()
        self.tos_navigator = None  # Initialized after ToS window is confirmed
        self.discovered_accounts = []
        self.setup_worker = None
        self.login_worker = None
        self.tos_hwnd = None  # Store HWND once found

        # Performance tracking
        self.scan_stats = {
            'total_scans': 0,
            'successful_scans': 0,
            'average_scan_time': 0,
            'alerts_today': 0
        }

        self._setup_ui_elements() # Corrected call
        self.update_button_states()

        # Auto-refresh timer for stats
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_statistics_display)
        self.stats_timer.start(5000)  # Update every 5 seconds

        self.overall_status_label.setText("Status: Ready - Click '🔑 Auto-Login ToS' or '✏️ Edit Credentials' to begin")
        self.log_monitoring_event("🚀 DeltaMon ready - Awaiting user action for ToS setup.")

    def _setup_ui_elements(self): # Renamed to indicate it's an internal setup method
        # === TOP CONTROL PANEL ===
        control_panel = self.create_control_panel()
        self.main_layout.addWidget(control_panel)

        # === MAIN CONTENT AREA ===
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Accounts and monitoring
        left_panel = self.create_accounts_panel()
        content_splitter.addWidget(left_panel)

        # Right side: Statistics and logs
        right_panel = self.create_statistics_panel()
        content_splitter.addWidget(right_panel)

        # Set splitter ratios (70% accounts, 30% stats)
        content_splitter.setSizes([int(self.width() * 0.65), int(self.width() * 0.35)]) # Adjusted for better balance

        self.main_layout.addWidget(content_splitter)


    def create_control_panel(self):
        """Create the main control panel."""
        control_frame = QGroupBox("Control Panel")
        control_layout = QVBoxLayout(control_frame)

        # Top row - main buttons
        main_buttons_layout = QHBoxLayout()

        # Auto-Login button
        self.auto_login_button = QPushButton("🔑 Auto-Login ToS")
        self.auto_login_button.setObjectName("successButton")
        self.auto_login_button.clicked.connect(self.start_auto_login_flow)  # Renamed slot
        main_buttons_layout.addWidget(self.auto_login_button)

        # NEW: Edit Credentials button
        self.edit_credentials_button = QPushButton("✏️ Edit Credentials")
        self.edit_credentials_button.setObjectName("editButton")
        self.edit_credentials_button.clicked.connect(self.edit_credentials)
        main_buttons_layout.addWidget(self.edit_credentials_button)

        main_buttons_layout.addSpacing(10)

        # Check ToS Status button
        self.check_tos_button = QPushButton("🔍 Check Status")
        self.check_tos_button.setObjectName("warningButton")
        self.check_tos_button.clicked.connect(self.check_tos_status)
        main_buttons_layout.addWidget(self.check_tos_button)

        main_buttons_layout.addSpacing(10)

        self.setup_template_button = QPushButton("🎯 Setup Template")
        self.setup_template_button.setObjectName("setupButton")
        self.setup_template_button.clicked.connect(self.setup_template)
        main_buttons_layout.addWidget(self.setup_template_button)

        main_buttons_layout.addSpacing(10)

        self.discover_button = QPushButton("📋 Read Accounts")
        self.discover_button.clicked.connect(self.discover_accounts)
        main_buttons_layout.addWidget(self.discover_button)

        main_buttons_layout.addSpacing(20)

        self.start_button = QPushButton("🚀 Start Monitoring")
        self.start_button.clicked.connect(self.start_monitoring)
        main_buttons_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("⏹️ Stop Monitoring")
        self.stop_button.setObjectName("criticalButton")
        self.stop_button.clicked.connect(self.stop_monitoring)
        main_buttons_layout.addWidget(self.stop_button)

        main_buttons_layout.addStretch()

        # Status and alerts
        status_layout = QHBoxLayout()
        self.overall_status_label = QLabel("Status: Ready for Auto-Login")
        self.overall_status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.overall_status_label)

        status_layout.addStretch()

        self.alert_count_label = QLabel("0")
        self.alert_count_label.setObjectName("alertCountGreen")
        self.alert_count_label.setToolTip("Active alerts today")
        status_layout.addWidget(QLabel("Alerts:"))
        status_layout.addWidget(self.alert_count_label)

        # Progress bar
        self.setup_progress = QProgressBar()
        self.setup_progress.setVisible(False)
        self.setup_progress.setRange(0, 100)

        # Settings row
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Scan Interval:"))

        self.scan_interval_spinner = QSpinBox()
        self.scan_interval_spinner.setRange(10, 300)
        self.scan_interval_spinner.setValue(60)
        self.scan_interval_spinner.setSuffix(" seconds")
        settings_layout.addWidget(self.scan_interval_spinner)

        settings_layout.addSpacing(20)
        settings_layout.addWidget(QLabel("Fast Mode:"))

        self.fast_mode_checkbox = QCheckBox("Enable")
        self.fast_mode_checkbox.setToolTip("Skip some validations for faster scanning")
        settings_layout.addWidget(self.fast_mode_checkbox)

        settings_layout.addStretch()

        # Assembly
        control_layout.addLayout(main_buttons_layout)
        control_layout.addLayout(status_layout)
        control_layout.addWidget(self.setup_progress)
        control_layout.addLayout(settings_layout)

        return control_frame

    def create_accounts_panel(self):
        """Create the accounts monitoring panel."""
        accounts_frame = QGroupBox("Account Monitoring")
        accounts_layout = QVBoxLayout(accounts_frame)

        # Dynamic account count label
        self.account_count_label = QLabel("No accounts discovered")
        accounts_layout.addWidget(self.account_count_label)

        # Accounts table with optimized columns
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(5)
        self.accounts_table.setHorizontalHeaderLabels([
            "Account", "Status", "Last Delta", "Last Check", "Alerts"
        ])

        # Configure table for performance with many rows
        self.accounts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.accounts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.accounts_table.setAlternatingRowColors(True)  # Zebra stripes
        self.accounts_table.verticalHeader().setVisible(False)

        # Column sizing for dynamic account count
        header = self.accounts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Account name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Delta
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Last check
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Alerts

        self.accounts_table.setColumnWidth(2, 80)  # Delta column
        self.accounts_table.setColumnWidth(3, 80)  # Time column
        self.accounts_table.setColumnWidth(4, 60)  # Alerts column

        # Optimize table for many rows
        self.accounts_table.setRowHeight(0, 20)  # Compact rows

        accounts_layout.addWidget(self.accounts_table)

        return accounts_frame

    def create_statistics_panel(self):
        """Create the statistics and monitoring panel."""
        stats_frame = QGroupBox("Statistics & Logs")
        stats_layout = QVBoxLayout(stats_frame)

        # Performance stats
        perf_layout = QGridLayout()

        self.total_scans_label = QLabel("0")
        self.success_rate_label = QLabel("0%")
        self.avg_scan_time_label = QLabel("0s")
        self.accounts_online_label = QLabel("0/0")

        perf_layout.addWidget(QLabel("Total Scans:"), 0, 0)
        perf_layout.addWidget(self.total_scans_label, 0, 1)
        perf_layout.addWidget(QLabel("Success Rate:"), 1, 0)
        perf_layout.addWidget(self.success_rate_label, 1, 1)
        perf_layout.addWidget(QLabel("Avg Scan Time:"), 2, 0)
        perf_layout.addWidget(self.avg_scan_time_label, 2, 1)
        perf_layout.addWidget(QLabel("Accounts Online:"), 3, 0)
        perf_layout.addWidget(self.accounts_online_label, 3, 1)

        stats_layout.addLayout(perf_layout)

        # Setup log
        self.setup_log = QTextEdit()
        self.setup_log.setMaximumHeight(200)
        self.setup_log.setVisible(False)  # Initially hidden
        self.setup_log.setPlaceholderText("Setup log will appear here...")
        self.setup_log_label = QLabel("Setup Log:")  # Label for the log
        self.setup_log_label.setVisible(False)  # Initially hidden

        stats_layout.addWidget(self.setup_log_label)
        stats_layout.addWidget(self.setup_log)

        # Monitoring log
        self.monitoring_log = QTextEdit()
        self.monitoring_log.setMaximumHeight(150)
        self.monitoring_log.setPlaceholderText("Monitoring events will appear here...")
        stats_layout.addWidget(QLabel("Monitoring Log:"))
        stats_layout.addWidget(self.monitoring_log)

        return stats_frame

    @Slot()
    def edit_credentials(self):
        """Open the LoginDialog to edit credentials."""
        self.log_monitoring_event("✏️ Opening credential editor...")

        login_dialog = LoginDialog(self)
        # login_dialog.load_saved_credentials() is called in its __init__

        # Connect the signal for when credentials are saved/updated
        # The signal now includes executable_path
        login_dialog.login_successful.connect(self.on_credentials_saved_or_updated)

        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            # This block will run if accept_login was called in LoginDialog
            # The actual saving and signal emission is handled by LoginDialog's accept_login
            self.log_monitoring_event("✅ Credential dialog accepted. Credentials may have been updated.")
        else:
            self.log_monitoring_event("❌ Credential editing cancelled.")

    @Slot(str, str, str)  # username, password, executable_path
    def on_credentials_saved_or_updated(self, username, password, executable_path):
        """
        Called when LoginDialog emits login_successful (meaning save & continue).
        This slot now receives the executable_path as well.
        """
        self.log_monitoring_event(f"🔑 Credentials processed for user: {username}.")
        if executable_path:
            self.log_monitoring_event(f"🛠️ ToS Executable Path: {executable_path}")
        else:
            self.log_monitoring_event("⚠️ ToS Executable Path not set.")

        # Optionally, can trigger auto-login flow here if desired after saving
        # For now, user clicks "Auto-Login ToS" button explicitly after this.
        QMessageBox.information(self, "Credentials Processed",
                                "Credentials (and executable path if provided) have been processed.\n"
                                "Click '🔑 Auto-Login ToS' to attempt login with these settings.")

    @Slot()
    def start_auto_login_flow(self):
        """Manages the process of auto-login, prompting for creds if necessary."""
        self.log_monitoring_event("🔑 Initiating Auto-Login ToS flow...")

        username, password, executable_path = self.credential_manager.get_credentials()

        if not username or not password or not executable_path or not os.path.exists(executable_path):
            self.log_monitoring_event("⚠️ Missing credentials or valid executable path. Opening setup dialog...")
            QMessageBox.information(self, "Setup Required",
                                    "ToS credentials or a valid executable path are missing or not yet configured.\n"
                                    "Please complete the setup in the dialog.")

            login_dialog = LoginDialog(self)
            # login_dialog.load_saved_credentials() # Called in __init__
            login_dialog.login_successful.connect(self.on_credentials_saved_for_auto_login)

            if login_dialog.exec() != QDialog.DialogCode.Accepted:
                self.log_monitoring_event("❌ Credential setup for auto-login cancelled.")
                self.overall_status_label.setText("Status: Auto-Login cancelled.")
                return
            # If accepted, on_credentials_saved_for_auto_login will be called, which then calls _execute_auto_login
        else:
            self.log_monitoring_event(
                f"✅ Found saved credentials and exec path: {executable_path}. Proceeding to login.")
            self._execute_auto_login(username, password, executable_path)

    @Slot(str, str, str)  # username, password, executable_path
    def on_credentials_saved_for_auto_login(self, username, password, executable_path):
        """
        Slot connected from LoginDialog when credentials are saved specifically before an auto-login attempt.
        """
        self.log_monitoring_event("✅ Credentials saved/confirmed. Proceeding with auto-login.")
        if not executable_path or not os.path.exists(executable_path):
            self.log_monitoring_event(f"❌ Invalid or missing executable path after dialog: {executable_path}")
            QMessageBox.critical(self, "Auto-Login Error",
                                 "A valid ToS executable path is required to proceed with auto-login.")
            self.overall_status_label.setText("Status: ❌ Executable path missing.")
            return
        self._execute_auto_login(username, password, executable_path)

    def _execute_auto_login(self, username: str, password: str, executable_path: str):
        """Execute the actual auto-login process in a worker thread."""
        if not executable_path or not os.path.exists(executable_path):
            self.log_monitoring_event(f"❌ Cannot execute auto-login: Invalid ToS executable path: {executable_path}")
            QMessageBox.critical(self, "Auto-Login Error",
                                 f"The ToS executable path is invalid or missing:\n{executable_path}\nPlease correct it via '✏️ Edit Credentials'.")
            self.overall_status_label.setText("Status: ❌ Invalid Executable Path.")
            return

        self.log_monitoring_event(f"🚀 Starting AutoLoginWorker with exec: {os.path.basename(executable_path)}")
        self.auto_login_button.setEnabled(False)
        self.edit_credentials_button.setEnabled(False)  # Disable while logging in
        self.setup_progress.setVisible(True)
        self.setup_progress.setValue(0)

        # Make setup log visible for login process too
        self.setup_log_label.setVisible(True)
        self.setup_log.setVisible(True)
        self.setup_log.clear()

        # Pass all required components to the worker
        self.login_worker = AutoLoginWorker(username, password, executable_path,
                                            self.tos_launcher, self.window_manager)
        self.login_worker.status_update.connect(self.on_login_status_update)
        self.login_worker.progress_update.connect(self.on_login_progress_update)
        self.login_worker.login_complete.connect(self.on_login_complete)
        self.login_worker.start()

    @Slot()
    def check_tos_status(self):
        """Check ToS status and guide user through any issues."""
        print("🔍 Checking ToS status...")
        self.log_monitoring_event("🔍 Checking Thinkorswim status...")
        self.overall_status_label.setText("Status: Checking ToS...")
        QApplication.processEvents()

        # Get comprehensive status
        status_report = self.window_manager.get_tos_status_report()

        # Create status message
        status_message = "📊 ToS Status Report:\n\n"
        action_needed = True

        if status_report['main_trading_available']:
            status_message += "✅ Main trading window: Available\n"
            status_message += "🎯 Status: Ready for monitoring!\n\n"
            status_message += "Next steps:\n"
            status_message += "• Click '🎯 Setup Template' (if not done)\n"
            status_message += "• Click '📋 Read Accounts'\n"
            status_message += "• Click '🚀 Start Monitoring'"
            self.overall_status_label.setText("Status: ✅ ToS Ready")
            self.tos_hwnd = self.window_manager.hwnd  # Store the found HWND
            action_needed = False
        elif status_report['login_required']:
            status_message += "🔑 Login window detected\n"
            status_message += "⚠️ Status: Login required\n\n"
            status_message += "Options:\n"
            status_message += "• Click '🔑 Auto-Login ToS' for automatic login\n"
            status_message += "• Or complete login manually and check status again"
            self.overall_status_label.setText("Status: 🔑 Login required")
        elif status_report['launcher_open']:
            status_message += "🚀 Launcher window detected\n"
            status_message += "⚠️ Status: Need to open trading platform\n\n"
            status_message += "Options:\n"
            status_message += "• Click '🔑 Auto-Login ToS' for automatic setup\n"
            status_message += "• Or open trading platform manually and check status again"
            self.overall_status_label.setText("Status: 🚀 Open trading platform")
        elif status_report['other_tos_windows'] > 0:
            status_message += f"⚠️ Found {status_report['other_tos_windows']} other ToS windows\n"
            status_message += "⚠️ Status: Main trading window not detected\n\n"
            status_message += "Possible issues:\n"
            status_message += "• Main window still loading\n"
            status_message += "• ToS window title might have changed (Expected: 'Main@thinkorswim [build 1985]')\n"
            status_message += "• Try '🔑 Auto-Login ToS' to restart the process"
            self.overall_status_label.setText("Status: ⚠️ ToS loading or issues")
        else:
            status_message += "❌ No ToS windows found\n"
            status_message += "❌ Status: Thinkorswim not running\n\n"
            status_message += "Solution:\n"
            status_message += "• Click '🔑 Auto-Login ToS' to start and login automatically"
            self.overall_status_label.setText("Status: ❌ Start Thinkorswim")

        status_message += f"\n\nRecommended action:\n{status_report['recommended_action']}"

        # Show status in message box
        QMessageBox.information(self, "ToS Status Check", status_message)
        self.log_monitoring_event(f"📊 ToS Status: {status_report['recommended_action']}")
        self.update_button_states(action_needed=action_needed, tos_ready=status_report['main_trading_available'])

    @Slot()
    def setup_template(self):
        """Start the template setup process."""
        self.log_monitoring_event("🎯 Initiating template setup...")

        if not self.tos_hwnd:
            self.log_monitoring_event("⚠️ ToS HWND not available for template setup. Checking status...")
            self.check_tos_status()  # This will update self.tos_hwnd if main window is found
            if not self.tos_hwnd:
                QMessageBox.warning(self, "Setup Prerequisite",
                                    "Main ToS window not confirmed. Please use '🔍 Check Status' or '🔑 Auto-Login ToS' first.")
                return

        if not self.tos_navigator:
            self.tos_navigator = TosNavigator(self.tos_hwnd)

        # Ensure ToS window is focused for navigator
        if not self.window_manager.focus_tos_window():
            QMessageBox.warning(self, "Focus Warning",
                                "Could not focus ToS window. Template setup might be unreliable.")
            # Proceed with caution

        self.setup_progress.setVisible(True)
        self.setup_log_label.setVisible(True)
        self.setup_log.setVisible(True)
        self.setup_log.clear()

        self.update_button_states(setting_up_template=True)

        QMessageBox.information(self, "Template Setup Instructions",
                                "🎯 Template Setup for Multi-Account Dropdown\n\n"
                                "1. Ensure the ToS window is visible and preferably maximized.\n"
                                "2. When prompted by status messages:\n"
                                "   • DO NOTHING for 'Capturing before state'.\n"
                                "   • CLICK THE ACCOUNT DROPDOWN for 'Capturing after state'.\n"
                                "3. Make sure ALL your accounts are visible in the dropdown when it's open.\n"
                                "4. Keep the dropdown open until the capture completes.\n\n"
                                "Click OK to begin the automated capture process.")

        self.setup_worker = ScaledTemplateSetupWorker(self.tos_navigator)
        self.setup_worker.status_update.connect(self.on_setup_status_update)
        self.setup_worker.progress_update.connect(self.on_setup_progress_update)
        self.setup_worker.finished_setup.connect(self.on_setup_finished)
        self.setup_worker.start()

    @Slot()
    def discover_accounts(self):
        """Enhanced account discovery reading from the account dropdown."""
        self.log_monitoring_event("🔍 Starting dropdown-based discovery for all accounts...")

        if not self.tos_hwnd:
            self.log_monitoring_event("⚠️ ToS HWND not available for discovery. Checking status...")
            self.check_tos_status()
            if not self.tos_hwnd:
                QMessageBox.warning(self, "Discovery Prerequisite",
                                    "Main ToS window not confirmed. Please use '🔍 Check Status' or '🔑 Auto-Login ToS' first.")
                return

        # Ensure TosNavigator is initialized
        if not self.tos_navigator:
            self.tos_navigator = TosNavigator(self.tos_hwnd)

        # Ensure ToS window is focused
        if not self.window_manager.focus_tos_window():
            QMessageBox.warning(self, "Focus Warning", "Could not focus ToS window. Account discovery might fail.")
            # Proceed with caution

        self.accounts_table.setRowCount(0)
        self.discovered_accounts = []
        self.update_button_states(discovering_accounts=True)
        self.overall_status_label.setText("Status: 🔍 Reading accounts from dropdown...")
        QApplication.processEvents()

        try:
            from core.enhanced_dropdown_reader import DropdownAccountDiscovery

            # Pass the existing, focused TosNavigator to the DropdownAccountDiscovery
            dropdown_discovery = DropdownAccountDiscovery(self.tos_navigator)

            def status_update_for_discovery(message):
                self.overall_status_label.setText(f"Discovery: {message}")
                self.log_monitoring_event(f"[Discovery] {message}")
                QApplication.processEvents()

            discovered_account_names = dropdown_discovery.read_all_accounts_from_dropdown(
                save_debug=True  # Enable debug image saving
            )

            if discovered_account_names:
                for account_name in discovered_account_names:
                    self.add_account_to_table(
                        account_name, "Ready", "N/A", "Never", "0"
                    )
                    self.discovered_accounts.append(account_name)  # Store names for monitoring

                total_found = len(discovered_account_names)
                self.account_count_label.setText(f"📊 {total_found} accounts discovered")
                self.overall_status_label.setText(f"Status: ✅ Found {total_found} accounts")
                self.log_monitoring_event(f"✅ Dropdown discovery successful! Found {total_found} accounts.")

                account_list_str = "\n".join([f"• {name}" for name in discovered_account_names[:15]])
                if len(discovered_account_names) > 15:
                    account_list_str += f"\n... and {len(discovered_account_names) - 15} more."
                QMessageBox.information(self, "Discovery Successful",
                                        f"✅ Successfully read {total_found} accounts from dropdown!\n\n"
                                        f"Accounts found:\n{account_list_str}\n\n"
                                        "Ready for monitoring!")
            else:
                self.account_count_label.setText("❌ No accounts discovered")
                self.overall_status_label.setText("Status: ❌ Dropdown discovery failed")
                self.log_monitoring_event(
                    "❌ Dropdown-based discovery failed. Check debug images in assets/captures/dropdown.")
                QMessageBox.warning(self, "Discovery Failed",
                                    "❌ Could not read accounts from dropdown.\n\n"
                                    "Troubleshooting:\n"
                                    "• Ensure '🎯 Setup Template' was run successfully.\n"
                                    "• Check ToS: is the dropdown clickable and shows accounts?\n"
                                    "• Review images in 'assets/captures/dropdown/' folder.")
        except Exception as e:
            error_msg = f"❌ Discovery error: {e}"
            self.account_count_label.setText("❌ Discovery error")
            self.overall_status_label.setText(f"Status: {error_msg}")
            self.log_monitoring_event(error_msg)
            QMessageBox.critical(self, "Discovery Error",
                                 f"❌ An error occurred during discovery:\n\n{str(e)}\n\n"
                                 "Please check the logs and debug images.")
        finally:
            self.update_button_states(tos_ready=bool(self.tos_hwnd))

    def add_account_to_table(self, account_name: str, status: str, delta: str, last_check: str, alerts: str):
        """Add account with all columns."""
        row_position = self.accounts_table.rowCount()
        self.accounts_table.insertRow(row_position)
        self.accounts_table.setItem(row_position, 0, QTableWidgetItem(account_name))
        self.accounts_table.setItem(row_position, 1, QTableWidgetItem(status))
        self.accounts_table.setItem(row_position, 2, QTableWidgetItem(delta))
        self.accounts_table.setItem(row_position, 3, QTableWidgetItem(last_check))
        self.accounts_table.setItem(row_position, 4, QTableWidgetItem(alerts))

    def log_monitoring_event(self, message: str):
        """Log monitoring events with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.monitoring_log.append(formatted_message)
        scrollbar = self.monitoring_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_statistics_display(self):
        """Update the statistics display."""
        self.total_scans_label.setText(str(self.scan_stats['total_scans']))
        if self.scan_stats['total_scans'] > 0 and self.scan_stats['successful_scans'] > 0:  # Avoid division by zero
            success_rate = (self.scan_stats['successful_scans'] / self.scan_stats['total_scans']) * 100
            self.success_rate_label.setText(f"{success_rate:.1f}%")
        else:
            self.success_rate_label.setText("0.0%")

        self.avg_scan_time_label.setText(f"{self.scan_stats['average_scan_time']:.1f}s")
        online_accounts = 0  # Placeholder
        total_accounts = len(self.discovered_accounts)
        self.accounts_online_label.setText(f"{online_accounts}/{total_accounts}")
        self.alert_count_label.setText(str(self.scan_stats['alerts_today']))
        self.alert_count_label.setObjectName(
            "alertCountGreen" if self.scan_stats['alerts_today'] == 0 else "alertCount")
        self.alert_count_label.setStyleSheet(self.styleSheet())  # Reapply to update color

    @Slot()
    def start_monitoring(self):
        """Start monitoring."""
        account_count = len(self.discovered_accounts)
        if account_count == 0:
            QMessageBox.warning(self, "No Accounts", "No accounts discovered. Please run '📋 Read Accounts' first.")
            return

        reply = QMessageBox.question(self, "Start Monitoring",
                                     f"Start monitoring {account_count} discovered accounts?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        self._monitoring_active = True
        self.update_button_states(monitoring_active=True)
        scan_interval = self.scan_interval_spinner.value()
        fast_mode = self.fast_mode_checkbox.isChecked()
        self.overall_status_label.setText(f"Status: 🚀 Monitoring {account_count} accounts")
        mode_text = "Fast Mode" if fast_mode else "Standard Mode"
        self.log_monitoring_event(f"🚀 Started monitoring {account_count} accounts - {mode_text}")
        self.log_monitoring_event(f"⚙️ Scan interval: {scan_interval}s")
        # Placeholder for actual monitoring logic start

    @Slot()
    def stop_monitoring(self):
        """Stop monitoring."""
        self._monitoring_active = False
        self.update_button_states(monitoring_active=False)
        self.overall_status_label.setText("Status: ⏹️ Monitoring stopped")
        self.log_monitoring_event("⏹️ Monitoring stopped")
        # Placeholder for actual monitoring logic stop

    def update_button_states(self, monitoring_active=None, tos_ready=None, setting_up_template=False,
                             discovering_accounts=False, action_needed=True):
        """Centralized button state management."""
        if monitoring_active is None:
            monitoring_active = self._monitoring_active
        else:
            self._monitoring_active = monitoring_active

        if tos_ready is None:
            tos_ready = bool(self.tos_hwnd)  # Base it on whether we have a valid HWND

        # Login/Edit buttons are always enabled unless a worker is active
        login_worker_active = self.login_worker and self.login_worker.isRunning()
        setup_worker_active = self.setup_worker and self.setup_worker.isRunning()

        self.auto_login_button.setEnabled(not monitoring_active and not login_worker_active and not setup_worker_active)
        self.edit_credentials_button.setEnabled(
            not monitoring_active and not login_worker_active and not setup_worker_active)
        self.check_tos_button.setEnabled(not monitoring_active and not login_worker_active and not setup_worker_active)

        # Setup, Discover, Start, Stop
        self.setup_template_button.setEnabled(
            not monitoring_active and tos_ready and not login_worker_active and not setup_worker_active and not discovering_accounts)
        self.discover_button.setEnabled(
            not monitoring_active and tos_ready and not login_worker_active and not setup_worker_active and not setting_up_template)

        can_start_monitoring = bool(self.discovered_accounts) and tos_ready
        self.start_button.setEnabled(
            not monitoring_active and can_start_monitoring and not login_worker_active and not setup_worker_active and not setting_up_template and not discovering_accounts)
        self.stop_button.setEnabled(monitoring_active)

    @Slot(str)
    def on_login_status_update(self, message):
        self.overall_status_label.setText(f"Auto-Login: {message}")
        self.setup_log.append(f"[Login] {message}")  # Log to setup_log during login
        scrollbar = self.setup_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        QApplication.processEvents()

    @Slot(int)
    def on_login_progress_update(self, value):
        self.setup_progress.setValue(value)
        QApplication.processEvents()

    @Slot(bool)
    def on_login_complete(self, success):
        # login_worker becomes None after it finishes, so check self.login_worker
        # self.auto_login_button.setEnabled(True) # Managed by update_button_states
        # self.edit_credentials_button.setEnabled(True) # Managed by update_button_states

        QTimer.singleShot(2000, lambda: self.setup_progress.setVisible(False))
        # QTimer.singleShot(5000, lambda: self.setup_log.setVisible(False)) # Keep log visible

        if success:
            self.overall_status_label.setText("Status: ✅ Auto-Login Complete! ToS is ready.")
            self.log_monitoring_event("✅ Auto-login successful - ToS ready for monitoring!")
            self.tos_hwnd = self.window_manager.hwnd  # Crucial: store the HWND of the main window
            QMessageBox.information(self, "Auto-Login Complete",
                                    "✅ Auto-login successful!\n\n"
                                    "🎯 ToS is now ready for monitoring operations.\n"
                                    "Next: '🎯 Setup Template' or '📋 Read Accounts'.")
        else:
            self.overall_status_label.setText("Status: ❌ Auto-login failed. Check logs.")
            self.log_monitoring_event(
                "❌ Auto-login failed - check credentials, ToS state, or logs in 'Setup Log' panel.")
            QMessageBox.warning(self, "Auto-Login Failed",
                                "❌ Auto-login was not successful.\n\n"
                                "Review the 'Setup Log' panel for details.\n"
                                "Common issues:\n"
                                "• Incorrect credentials (use '✏️ Edit Credentials')\n"
                                "• ToS login screen changed or unexpected pop-ups\n"
                                "• Network or ToS server issues\n\n"
                                "Try manual login, then '🔍 Check Status'.")
        self.update_button_states(tos_ready=success)

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
        # Keep setup_log visible: QTimer.singleShot(5000, lambda: self.setup_log.setVisible(False))

        if success:
            self.overall_status_label.setText("Status: ✅ Template setup complete!")
            self.log_monitoring_event("✅ Template setup completed - Ready for account discovery!")
            QMessageBox.information(self, "Setup Complete",
                                    "✅ Template setup completed!\n\n"
                                    "🎯 Optimized for your account dropdown.\n"
                                    "Next: '📋 Read Accounts'.")
        else:
            self.overall_status_label.setText("Status: ❌ Template setup failed. Check logs.")
            self.log_monitoring_event("❌ Template setup failed. Review 'Setup Log' panel for details.")
            QMessageBox.warning(self, "Setup Failed",
                                "❌ Template setup failed.\n\n"
                                "Review the 'Setup Log' panel.\n"
                                "Ensure:\n"
                                "• ToS window is maximized and visible.\n"
                                "• You clicked the dropdown when prompted.\n"
                                "• All accounts were visible in the dropdown.")
        self.update_button_states(tos_ready=bool(self.tos_hwnd))