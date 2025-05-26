# Delta_Mon/core/monitoring_service.py

import time
import threading
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from core.window_manager import WindowManager
from core.tos_navigator import TosNavigator
from core.tab_detector import TabDetector
from core.delta_extractor import DeltaExtractor
from core.alert_manager import AlertManager
from utils.config_manager import ConfigManager
from utils.ocr_utils import OCRUtils


class MonitoringState(Enum):
    IDLE = "idle"
    DISCOVERING = "discovering"
    MONITORING = "monitoring"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class AccountMonitorData:
    """Data structure for tracking account monitoring status."""
    name: str
    tab_info: dict
    last_delta_value: Optional[float] = None
    last_check_time: Optional[datetime] = None
    error_count: int = 0
    status: str = "ready"


class MonitoringService:
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize monitoring service.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.alert_manager = AlertManager(config_manager)

        # Core components
        self.window_manager = WindowManager(
            target_exact_title="Main@thinkorswim [build 1985]",
            exclude_title_substring="DeltaMon"
        )
        self.tos_navigator = None
        self.tab_detector = None
        self.delta_extractor = None
        self.ocr_utils = OCRUtils()

        # Monitoring state
        self.state = MonitoringState.IDLE
        self.monitoring_thread = None
        self.stop_monitoring_flag = threading.Event()

        # Account data
        self.discovered_accounts: List[AccountMonitorData] = []
        self.scan_interval = config_manager.get_scan_interval()

        # Statistics
        self.total_scans = 0
        self.successful_scans = 0
        self.total_errors = 0

        # Status callback for UI updates
        self.status_callback: Optional[Callable] = None

        print(f"MonitoringService initialized with {self.scan_interval}s scan interval")

    def set_status_callback(self, callback: Callable):
        """Set callback function for status updates."""
        self.status_callback = callback

    def set_discord_webhook(self, webhook_url: str):
        """Set Discord webhook for alerts."""
        self.alert_manager.set_discord_webhook(webhook_url)

    def _update_status(self, message: str, account_name: str = None):
        """Update status and notify callback if set."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"

        if account_name:
            full_message = f"[{timestamp}] {account_name}: {message}"

        print(full_message)

        if self.status_callback:
            self.status_callback(full_message, account_name)

    def discover_accounts(self) -> bool:
        """
        Discover available accounts in ToS.

        Returns:
            True if discovery successful, False otherwise
        """
        self.state = MonitoringState.DISCOVERING
        self._update_status("Starting account discovery...")

        try:
            # Find ToS window
            tos_hwnd = self.window_manager.find_tos_window()
            if not tos_hwnd:
                self._update_status("ToS window not found")
                self.state = MonitoringState.ERROR
                return False

            # Focus ToS window
            if not self.window_manager.focus_tos_window():
                self._update_status("Warning: Could not focus ToS window")

            # Initialize navigation components
            self.tos_navigator = TosNavigator(tos_hwnd)
            self.tab_detector = TabDetector(self.tos_navigator)
            self.delta_extractor = DeltaExtractor(self.tos_navigator)

            # Discover accounts via dropdown
            self._update_status("Clicking account dropdown...")
            if not self.tos_navigator.click_account_dropdown():
                self._update_status("Failed to click account dropdown")
                self.state = MonitoringState.ERROR
                return False

            time.sleep(1.5)  # Wait for dropdown to appear

            # Capture and analyze dropdown
            self._update_status("Capturing dropdown list...")
            captured_image_path = self.tos_navigator.capture_dropdown_area()
            if not captured_image_path:
                self._update_status("Failed to capture dropdown area")
                self.state = MonitoringState.ERROR
                return False

            # Extract account names using OCR
            self._update_status("Extracting account names...")
            account_names = self.ocr_utils.extract_account_names(captured_image_path)

            if not account_names:
                self._update_status("No accounts found via OCR, using config fallback")
                account_names = self.config_manager.get_account_list()

            # Detect account tabs
            self._update_status("Detecting account tabs...")
            detected_tabs = self.tab_detector.detect_account_tabs()

            # Combine account names with tab information
            self.discovered_accounts = []
            for i, account_name in enumerate(account_names):
                if i < len(detected_tabs):
                    tab_info = detected_tabs[i]
                    tab_info['account_name'] = account_name
                else:
                    # Create placeholder tab info if we have more names than detected tabs
                    tab_info = {
                        'index': i,
                        'account_name': account_name,
                        'name': account_name,
                        'relative_x': 100 + (i * 120),  # Estimate position
                        'relative_y': 50,
                        'width': 120,
                        'height': 30,
                        'center_x': 160 + (i * 120),
                        'center_y': 65
                    }

                account_data = AccountMonitorData(
                    name=account_name,
                    tab_info=tab_info,
                    status="discovered"
                )
                self.discovered_accounts.append(account_data)

            # Update tab names with actual account names
            if detected_tabs:
                self.tab_detector.update_tab_names(detected_tabs, account_names)

            self._update_status(f"Discovery complete: {len(self.discovered_accounts)} accounts found")
            for account in self.discovered_accounts:
                self._update_status(f"Found account: {account.name}", account.name)

            self.state = MonitoringState.IDLE
            return True

        except Exception as e:
            self._update_status(f"Discovery error: {e}")
            self.state = MonitoringState.ERROR
            return False

    def start_monitoring(self) -> bool:
        """
        Start the monitoring process.

        Returns:
            True if monitoring started successfully
        """
        if not self.discovered_accounts:
            self._update_status("No accounts discovered. Run discovery first.")
            return False

        if self.state == MonitoringState.MONITORING:
            self._update_status("Monitoring already active")
            return True

        self.state = MonitoringState.MONITORING
        self.stop_monitoring_flag.clear()

        # Send startup notification
        account_names = [acc.name for acc in self.discovered_accounts]
        self.alert_manager.send_startup_notification(account_names)

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        self._update_status(f"Monitoring started for {len(self.discovered_accounts)} accounts")
        return True

    def stop_monitoring(self):
        """Stop the monitoring process."""
        if self.state != MonitoringState.MONITORING:
            self._update_status("Monitoring not active")
            return

        self._update_status("Stopping monitoring...")
        self.stop_monitoring_flag.set()

        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)  # Wait up to 10 seconds

        # Send shutdown notification
        self.alert_manager.send_shutdown_notification()

        self.state = MonitoringState.IDLE
        self._update_status("Monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop (runs in separate thread)."""
        self._update_status("Monitoring loop started")

        while not self.stop_monitoring_flag.is_set():
            try:
                scan_start_time = time.time()
                self.total_scans += 1

                # Monitor each account
                scan_successful = True
                for account in self.discovered_accounts:
                    if self.stop_monitoring_flag.is_set():
                        break

                    success = self._monitor_account(account)
                    if not success:
                        scan_successful = False

                if scan_successful:
                    self.successful_scans += 1

                # Calculate scan duration and wait for next interval
                scan_duration = time.time() - scan_start_time
                sleep_time = max(0, self.scan_interval - scan_duration)

                if scan_duration > self.scan_interval:
                    self._update_status(
                        f"Warning: Scan took {scan_duration:.1f}s (longer than {self.scan_interval}s interval)")

                # Sleep in small chunks to allow for responsive stopping
                sleep_chunks = int(sleep_time / 0.5) + 1
                for _ in range(sleep_chunks):
                    if self.stop_monitoring_flag.is_set():
                        break
                    time.sleep(min(0.5, sleep_time / sleep_chunks))

            except Exception as e:
                self.total_errors += 1
                self._update_status(f"Monitoring loop error: {e}")
                time.sleep(5)  # Brief pause before retrying

        self._update_status("Monitoring loop ended")

    def _monitor_account(self, account: AccountMonitorData) -> bool:
        """
        Monitor a single account for delta changes.

        Args:
            account: Account data to monitor

        Returns:
            True if monitoring successful, False otherwise
        """
        try:
            # Switch to the account's tab
            if not self.tab_detector.switch_to_tab(account.tab_info):
                self._update_status(f"Failed to switch to tab", account.name)
                account.error_count += 1
                account.status = "tab_switch_error"
                return False

            # Small delay for tab to load
            time.sleep(0.5)

            # Extract delta value
            delta_value = self.delta_extractor.extract_delta_value(account.name)

            if delta_value is not None:
                account.last_delta_value = delta_value
                account.last_check_time = datetime.now()
                account.error_count = 0  # Reset error count on success
                account.status = f"monitoring ({delta_value * 100:+.3f}%)"

                # Check threshold and trigger alerts if needed
                alert_triggered = self.alert_manager.check_delta_threshold(account.name, delta_value)

                if alert_triggered:
                    self._update_status(f"ALERT: {delta_value * 100:+.3f}%", account.name)

                return True
            else:
                account.error_count += 1
                account.status = f"extraction_error (#{account.error_count})"
                self._update_status(f"Failed to extract delta value", account.name)

                # If too many errors, mark account as problematic
                if account.error_count >= 5:
                    account.status = "multiple_errors"
                    self._update_status(f"Multiple extraction failures", account.name)

                return False

        except Exception as e:
            account.error_count += 1
            account.status = f"monitor_error (#{account.error_count})"
            self._update_status(f"Monitoring error: {e}", account.name)
            return False

    def get_monitoring_statistics(self) -> Dict[str, any]:
        """Get monitoring statistics."""
        alert_stats = self.alert_manager.get_alert_statistics()

        return {
            "state": self.state.value,
            "total_accounts": len(self.discovered_accounts),
            "total_scans": self.total_scans,
            "successful_scans": self.successful_scans,
            "total_errors": self.total_errors,
            "scan_interval": self.scan_interval,
            "success_rate": f"{(self.successful_scans / max(1, self.total_scans)) * 100:.1f}%",
            "alert_statistics": alert_stats,
            "account_status": [
                {
                    "name": acc.name,
                    "status": acc.status,
                    "last_delta": f"{acc.last_delta_value * 100:+.3f}%" if acc.last_delta_value else "N/A",
                    "last_check": acc.last_check_time.strftime("%H:%M:%S") if acc.last_check_time else "Never",
                    "error_count": acc.error_count
                }
                for acc in self.discovered_accounts
            ]
        }

    def get_discovered_accounts(self) -> List[AccountMonitorData]:
        """Get list of discovered accounts."""
        return self.discovered_accounts.copy()

    def is_monitoring_active(self) -> bool:
        """Check if monitoring is currently active."""
        return self.state == MonitoringState.MONITORING

    def get_current_state(self) -> MonitoringState:
        """Get current monitoring state."""
        return self.state


# Example usage
if __name__ == "__main__":
    from utils.config_manager import ConfigManager

    config = ConfigManager()
    monitoring_service = MonitoringService(config)

    # Set Discord webhook for testing
    webhook_url = "YOUR_DISCORD_WEBHOOK_URL_HERE"
    monitoring_service.set_discord_webhook(webhook_url)

    print("Testing monitoring service...")

    # Test discovery
    if monitoring_service.discover_accounts():
        print("✅ Account discovery successful")

        # Test monitoring for a short period
        if monitoring_service.start_monitoring():
            print("✅ Monitoring started")
            time.sleep(30)  # Monitor for 30 seconds
            monitoring_service.stop_monitoring()
            print("✅ Monitoring stopped")

            # Print statistics
            stats = monitoring_service.get_monitoring_statistics()
            print(f"Statistics: {stats}")
        else:
            print("❌ Failed to start monitoring")
    else:
        print("❌ Account discovery failed")