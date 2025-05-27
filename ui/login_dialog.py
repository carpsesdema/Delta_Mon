from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QCheckBox,
    QMessageBox, QFileDialog, QApplication
)
from PySide6.QtCore import Qt, Signal
import os

from utils.credential_manager import CredentialManager
from utils.tos_launcher import TosLauncher


class LoginDialog(QDialog):
    login_successful = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ThinkOrSwim Login & Setup")
        self.setFixedWidth(450)

        self.credential_manager = CredentialManager()
        self.tos_launcher = TosLauncher()

        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                padding: 2px;
            }
            QLineEdit {
                background-color: #4a4a4a;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #5a5a5a;
                padding: 8px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton#loginButton {
                background-color: #27ae60;
            }
            QPushButton#loginButton:hover {
                background-color: #2ecc71;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                background-color: #4a4a4a;
                border: 1px solid #5a5a5a;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #2ecc71;
            }
        """)

        self.setup_ui()
        self.load_saved_credentials()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        info_label = QLabel("Enter ThinkOrSwim credentials and verify executable path:")
        layout.addWidget(info_label)

        form_layout = QFormLayout()

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Your ToS Username")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Your ToS Password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        form_layout.addRow("Username:", self.username_edit)
        form_layout.addRow("Password:", self.password_edit)

        exe_path_label = QLabel("ToS Executable Path:")
        self.exe_path_edit = QLineEdit()
        self.exe_path_edit.setPlaceholderText("Click 'Auto-Detect' or 'Browse...'")

        exe_buttons_layout = QHBoxLayout()
        auto_detect_button = QPushButton("Auto-Detect")
        auto_detect_button.clicked.connect(self.auto_detect_executable)
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_for_executable)

        exe_buttons_layout.addWidget(auto_detect_button)
        exe_buttons_layout.addWidget(browse_button)

        form_layout.addRow(exe_path_label, self.exe_path_edit)
        form_layout.addRow("", exe_buttons_layout)

        layout.addLayout(form_layout)

        self.save_credentials_check = QCheckBox("Save credentials and path securely")
        self.save_credentials_check.setChecked(True)
        layout.addWidget(self.save_credentials_check)

        button_layout = QHBoxLayout()

        self.test_button = QPushButton("Test Launch & Login")
        self.test_button.clicked.connect(self.test_login)
        button_layout.addWidget(self.test_button)

        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        self.login_button = QPushButton("Save & Continue")
        self.login_button.setObjectName("loginButton")
        self.login_button.clicked.connect(self.accept_login)
        button_layout.addWidget(self.login_button)

        layout.addLayout(button_layout)

    def load_saved_credentials(self):
        username, password, executable_path = self.credential_manager.get_credentials()

        if username:
            self.username_edit.setText(username)
        if password:
            self.password_edit.setText(password)

        if executable_path and os.path.exists(executable_path):
            self.exe_path_edit.setText(executable_path)
        else:

            self.auto_detect_executable(silent=True)

    def auto_detect_executable(self, silent=False):
        print("Attempting to auto-detect ToS executable...")
        found_path = self.tos_launcher.find_tos_executable()
        if found_path:
            self.exe_path_edit.setText(found_path)
            if not silent:
                QMessageBox.information(self, "Executable Found", f"Auto-detected ToS executable at:\n{found_path}")
        elif not silent:
            QMessageBox.information(self, "Not Found",
                                    "Could not auto-detect ToS executable.\nPlease use 'Browse...' to locate it manually.")

    def browse_for_executable(self):
        current_dir = os.path.dirname(self.exe_path_edit.text()) if self.exe_path_edit.text() else os.path.expanduser(
            "~")

        file_filter = "Executables (*.exe *.lnk);;All files (*.*)" if os.name == 'nt' else "All files (*)"

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select ThinkOrSwim Executable or Shortcut",
            current_dir, file_filter
        )

        if file_path:
            self.exe_path_edit.setText(file_path)

    def test_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        exe_path = self.exe_path_edit.text().strip()

        if not username or not password:
            QMessageBox.information(self, "Missing Credentials", "Please enter both username and password.")
            return

        if not exe_path:
            QMessageBox.information(self, "Missing Executable Path",
                                    "Please provide the path to ThinkOrSwim executable or shortcut.")
            return

        if not os.path.exists(exe_path):
            QMessageBox.information(self, "Invalid Path", f"The specified executable path does not exist:\n{exe_path}")
            return

        reply = QMessageBox.question(
            self, "Confirm Test",
            "This will attempt to launch ThinkOrSwim and log in with the provided details.\n"
            "Ensure ToS is closed or you are logged out for a clean test.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Test in Progress")
        msg_box.setText("Attempting to launch and login to ThinkOrSwim...\n\n"
                        "Please wait and do not interact with ToS windows during this test.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.NoButton)
        msg_box.show()
        QApplication.processEvents()

        launch_success = self.tos_launcher.launch_tos(exe_path)
        login_success = False
        if launch_success:
            login_success = self.tos_launcher.login_to_tos(username, password)

        msg_box.close()

        if launch_success and login_success:
            QMessageBox.information(self, "Test Successful",
                                    "ThinkOrSwim launched and login sequence initiated successfully!")
        elif launch_success and not login_success:
            QMessageBox.information(self, "Login Partially Successful",
                                    "ThinkOrSwim launched, but login sequence failed or timed out.\nCheck credentials and ToS state.")
        else:
            QMessageBox.information(self, "Test Failed",
                                    "Failed to launch ThinkOrSwim.\nPlease check the executable path and ensure ToS can be started manually.")

    def accept_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        exe_path = self.exe_path_edit.text().strip()

        if not username or not password:
            QMessageBox.information(self, "Missing Credentials", "Please enter both username and password.")
            return

        if not exe_path:
            QMessageBox.information(self, "Missing Executable Path",
                                    "Please provide the ToS executable path.\n"
                                    "Use 'Auto-Detect' or 'Browse...'.")
            return

        if not os.path.exists(exe_path):
            QMessageBox.information(self, "Invalid Path", f"The ToS executable path is invalid:\n{exe_path}")
            return

        if self.save_credentials_check.isChecked():
            save_ok = self.credential_manager.save_credentials(username, password, exe_path)
            if not save_ok:
                QMessageBox.information(self, "Save Error", "Could not save credentials. Check console for details.")

        self.login_successful.emit(username, password, exe_path)

        self.accept()