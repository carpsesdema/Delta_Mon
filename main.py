# Delta_Mon/main.py

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # The stylesheet is applied within MainWindow in this version
    # If you later move QSS to ui/styles.py and want to apply it globally:
    # from ui.styles import DARK_THEME_QSS
    # app.setStyleSheet(DARK_THEME_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())