import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.scaled_main_window import ScaledMainWindow
import os

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("DeltaMon - OptionDelta Monitor")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("TradingTools")

    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'app_icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        print(f"Warning: Application icon not found at {icon_path}")

    window = ScaledMainWindow()
    window.show()

    sys.exit(app.exec())