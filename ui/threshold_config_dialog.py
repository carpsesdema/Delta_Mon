from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QDoubleSpinBox, QLabel, QGroupBox,
    QSpinBox, QCheckBox, QLineEdit, QTextEdit,
    QMessageBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import configparser
import os


class ThresholdConfigDialog(QDialog):
    config_saved = Signal(dict)

    def __init__(self, parent=None, config_file="pradeep_config.ini"):
        super().__init__(parent)
        self.config_file = config_file
        self.setWindowTitle("⚙️ Configure Alert Settings")
        self.setFixedSize(500, 600)

        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
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
            QLabel {
                color: #ffffff;
                padding: 2px;
            }
            QDoubleSpinBox, QSpinBox, QLineEdit {
                background-color: #4a4a4a;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 4px;
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
            QPushButton#saveButton {
                background-color: #27ae60;
            }
            QPushButton#saveButton:hover {
                background-color: #2ecc71;
            }
            QPushButton#testButton {
                background-color: #3498db;
            }
            QPushButton#testButton:hover {
                background-color: #5dade2;
            }
            QTextEdit {
                background-color: #3c3c3c;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
        """)

        self.setup_ui()
        self.load_current_config()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        tab_widget = QTabWidget()

        thresholds_tab = self.create_thresholds_tab()
        tab_widget.addTab(thresholds_tab, "🚨 Alert Thresholds")

        monitoring_tab = self.create_monitoring_tab()
        tab_widget.addTab(monitoring_tab, "⚙️ Monitoring")

        discord_tab = self.create_discord_tab()
        tab_widget.addTab(discord_tab, "🔔 Discord")

        layout.addWidget(tab_widget)

        button_layout = QHBoxLayout()

        self.test_button = QPushButton("🧪 Test Thresholds")
        self.test_button.setObjectName("testButton")
        self.test_button.clicked.connect(self.test_thresholds)
        button_layout.addWidget(self.test_button)

        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        self.save_button = QPushButton("💾 Save Settings")
        self.save_button.setObjectName("saveButton")
        self.save_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

    def create_thresholds_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        thresholds_group = QGroupBox("🎯 Delta Alert Thresholds")
        thresholds_layout = QFormLayout(thresholds_group)

        self.positive_threshold_spin = QDoubleSpinBox()
        self.positive_threshold_spin.setRange(0.001, 1.0)
        self.positive_threshold_spin.setDecimals(3)
        self.positive_threshold_spin.setSingleStep(0.01)
        self.positive_threshold_spin.setValue(0.08)
        self.positive_threshold_spin.setSuffix("")
        thresholds_layout.addRow("🔥 High Delta Alert (when delta >):", self.positive_threshold_spin)

        self.negative_threshold_spin = QDoubleSpinBox()
        self.negative_threshold_spin.setRange(-1.0, -0.001)
        self.negative_threshold_spin.setDecimals(3)
        self.negative_threshold_spin.setSingleStep(0.01)
        self.negative_threshold_spin.setValue(-0.05)
        self.negative_threshold_spin.setSuffix("")
        thresholds_layout.addRow("❄️ Low Delta Alert (when delta <):", self.negative_threshold_spin)

        layout.addWidget(thresholds_group)

        examples_group = QGroupBox("📊 Examples")
        examples_layout = QVBoxLayout(examples_group)

        self.examples_text = QTextEdit()
        self.examples_text.setMaximumHeight(120)
        self.examples_text.setReadOnly(True)
        examples_layout.addWidget(self.examples_text)

        layout.addWidget(examples_group)

        self.positive_threshold_spin.valueChanged.connect(self.update_examples)
        self.negative_threshold_spin.valueChanged.connect(self.update_examples)

        behavior_group = QGroupBox("🔔 Alert Behavior")
        behavior_layout = QFormLayout(behavior_group)

        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(1, 60)
        self.cooldown_spin.setValue(5)
        self.cooldown_spin.setSuffix(" minutes")
        behavior_layout.addRow("Cooldown between alerts:", self.cooldown_spin)

        self.max_alerts_spin = QSpinBox()
        self.max_alerts_spin.setRange(5, 100)
        self.max_alerts_spin.setValue(20)
        self.max_alerts_spin.setSuffix(" per hour")
        behavior_layout.addRow("Maximum alerts per hour:", self.max_alerts_spin)

        layout.addWidget(behavior_group)

        layout.addStretch()

        self.update_examples()

        return tab

    def create_monitoring_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        scan_group = QGroupBox("⏱️ Scan Settings")
        scan_layout = QFormLayout(scan_group)

        self.scan_interval_spin = QSpinBox()
        self.scan_interval_spin.setRange(10, 300)
        self.scan_interval_spin.setValue(45)
        self.scan_interval_spin.setSuffix(" seconds")
        scan_layout.addRow("Scan interval:", self.scan_interval_spin)

        self.fast_mode_check = QCheckBox("Enable fast mode (skip some validations)")
        scan_layout.addRow("Fast mode:", self.fast_mode_check)

        self.parallel_check = QCheckBox("Enable parallel scanning (faster for 25 accounts)")
        self.parallel_check.setChecked(True)
        scan_layout.addRow("Parallel scanning:", self.parallel_check)

        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 5)
        self.max_workers_spin.setValue(3)
        scan_layout.addRow("Max parallel workers:", self.max_workers_spin)

        layout.addWidget(scan_group)

        delta_group = QGroupBox("📊 Delta Extraction")
        delta_layout = QFormLayout(delta_group)

        self.column_name_edit = QLineEdit()
        self.column_name_edit.setText("OptionDelta")
        delta_layout.addRow("Column name to look for:", self.column_name_edit)

        self.save_debug_check = QCheckBox("Save debug images for troubleshooting")
        self.save_debug_check.setChecked(True)
        delta_layout.addRow("Debug images:", self.save_debug_check)

        layout.addWidget(delta_group)

        error_group = QGroupBox("⚠️ Error Handling")
        error_layout = QFormLayout(error_group)

        self.max_errors_spin = QSpinBox()
        self.max_errors_spin.setRange(1, 10)
        self.max_errors_spin.setValue(3)
        error_layout.addRow("Max consecutive errors per account:", self.max_errors_spin)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 30)
        self.timeout_spin.setValue(10)
        self.timeout_spin.setSuffix(" seconds")
        error_layout.addRow("Account scan timeout:", self.timeout_spin)

        layout.addWidget(error_group)

        layout.addStretch()

        return tab

    def create_discord_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        discord_group = QGroupBox("🔔 Discord Integration")
        discord_layout = QFormLayout(discord_group)

        self.webhook_url_edit = QLineEdit()
        self.webhook_url_edit.setPlaceholderText("https://discord.com/api/webhooks/...")
        discord_layout.addRow("Webhook URL:", self.webhook_url_edit)

        self.test_webhook_button = QPushButton("🧪 Test Webhook")
        self.test_webhook_button.clicked.connect(self.test_discord_webhook)
        discord_layout.addRow("", self.test_webhook_button)

        layout.addWidget(discord_group)

        message_group = QGroupBox("💬 Message Settings")
        message_layout = QFormLayout(message_group)

        self.include_screenshot_check = QCheckBox("Include screenshots in alerts")
        message_layout.addRow("Screenshots:", self.include_screenshot_check)

        self.include_stats_check = QCheckBox("Include performance stats in alerts")
        self.include_stats_check.setChecked(True)
        message_layout.addRow("Performance stats:", self.include_stats_check)

        layout.addWidget(message_group)

        layout.addStretch()

        return tab

    def update_examples(self):
        pos_thresh = self.positive_threshold_spin.value()
        neg_thresh = self.negative_threshold_spin.value()

        examples = f"""Examples with current thresholds:

Delta = +{pos_thresh + 0.01:.3f} → 🚨 HIGH DELTA ALERT (above +{pos_thresh:.3f})
Delta = +{pos_thresh - 0.01:.3f} → ✅ No alert (below +{pos_thresh:.3f})
Delta = +0.000 → ✅ No alert (between thresholds)
Delta = {neg_thresh + 0.01:.3f} → ✅ No alert (above {neg_thresh:.3f})
Delta = {neg_thresh - 0.01:.3f} → 🚨 LOW DELTA ALERT (below {neg_thresh:.3f})

Safe zone: {neg_thresh:.3f} < delta < +{pos_thresh:.3f}"""

        self.examples_text.setPlainText(examples)

    def test_thresholds(self):
        pos_thresh = self.positive_threshold_spin.value()
        neg_thresh = self.negative_threshold_spin.value()

        test_values = [
            pos_thresh + 0.01,
            pos_thresh - 0.01,
            0.0,
            neg_thresh + 0.01,
            neg_thresh - 0.01,
        ]

        results = []
        for value in test_values:
            if value > pos_thresh:
                result = "🚨 HIGH DELTA ALERT"
            elif value < neg_thresh:
                result = "🚨 LOW DELTA ALERT"
            else:
                result = "✅ No alert"

            results.append(f"Delta {value:+.3f} → {result}")

        test_text = "🧪 Threshold Test Results:\n\n" + "\n".join(results)

        QMessageBox.information(self, "Threshold Test", test_text)

    def test_discord_webhook(self):
        webhook_url = self.webhook_url_edit.text().strip()

        if not webhook_url:
            QMessageBox.information(self, "Missing Webhook",
                                    "Please enter a Discord webhook URL first.")
            return

        try:
            from services.discord_service import DiscordService

            discord = DiscordService(webhook_url)
            success = discord.test_webhook()

            if success:
                QMessageBox.information(self, "Webhook Test",
                                        "✅ Discord webhook test successful!\n\n"
                                        "Check your Discord channel for the test message.")
            else:
                QMessageBox.information(self, "Webhook Test Failed",
                                        "❌ Discord webhook test failed.\n\n"
                                        "Please check:\n"
                                        "• Webhook URL is correct\n"
                                        "• Internet connection\n"
                                        "• Discord server permissions")

        except Exception as e:
            QMessageBox.information(self, "Webhook Test Error",
                                    f"❌ Error testing webhook:\n\n{str(e)}")

    def load_current_config(self):
        if not os.path.exists(self.config_file):
            return

        try:
            config = configparser.ConfigParser()
            config.read(self.config_file)

            if config.has_section('AlertThresholds'):
                pos_thresh = config.getfloat('AlertThresholds', 'positive_threshold', fallback=0.08)
                neg_thresh = config.getfloat('AlertThresholds', 'negative_threshold', fallback=-0.05)

                self.positive_threshold_spin.setValue(pos_thresh)
                self.negative_threshold_spin.setValue(neg_thresh)

            if config.has_section('AlertSettings'):
                cooldown = config.getint('AlertSettings', 'alert_cooldown_minutes', fallback=5)
                max_alerts = config.getint('AlertSettings', 'max_alerts_per_hour', fallback=20)

                self.cooldown_spin.setValue(cooldown)
                self.max_alerts_spin.setValue(max_alerts)

                webhook_url = config.get('AlertSettings', 'discord_webhook_url', fallback='')
                self.webhook_url_edit.setText(webhook_url)

            if config.has_section('MonitoringSettings'):
                scan_interval = config.getint('MonitoringSettings', 'scan_interval_seconds', fallback=45)
                fast_mode = config.getboolean('MonitoringSettings', 'fast_mode', fallback=False)
                parallel = config.getboolean('MonitoringSettings', 'parallel_scanning', fallback=True)
                max_workers = config.getint('MonitoringSettings', 'max_parallel_workers', fallback=3)

                self.scan_interval_spin.setValue(scan_interval)
                self.fast_mode_check.setChecked(fast_mode)
                self.parallel_check.setChecked(parallel)
                self.max_workers_spin.setValue(max_workers)

                column_name = config.get('MonitoringSettings', 'delta_column_name', fallback='OptionDelta')
                self.column_name_edit.setText(column_name)

            print(f"✅ Loaded configuration from {self.config_file}")

        except Exception as e:
            print(f"⚠️ Error loading config: {e}")

    def save_config(self):
        try:
            config = configparser.ConfigParser()

            if os.path.exists(self.config_file):
                config.read(self.config_file)

            if not config.has_section('AlertThresholds'):
                config.add_section('AlertThresholds')

            config.set('AlertThresholds', 'positive_threshold', str(self.positive_threshold_spin.value()))
            config.set('AlertThresholds', 'negative_threshold', str(self.negative_threshold_spin.value()))

            if not config.has_section('AlertSettings'):
                config.add_section('AlertSettings')

            config.set('AlertSettings', 'alert_cooldown_minutes', str(self.cooldown_spin.value()))
            config.set('AlertSettings', 'max_alerts_per_hour', str(self.max_alerts_spin.value()))
            config.set('AlertSettings', 'discord_webhook_url', self.webhook_url_edit.text().strip())

            if not config.has_section('MonitoringSettings'):
                config.add_section('MonitoringSettings')

            config.set('MonitoringSettings', 'scan_interval_seconds', str(self.scan_interval_spin.value()))
            config.set('MonitoringSettings', 'fast_mode', str(self.fast_mode_check.isChecked()))
            config.set('MonitoringSettings', 'parallel_scanning', str(self.parallel_check.isChecked()))
            config.set('MonitoringSettings', 'max_parallel_workers', str(self.max_workers_spin.value()))
            config.set('MonitoringSettings', 'delta_column_name', self.column_name_edit.text().strip())

            with open(self.config_file, 'w') as f:
                config.write(f)

            config_dict = {
                'positive_threshold': self.positive_threshold_spin.value(),
                'negative_threshold': self.negative_threshold_spin.value(),
                'cooldown_minutes': self.cooldown_spin.value(),
                'max_alerts_per_hour': self.max_alerts_spin.value(),
                'discord_webhook_url': self.webhook_url_edit.text().strip(),
                'scan_interval': self.scan_interval_spin.value(),
                'fast_mode': self.fast_mode_check.isChecked(),
                'parallel_scanning': self.parallel_check.isChecked(),
                'max_workers': self.max_workers_spin.value(),
                'delta_column_name': self.column_name_edit.text().strip()
            }

            self.config_saved.emit(config_dict)

            QMessageBox.information(self, "Settings Saved",
                                    f"✅ Configuration saved successfully!\n\n"
                                    f"Settings saved to: {self.config_file}")

            self.accept()

        except Exception as e:
            QMessageBox.information(self, "Save Error",
                                    f"❌ Error saving configuration:\n\n{str(e)}")


class ConfigurableAlertManager:

    def __init__(self, config_file="pradeep_config.ini"):
        self.config_file = config_file
        self.reload_config()

    def reload_config(self):
        self.config = configparser.ConfigParser()

        if os.path.exists(self.config_file):
            self.config.read(self.config_file)

        self.positive_threshold = self.config.getfloat('AlertThresholds', 'positive_threshold', fallback=0.08)
        self.negative_threshold = self.config.getfloat('AlertThresholds', 'negative_threshold', fallback=-0.05)

        self.cooldown_minutes = self.config.getint('AlertSettings', 'alert_cooldown_minutes', fallback=5)
        self.webhook_url = self.config.get('AlertSettings', 'discord_webhook_url', fallback='')

        print(f"🔧 Config reloaded: +{self.positive_threshold} / {self.negative_threshold}")

    def show_config_dialog(self, parent=None):
        dialog = ThresholdConfigDialog(parent, self.config_file)
        dialog.config_saved.connect(self.on_config_saved)
        return dialog.exec()

    def on_config_saved(self, config_dict):
        self.reload_config()
        print(f"✅ Configuration updated: {config_dict}")

    def check_threshold(self, account_name: str, delta_value: float) -> tuple:
        if delta_value > self.positive_threshold:
            return True, "HIGH_DELTA", self.positive_threshold
        elif delta_value < self.negative_threshold:
            return True, "LOW_DELTA", self.negative_threshold
        else:
            return False, "NO_ALERT", None


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = ThresholdConfigDialog()

    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Configuration saved!")
    else:
        print("Configuration cancelled.")

    sys.exit()