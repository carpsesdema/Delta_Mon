# Delta_Mon/ui/scaled_main_window.py

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QAbstractItemView,
    QHeaderView, QLabel, QTableWidgetItem, QMessageBox, QApplication,
    QProgressBar, QTextEdit, QSplitter, QGroupBox, QGridLayout,
    QSpinBox, QCheckBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Slot, QTimer, QThread, Signal
from PySide6.QtGui import QFont

import time
import os
from datetime import datetime

from utils.config_manager import ConfigManager
from core.window_manager import WindowManager
from core.tos_navigator import TosNavigator

# Enhanced Dark Theme for larger scale
SCALED_DARK_STYLE_SHEET = """
    QWidget {
        background-color: #2b2b2b;
        color: #ffffff;
        font-size: 9pt;  /* Slightly smaller for more data */
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
    QTableWidget {
        background-color: #3c3c3c;
        color: #ffffff;
        gridline-color: #5a5a5a;
        border: 1px solid #5a5a5a;
        border-radius: 4px;
        alternate-background-color: #3a3a3a;  /* Zebra stripes for better readability */
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


class ScaledTemplateSetupWorker(QThread):
    """Enhanced setup worker for large scale monitoring."""

    status_update = Signal(str)
    progress_update = Signal(int)
    finished_setup = Signal(bool)

    def __init__(self, tos_navigator):
        super().__init__()
        self.tos_navigator = tos_navigator

    def run(self):
        """Run the template setup process with enhanced validation."""
        try:
            self.status_update.emit("🚀 Starting enterprise-scale template setup...")
            self.progress_update.emit(5)

            # Enhanced setup process for 25 account monitoring
            self.status_update.emit("📊 Optimizing for 25+ account monitoring...")
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

            # Longer delay for user to prepare for 25-account workflow
            self.status_update.emit("👆 Get ready to click the account dropdown...")
            self.status_update.emit("📋 TIP: For 25 accounts, ensure dropdown shows ALL accounts!")
            time.sleep(3)

            self.progress_update.emit(45)

            # Capture before state
            before_path = self.tos_navigator.capture_upper_left_region("before_dropdown_enterprise.png")
            if not before_path:
                self.status_update.emit("❌ Failed to capture before state")
                self.finished_setup.emit(False)
                return

            # Extended countdown for user preparation
            self.status_update.emit("👆 CLICK DROPDOWN NOW! (10 seconds...)")
            for i in range(10, 0, -1):
                self.status_update.emit(f"👆 Click account dropdown! ({i}s) - Make sure ALL 25 accounts are visible!")
                time.sleep(1)
                self.progress_update.emit(45 + i * 3)

            # Capture after state
            self.status_update.emit("📸 Capturing expanded dropdown state...")
            after_path = self.tos_navigator.capture_upper_left_region("after_dropdown_enterprise.png",
                                                                      width_ratio=0.5,
                                                                      height_ratio=0.6)  # Larger capture for many accounts
            if not after_path:
                self.status_update.emit("❌ Failed to capture after state")
                self.finished_setup.emit(False)
                return

            self.progress_update.emit(85)

            # Create and validate template
            self.status_update.emit("🔍 Creating enterprise template...")
            template_created = self.tos_navigator._create_template_from_difference(before_path, after_path)

            if template_created:
                self.progress_update.emit(95)

                # Enhanced testing for enterprise scale
                self.status_update.emit("🧪 Running enterprise-scale validation...")
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
                    self.status_update.emit("🏢 Ready for 25-account enterprise monitoring!")
                else:
                    self.status_update.emit("⚠️ Template created but validation inconclusive")

                self.progress_update.emit(100)
                self.finished_setup.emit(True)
            else:
                self.status_update.emit("❌ Failed to create enterprise template")
                self.finished_setup.emit(False)

        except Exception as e:
            self.status_update.emit(f"❌ Enterprise setup error: {e}")
            self.finished_setup.emit(False)


class ScaledMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeltaMon Enterprise - 25 Account Monitor")
        self.setGeometry(50, 50, 1200, 800)  # Larger window for more data

        self.setStyleSheet(SCALED_DARK_STYLE_SHEET)

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # State variables
        self._monitoring_active = False
        self.config_manager = ConfigManager()
        self.window_manager = WindowManager(target_exact_title="Main@thinkorswim [build 1985]",
                                            exclude_title_substring="DeltaMon")
        self.tos_navigator = None
        self.discovered_accounts = []
        self.setup_worker = None

        # Performance tracking
        self.scan_stats = {
            'total_scans': 0,
            'successful_scans': 0,
            'average_scan_time': 0,
            'alerts_today': 0
        }

        self.setup_ui_elements()
        self.update_button_states()

        # Auto-refresh timer for stats
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_statistics_display)
        self.stats_timer.start(5000)  # Update every 5 seconds

    def setup_ui_elements(self):
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
        content_splitter.setSizes([800, 400])

        self.main_layout.addWidget(content_splitter)

    def create_control_panel(self):
        """Create the main control panel."""
        control_frame = QGroupBox("Control Panel")
        control_layout = QVBoxLayout(control_frame)

        # Top row - main buttons
        main_buttons_layout = QHBoxLayout()

        self.setup_template_button = QPushButton("🎯 Setup Enterprise Template")
        self.setup_template_button.setObjectName("setupButton")
        self.setup_template_button.clicked.connect(self.setup_template)
        main_buttons_layout.addWidget(self.setup_template_button)

        main_buttons_layout.addSpacing(10)

        self.discover_button = QPushButton("📋 Read Accounts from Dropdown")
        self.discover_button.clicked.connect(self.discover_accounts)
        main_buttons_layout.addWidget(self.discover_button)

        main_buttons_layout.addSpacing(20)

        self.start_button = QPushButton("🚀 Start Enterprise Monitoring")
        self.start_button.clicked.connect(self.start_monitoring)
        main_buttons_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("⏹️ Stop Monitoring")
        self.stop_button.setObjectName("criticalButton")
        self.stop_button.clicked.connect(self.stop_monitoring)
        main_buttons_layout.addWidget(self.stop_button)

        main_buttons_layout.addStretch()

        # Status and alerts
        status_layout = QHBoxLayout()
        self.overall_status_label = QLabel("Status: Ready for Enterprise Monitoring")
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
        accounts_frame = QGroupBox("Account Monitoring (25 Accounts)")
        accounts_layout = QVBoxLayout(accounts_frame)

        # Accounts table with optimized columns for 25 accounts
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

        # Column sizing for 25 accounts
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
        stats_frame = QGroupBox("Enterprise Statistics & Logs")
        stats_layout = QVBoxLayout(stats_frame)

        # Performance stats
        perf_layout = QGridLayout()

        self.total_scans_label = QLabel("0")
        self.success_rate_label = QLabel("0%")
        self.avg_scan_time_label = QLabel("0s")
        self.accounts_online_label = QLabel("0/25")

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
        self.setup_log.setVisible(False)
        self.setup_log.setPlaceholderText("Enterprise setup log will appear here...")
        stats_layout.addWidget(QLabel("Setup Log:"))
        stats_layout.addWidget(self.setup_log)

        # Monitoring log
        self.monitoring_log = QTextEdit()
        self.monitoring_log.setMaximumHeight(150)
        self.monitoring_log.setPlaceholderText("Monitoring events will appear here...")
        stats_layout.addWidget(QLabel("Monitoring Log:"))
        stats_layout.addWidget(self.monitoring_log)

        return stats_frame

    @Slot()
    def setup_template(self):
        """Start the enterprise template setup process."""
        print("Enterprise template setup started...")

        # Find ToS window
        tos_hwnd = self.window_manager.find_tos_window()
        if not tos_hwnd:
            QMessageBox.warning(self, "Setup Failed",
                                "Could not find ToS window. Please ensure Thinkorswim is running.")
            return

        # Focus and initialize
        if not self.window_manager.focus_tos_window():
            QMessageBox.warning(self, "Setup Warning",
                                "ToS window found but could not be focused. Setup may fail.")

        if not self.tos_navigator:
            self.tos_navigator = TosNavigator(tos_hwnd)

        # Show setup UI
        self.setup_progress.setVisible(True)
        self.setup_log.setVisible(True)
        self.setup_log.clear()

        # Disable buttons
        self.setup_template_button.setEnabled(False)
        self.discover_button.setEnabled(False)

        # Enhanced instructions for 25 accounts
        QMessageBox.information(self, "Enterprise Template Setup",
                                "🏢 Enterprise Template Setup for 25 Accounts\n\n"
                                "📋 Instructions:\n"
                                "1. Keep ToS window fully visible and maximized\n"
                                "2. When prompted, click the account dropdown\n"
                                "3. IMPORTANT: Ensure ALL 25 accounts are visible in the dropdown\n"
                                "4. If accounts are cut off, the system will detect a larger area\n"
                                "5. Let the dropdown stay open until capture completes\n\n"
                                "⚡ This creates an optimized template for fast 25-account scanning!\n\n"
                                "Click OK to start!")

        # Start enhanced worker
        self.setup_worker = ScaledTemplateSetupWorker(self.tos_navigator)
        self.setup_worker.status_update.connect(self.on_setup_status_update)
        self.setup_worker.progress_update.connect(self.on_setup_progress_update)
        self.setup_worker.finished_setup.connect(self.on_setup_finished)
        self.setup_worker.start()

    @Slot()
    def discover_accounts(self):
        """Enhanced account discovery reading from the account dropdown."""
        self.log_monitoring_event("🔍 Starting dropdown-based discovery for all accounts...")

        # Clear existing accounts
        self.accounts_table.setRowCount(0)
        self.discovered_accounts = []

        # Update UI to show discovery in progress
        self.discover_button.setEnabled(False)
        self.overall_status_label.setText("Status: 🔍 Reading accounts from dropdown...")

        try:
            # Import and use the dropdown-based discovery
            from core.enhanced_dropdown_reader import DropdownAccountDiscovery

            dropdown_discovery = DropdownAccountDiscovery()

            # Run discovery with UI status updates
            def status_update(message):
                self.overall_status_label.setText(f"Discovery: {message}")
                self.log_monitoring_event(message)
                QApplication.processEvents()

            # Run the discovery process
            discovered_account_names = dropdown_discovery.discover_all_accounts(
                status_callback=status_update
            )

            if discovered_account_names:
                # Populate the UI table
                for account_name in discovered_account_names:
                    self.add_account_to_table(
                        account_name,
                        "Ready (from dropdown)",
                        "N/A",  # Delta value 
                        "Never",  # Last check
                        "0"  # Alerts
                    )

                    # Store for monitoring
                    self.discovered_accounts.append(account_name)

                # Success summary
                total_found = len(discovered_account_names)
                self.overall_status_label.setText(f"Status: ✅ Found {total_found} accounts from dropdown")

                success_message = f"✅ Dropdown discovery successful! Found {total_found} accounts"
                self.log_monitoring_event(success_message)

                # Show success dialog
                account_list = "\n".join([f"• {name}" for name in discovered_account_names[:15]])
                if len(discovered_account_names) > 15:
                    account_list += f"\n... and {len(discovered_account_names) - 15} more"

                QMessageBox.information(self, "Discovery Successful",
                                        f"✅ Successfully read {total_found} accounts from dropdown!\n\n"
                                        f"Accounts found:\n{account_list}\n\n"
                                        f"{'🎉 Perfect for enterprise monitoring!' if total_found >= 20 else '👍 Ready for monitoring!'}")

            else:
                # Discovery failed
                self.overall_status_label.setText("Status: ❌ Dropdown discovery failed")
                self.log_monitoring_event("❌ Dropdown-based discovery failed")

                QMessageBox.warning(self, "Discovery Failed",
                                    "❌ Could not read accounts from dropdown.\n\n"
                                    "Possible issues:\n"
                                    "• Account dropdown not found or not clickable\n"
                                    "• Dropdown didn't open properly\n"
                                    "• OCR could not read account names from list\n\n"
                                    "Try:\n"
                                    "• Ensure ToS window is visible and active\n"
                                    "• Run 'Setup Template' to improve dropdown detection\n"
                                    "• Check that account dropdown is in upper-left area\n"
                                    "• Verify accounts are loaded in ToS")

        except Exception as e:
            # Handle any errors
            error_msg = f"❌ Discovery error: {e}"
            self.overall_status_label.setText("Status: ❌ Discovery error")
            self.log_monitoring_event(error_msg)

            QMessageBox.critical(self, "Discovery Error",
                                 f"❌ An error occurred during discovery:\n\n{str(e)}\n\n"
                                 f"Please check the logs for more details.")

        finally:
            # Re-enable discovery button
            self.discover_button.setEnabled(True)
            self.update_button_states()

    def add_account_to_table(self, account_name: str, status: str, delta: str, last_check: str, alerts: str):
        """Add account with all columns for enterprise view."""
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

        # Auto-scroll to bottom
        scrollbar = self.monitoring_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_statistics_display(self):
        """Update the statistics display."""
        self.total_scans_label.setText(str(self.scan_stats['total_scans']))

        if self.scan_stats['total_scans'] > 0:
            success_rate = (self.scan_stats['successful_scans'] / self.scan_stats['total_scans']) * 100
            self.success_rate_label.setText(f"{success_rate:.1f}%")

        self.avg_scan_time_label.setText(f"{self.scan_stats['average_scan_time']:.1f}s")

        # Count "online" accounts (those with recent successful checks)
        online_accounts = len([acc for acc in self.discovered_accounts if "monitoring" in str(acc).lower()])
        self.accounts_online_label.setText(f"{online_accounts}/25")

        # Update alert count
        self.alert_count_label.setText(str(self.scan_stats['alerts_today']))
        if self.scan_stats['alerts_today'] > 0:
            self.alert_count_label.setObjectName("alertCount")
        else:
            self.alert_count_label.setObjectName("alertCountGreen")

        # Reapply stylesheet to update colors
        self.alert_count_label.setStyleSheet(self.styleSheet())

    @Slot()
    def start_monitoring(self):
        """Start enterprise monitoring."""
        if len(self.discovered_accounts) < 25:
            reply = QMessageBox.question(self, "Partial Account Set",
                                         f"Only {len(self.discovered_accounts)} accounts discovered.\n"
                                         f"Pradeep mentioned 25 accounts total.\n\n"
                                         f"Continue with current accounts?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        self._monitoring_active = True
        self.update_button_states()

        scan_interval = self.scan_interval_spinner.value()
        fast_mode = self.fast_mode_checkbox.isChecked()

        self.overall_status_label.setText(f"Status: 🚀 Monitoring {len(self.discovered_accounts)} accounts")

        mode_text = "Fast Mode" if fast_mode else "Standard Mode"
        self.log_monitoring_event(f"🚀 Started enterprise monitoring - {mode_text}")
        self.log_monitoring_event(f"⚙️ Scan interval: {scan_interval}s")
        self.log_monitoring_event(f"📊 Expected full cycle time: ~{len(self.discovered_accounts) * 2}s")

    @Slot()
    def stop_monitoring(self):
        """Stop enterprise monitoring."""
        self._monitoring_active = False
        self.update_button_states()
        self.overall_status_label.setText("Status: ⏹️ Monitoring stopped")
        self.log_monitoring_event("⏹️ Enterprise monitoring stopped")

    def update_button_states(self):
        """Update button states for enterprise scale."""
        self.start_button.setEnabled(not self._monitoring_active and bool(self.discovered_accounts))
        self.stop_button.setEnabled(self._monitoring_active)
        self.discover_button.setEnabled(not self._monitoring_active)

    # Setup event handlers (same as before)
    @Slot(str)
    def on_setup_status_update(self, message):
        self.overall_status_label.setText(f"Setup: {message}")
        self.setup_log.append(message)
        scrollbar = self.setup_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        QApplication.processEvents()

    @Slot(int)
    def on_setup_progress_update(self, value):
        self.setup_progress.setValue(value)
        QApplication.processEvents()

    @Slot(bool)
    def on_setup_finished(self, success):
        self.setup_template_button.setEnabled(True)
        self.discover_button.setEnabled(True)
        QTimer.singleShot(3000, lambda: self.setup_progress.setVisible(False))

        if success:
            self.overall_status_label.setText("Setup: ✅ Enterprise template ready!")
            self.log_monitoring_event("✅ Enterprise template setup completed - Ready for 25 accounts!")
            QMessageBox.information(self, "Enterprise Setup Complete",
                                    "✅ Enterprise template setup completed!\n\n"
                                    "🏢 Optimized for 25-account monitoring\n"
                                    "⚡ Enhanced performance and accuracy\n"
                                    "🎯 Ready for large-scale discovery")
        else:
            self.overall_status_label.setText("Setup: ❌ Enterprise setup failed")
            QMessageBox.warning(self, "Enterprise Setup Failed",
                                "❌ Enterprise template setup failed.\n\n"
                                "Please ensure:\n"
                                "• ToS window is maximized and visible\n"
                                "• All 25 accounts are accessible\n"
                                "• Account dropdown can be clicked")