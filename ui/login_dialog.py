# ui/login_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QCheckBox,
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
import os

from utils.credential_manager import CredentialManager
from utils.tos_launcher import TosLauncher


class LoginDialog(QDialog):
    """Dialog for ThinkOrSwim credentials and auto-launch settings."""

    # Signal emitted when login is successful
    login_successful = Signal(str, str)  # username, password

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ThinkOrSwim Login")
        self.setFixedWidth(400)

        # Initialize managers
        self.credential_manager = CredentialManager()
        self.tos_launcher = TosLauncher()

        # Apply dark theme
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
        """Set up the UI layout."""
        layout = QVBoxLayout(self)

        # Info label
        info_label = QLabel("Enter your ThinkOrSwim credentials for auto-login:")
        layout.addWidget(info_label)

        # Form layout for credentials
        form_layout = QFormLayout()

        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        form_layout.addRow("Username:", self.username_edit)
        form_layout.addRow("Password:", self.password_edit)

        # TOS executable path
        exe_layout = QHBoxLayout()
        self.exe_path_edit = QLineEdit()
        self.exe_path_edit.setPlaceholderText("Auto-detect")
        self.exe_path_edit.setReadOnly(True)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_for_executable)

        exe_layout.addWidget(self.exe_path_edit)
        exe_layout.addWidget(browse_button)

        form_layout.addRow("TOS Executable:", exe_layout)

        layout.addLayout(form_layout)

        # Options
        self.save_credentials_check = QCheckBox("Save credentials securely")
        self.save_credentials_check.setChecked(True)
        layout.addWidget(self.save_credentials_check)

        self.auto_launch_check = QCheckBox("Auto-launch TOS on startup")
        self.auto_launch_check.setChecked(True)
        layout.addWidget(self.auto_launch_check)

        # Buttons
        button_layout = QHBoxLayout()

        self.test_button = QPushButton("Test Login")
        self.test_button.clicked.connect(self.test_login)
        button_layout.addWidget(self.test_button)

        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        self.login_button = QPushButton("Login & Continue")
        self.login_button.setObjectName("loginButton")
        self.login_button.clicked.connect(self.accept_login)
        button_layout.addWidget(self.login_button)

        layout.addLayout(button_layout)

    def load_saved_credentials(self):
        """Load saved credentials if available."""
        username, password = self.credential_manager.get_credentials()

        if username:
            self.username_edit.setText(username)

        if password:
            self.password_edit.setText(password)

        # Try to find TOS executable
        executable_path = self.tos_launcher.find_tos_executable()
        if executable_path:
            self.exe_path_edit.setText(executable_path)

    def browse_for_executable(self):
        """Open file dialog to browse for TOS executable."""
        file_filter = "Executable files (*.exe);;All files (*.*)"

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select ThinkOrSwim Executable",
            os.path.expanduser("~"), file_filter
        )

        if file_path:
            self.exe_path_edit.setText(file_path)

    def test_login(self):
        """Test login credentials."""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "Missing Credentials",
                                "Please enter both username and password")
            return

        reply = QMessageBox.question(
            self, "Confirm Test Login",
            "This will launch ThinkOrSwim and attempt to login.\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        # Get executable path
        exe_path = self.exe_path_edit.text() if self.exe_path_edit.text() else None

        # Launch and login
        self.tos_launcher.launch_tos(exe_path)

        # Show countdown message box
        msg = QMessageBox(self)
        msg.setWindowTitle("Login in Progress")
        msg.setText("Attempting to login to ThinkOrSwim...\n\n"
                    "Please wait and don't interact with the login window.")
        msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        msg.show()

        # Login
        success = self.tos_launcher.login_to_tos(username, password)

        # Close message
        msg.close()

        if success:
            QMessageBox.information(self, "Login Successful",
                                    "ThinkOrSwim login was successful!")
        else:
            QMessageBox.warning(self, "Login Failed",
                                "ThinkOrSwim login attempt failed.\n\n"
                                "Please check your credentials and try again.")

    def accept_login(self):
        """Handle login button click."""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "Missing Credentials",
                                "Please enter both username and password")
            return

        # Get executable path
        exe_path = self.exe_path_edit.text().strip() if self.exe_path_edit.text().strip() else None

        # Save credentials including executable path
        if self.save_credentials_check.isChecked():
            self.credential_manager.save_credentials(username, password, exe_path)

        # Emit signal with credentials
        self.login_successful.emit(username, password)

        # Close dialog
        self.accept()