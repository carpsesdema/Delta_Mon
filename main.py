# Delta_Mon/main.py

import sys
from PySide6.QtWidgets import QApplication
from ui.scaled_main_window import ScaledMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("DeltaMon - OptionDelta Monitor")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("TradingTools")

    # Create and show the main window
    window = ScaledMainWindow()
    window.show()

    # Set up proper application exit
    sys.exit(app.exec())