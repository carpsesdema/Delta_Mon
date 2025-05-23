# Delta_Mon/ui/styles.py

DARK_THEME_QSS = """
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
        min-height: 20px;
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
        background-color: #5a6370;
        color: #ffffff;
    }
    QLabel {
        padding: 2px; /* General padding for labels */
    }
    QLabel#statusLabel { /* Specific styling for the status label */
        font-weight: bold;
        padding: 5px;
        color: #cccccc; /* Lighter grey for less emphasis than pure white */
        border: 1px solid #4a4a4a; /* Optional: give it a subtle border */
        border-radius: 3px;
        background-color: #333333; /* Slightly different background */
    }
"""