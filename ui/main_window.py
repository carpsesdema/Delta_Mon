# Delta_Mon/ui/main_window.py

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QAbstractItemView,
    QHeaderView, QLabel, QTableWidgetItem, QMessageBox, QApplication  # Added QApplication
)
from PySide6.QtCore import Qt, Slot  # QTimer removed, time.sleep is used directly for simplicity now

import time  # For simple pauses
import os  # For os.path.basename

from utils.config_manager import ConfigManager
from core.window_manager import WindowManager  # Uses pywin32 version
from core.tos_navigator import TosNavigator

# Basic Dark Theme QSS (remains the same)
DARK_STYLE_SHEET = """
    QWidget {
        background-color: #2b2b2b;
        color: #ffffff;
        font-size: 10pt;
    }
    QMainWindow {
        background-color: #2b2b2b;
    }
    QPushButton {
        background-color: #4a4a4a;
        color: #ffffff;
        border: 1px solid #5a5a5a;
        padding: 8px;
        min-height: 20px; /* Minimum height for buttons */
        border-radius: 4px;
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
    QTableWidget {
        background-color: #3c3c3c;
        color: #ffffff;
        gridline-color: #5a5a5a;
        border: 1px solid #5a5a5a;
        border-radius: 4px;
    }
    QHeaderView::section {
        background-color: #4a4a4a;
        color: #ffffff;
        padding: 4px;
        border: 1px solid #5a5a5a;
        font-weight: bold;
    }
    QTableWidget::item {
        padding: 5px;
    }
    QTableWidget::item:selected {
        background-color: #5a6370; /* A distinct selection color */
        color: #ffffff;
    }
    QLabel { /* General styling for labels */
        padding: 2px;
    }
    QLabel#statusLabel { /* Specific styling for the overall status label */
        font-weight: bold;
        padding: 5px;
        color: #cccccc; /* Lighter grey for less emphasis than pure white */
        border: 1px solid #4a4a4a; /* Optional: give it a subtle border */
        border-radius: 3px;
        background-color: #333333; /* Slightly different background */
    }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeltaMon - Thinkorswim Monitor")
        self.setGeometry(100, 100, 800, 600)

        self.setStyleSheet(DARK_STYLE_SHEET)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._monitoring_active = False
        self.config_manager = ConfigManager()
        # Initialize WindowManager with the exact title you provided
        self.window_manager = WindowManager(target_exact_title="Main@thinkorswim [build 1985]",
                                            exclude_title_substring="DeltaMon")
        self.tos_navigator = None
        self.discovered_accounts = []

        self.setup_ui_elements()
        self.update_button_states()

    def setup_ui_elements(self):
        # UI setup code (buttons, table, labels) remains the same as your last version
        # --- Control Buttons ---
        controls_layout = QHBoxLayout()
        self.discover_button = QPushButton("Discover Accounts (ToS)")
        self.discover_button.clicked.connect(self.discover_accounts)
        controls_layout.addWidget(self.discover_button)
        controls_layout.addSpacing(20)
        self.start_button = QPushButton("Start Monitoring")
        self.start_button.clicked.connect(self.start_monitoring)
        controls_layout.addWidget(self.start_button)
        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.clicked.connect(self.stop_monitoring)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addStretch()

        self.overall_status_label = QLabel("Status: Idle")
        self.overall_status_label.setObjectName("statusLabel")

        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(2)
        self.accounts_table.setHorizontalHeaderLabels(["Account", "Status"])
        self.accounts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.accounts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.accounts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.accounts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.accounts_table.verticalHeader().setVisible(False)
        self.accounts_table.setMinimumHeight(200)

        top_layout = QHBoxLayout()
        top_layout.addLayout(controls_layout)
        top_layout.addStretch()
        top_layout.addWidget(self.overall_status_label)

        self.main_layout.addLayout(top_layout)
        self.main_layout.addWidget(QLabel("Monitored Accounts:"))
        self.main_layout.addWidget(self.accounts_table)

    @Slot()
    def discover_accounts(self):
        print("Discover Accounts process started...")
        self.overall_status_label.setText("Status: Locating ToS window...")
        QApplication.processEvents()

        self.accounts_table.setRowCount(0)
        self.discovered_accounts = []
        # self.update_button_states() # update_button_states() will be called at the end

        tos_hwnd = self.window_manager.find_tos_window()  # Returns HWND or None
        if not tos_hwnd:
            self.overall_status_label.setText("Status: ToS window not found.")
            QMessageBox.warning(self, "Discovery Failed",
                                "Could not find the ToS window using title 'Main@thinkorswim [build 1985]'. Please ensure it is running and the title is exact.")
            self.update_button_states()
            return

        if not self.window_manager.focus_tos_window():  # focus_tos_window uses the stored self.hwnd
            self.overall_status_label.setText("Status: ToS window found but could not focus.")
            QMessageBox.warning(self, "Discovery Warning",
                                "ToS window found but could not be focused. Automation might fail.")
            # self.update_button_states() # Decide if we should proceed or not
            # return

        self.tos_navigator = TosNavigator(tos_hwnd)  # Pass the HWND
        self.overall_status_label.setText("Status: ToS window focused. Clicking dropdown...")
        QApplication.processEvents()

        if self.tos_navigator.click_account_dropdown():
            self.overall_status_label.setText("Status: Dropdown clicked. Capturing list area...")
            QApplication.processEvents()

            time.sleep(1.0)  # Pause for dropdown to visually appear

            # Adjust these parameters in TosNavigator as needed:
            # offset_x_from_trigger, offset_y_from_trigger_bottom, width, height
            captured_image_path = self.tos_navigator.capture_dropdown_area(
                offset_x_from_trigger=0,  # e.g., -10 to shift left, 10 to shift right from trigger's left edge
                offset_y_from_trigger_bottom=2,  # e.g., 2-5 pixels below the trigger template
                width=250,  # Approximate width of your dropdown
                height=200  # Approximate height of your dropdown
            )
            if captured_image_path:
                self.overall_status_label.setText(f"Status: Dropdown captured: {os.path.basename(captured_image_path)}")
                QMessageBox.information(self, "Capture Success",
                                        f"Dropdown area image saved to:\n{captured_image_path}\n\nPlease check this image. Next step is OCR.")
            else:
                self.overall_status_label.setText("Status: Failed to capture dropdown area.")
                QMessageBox.warning(self, "Capture Failed",
                                    "Could not capture the dropdown list area. Check console for errors. Ensure ToS window is not obstructed.")
        else:
            self.overall_status_label.setText("Status: Failed to find/click account dropdown.")
            QMessageBox.warning(self, "Discovery Failed",
                                "Could not find or click the account dropdown in ToS. Check template image and ToS window state.")
            self.update_button_states()
            return

        print("SIMULATED account population from config (actual OCR is next step)...")
        simulated_accounts_from_config = self.config_manager.get_account_list()
        if simulated_accounts_from_config:
            self.discovered_accounts = simulated_accounts_from_config
            for acc_name in self.discovered_accounts:
                self.add_account_to_table(acc_name, "Ready (Simulated from config)")
        else:
            self.add_account_to_table("No accounts in config.", "Simulated")

        self.update_button_states()

    def update_button_states(self):
        self.start_button.setEnabled(not self._monitoring_active and bool(self.discovered_accounts))
        self.stop_button.setEnabled(self._monitoring_active)
        self.discover_button.setEnabled(not self._monitoring_active)

    # start_monitoring, stop_monitoring, add_account_to_table, update_account_status remain the same
    @Slot()
    def start_monitoring(self):
        if not self.discovered_accounts:
            self.overall_status_label.setText("Status: Discover accounts first")
            return
        self._monitoring_active = True
        self.update_button_states()
        self.overall_status_label.setText("Status: Monitoring (Simulated)...")
        for acc_name in self.discovered_accounts:
            self.update_account_status(acc_name, "Monitoring (Simulated)...")

    @Slot()
    def stop_monitoring(self):
        self._monitoring_active = False
        self.update_button_states()
        self.overall_status_label.setText("Status: Stopped")
        for acc_name in self.discovered_accounts:
            self.update_account_status(acc_name, "Stopped (Ready)")

    def add_account_to_table(self, account_name: str, status: str):
        row_position = self.accounts_table.rowCount()
        self.accounts_table.insertRow(row_position)
        self.accounts_table.setItem(row_position, 0, QTableWidgetItem(account_name))
        self.accounts_table.setItem(row_position, 1, QTableWidgetItem(status))

    def update_account_status(self, account_name: str, new_status: str):
        for row in range(self.accounts_table.rowCount()):
            item = self.accounts_table.item(row, 0)
            if item and item.text() == account_name:
                self.accounts_table.setItem(row, 1, QTableWidgetItem(new_status))
                return