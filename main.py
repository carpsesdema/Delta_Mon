# main.py (modified)

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.login_dialog import LoginDialog
from utils.credential_manager import CredentialManager
from utils.tos_launcher import TosLauncher


def main():
    app = QApplication(sys.argv)

    # Initialize credential manager
    credential_manager = CredentialManager()

    # Show login dialog first
    login_dialog = LoginDialog()

    if login_dialog.exec():
        # Login accepted
        username, password = credential_manager.get_credentials()

        # Create and show main window
        window = MainWindow()
        window.show()

        # Launch TOS if auto-launch is enabled
        if login_dialog.auto_launch_check.isChecked():
            tos_launcher = TosLauncher()
            tos_launcher.launch_and_login(username, password)

        sys.exit(app.exec())
    else:
        # Login cancelled
        sys.exit(0)


if __name__ == "__main__":
    main()