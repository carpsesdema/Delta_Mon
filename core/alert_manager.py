# Delta_Mon/core/alert_manager.py

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from services.discord_service import DiscordService
from utils.config_manager import ConfigManager


@dataclass
class AlertHistory:
    """Track alert history for rate limiting and logging."""
    account_name: str
    delta_value: float
    threshold: float
    timestamp: datetime
    alert_sent: bool


class AlertManager:
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize alert manager.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.discord_service = DiscordService()

        # Load thresholds from config
        self.positive_threshold, self.negative_threshold = config_manager.get_delta_thresholds()

        # Alert tracking
        self.alert_history: List[AlertHistory] = []
        self.last_alert_time: Dict[str, datetime] = {}
        self.alert_cooldown_minutes = 5  # Minimum time between alerts per account

        # Statistics
        self.total_alerts_sent = 0
        self.alerts_by_account: Dict[str, int] = {}

        print(
            f"AlertManager initialized with thresholds: +{self.positive_threshold * 100:.3f}% / {self.negative_threshold * 100:.3f}%")

    def set_discord_webhook(self, webhook_url: str):
        """Set Discord webhook URL for alerts."""
        self.discord_service.set_webhook_url(webhook_url)
        print(f"Discord webhook configured for alerts")

    def check_delta_threshold(self, account_name: str, delta_value: float) -> bool:
        """
        Check if delta value exceeds threshold and trigger alert if needed.

        Args:
            account_name: Name of the account
            delta_value: Current delta value

        Returns:
            True if alert was triggered, False otherwise
        """
        threshold_exceeded = False
        exceeded_threshold = 0.0

        # Check positive threshold
        if delta_value > self.positive_threshold:
            threshold_exceeded = True
            exceeded_threshold = self.positive_threshold

        # Check negative threshold
        elif delta_value < self.negative_threshold:
            threshold_exceeded = True
            exceeded_threshold = self.negative_threshold

        if threshold_exceeded:
            print(
                f"⚠️ Threshold exceeded for {account_name}: {delta_value * 100:+.3f}% (threshold: ±{abs(exceeded_threshold) * 100:.3f}%)")
            return self._trigger_alert(account_name, delta_value, exceeded_threshold)
        else:
            # Log normal readings occasionally for debugging
            if int(time.time()) % 30 == 0:  # Every 30 seconds
                print(
                    f"✅ {account_name}: {delta_value * 100:+.3f}% (within ±{abs(self.positive_threshold) * 100:.3f}%)")

        return False

    def _trigger_alert(self, account_name: str, delta_value: float, threshold: float) -> bool:
        """
        Trigger an alert for threshold exceedance.

        Args:
            account_name: Account name
            delta_value: Delta value that exceeded threshold
            threshold: The threshold that was exceeded

        Returns:
            True if alert was sent, False if skipped due to cooldown
        """
        now = datetime.now()

        # Check cooldown period
        if self._is_in_cooldown(account_name, now):
            cooldown_remaining = self._get_cooldown_remaining(account_name, now)
            print(f"🕐 Alert cooldown active for {account_name} ({cooldown_remaining:.1f}m remaining)")

            # Log the event even if we don't send alert
            self._log_alert_history(account_name, delta_value, threshold, alert_sent=False)
            return False

        # Send the alert
        alert_sent = self.discord_service.send_delta_alert(
            account_name=account_name,
            delta_value=delta_value,
            threshold=threshold,
            alert_type="threshold_exceeded"
        )

        if alert_sent:
            self.last_alert_time[account_name] = now
            self.total_alerts_sent += 1
            self.alerts_by_account[account_name] = self.alerts_by_account.get(account_name, 0) + 1

            print(f"🚨 Alert sent for {account_name}: {delta_value * 100:+.3f}%")
        else:
            print(f"❌ Failed to send alert for {account_name}")

        # Log the alert attempt
        self._log_alert_history(account_name, delta_value, threshold, alert_sent)

        return alert_sent

    def _is_in_cooldown(self, account_name: str, current_time: datetime) -> bool:
        """Check if account is in alert cooldown period."""
        if account_name not in self.last_alert_time:
            return False

        last_alert = self.last_alert_time[account_name]
        cooldown_period = timedelta(minutes=self.alert_cooldown_minutes)

        return current_time - last_alert < cooldown_period

    def _get_cooldown_remaining(self, account_name: str, current_time: datetime) -> float:
        """Get remaining cooldown time in minutes."""
        if account_name not in self.last_alert_time:
            return 0.0

        last_alert = self.last_alert_time[account_name]
        cooldown_period = timedelta(minutes=self.alert_cooldown_minutes)
        elapsed = current_time - last_alert

        if elapsed >= cooldown_period:
            return 0.0

        remaining = cooldown_period - elapsed
        return remaining.total_seconds() / 60.0

    def _log_alert_history(self, account_name: str, delta_value: float,
                           threshold: float, alert_sent: bool):
        """Log alert to history for tracking and analysis."""
        alert_record = AlertHistory(
            account_name=account_name,
            delta_value=delta_value,
            threshold=threshold,
            timestamp=datetime.now(),
            alert_sent=alert_sent
        )

        self.alert_history.append(alert_record)

        # Keep only last 1000 alerts to prevent memory bloat
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

    def get_alert_statistics(self) -> Dict[str, any]:
        """Get statistics about alerts sent."""
        return {
            "total_alerts_sent": self.total_alerts_sent,
            "alerts_by_account": self.alerts_by_account.copy(),
            "total_threshold_events": len(self.alert_history),
            "current_thresholds": {
                "positive": f"{self.positive_threshold * 100:.3f}%",
                "negative": f"{self.negative_threshold * 100:.3f}%"
            },
            "cooldown_minutes": self.alert_cooldown_minutes
        }

    def update_thresholds(self, positive_threshold: float, negative_threshold: float):
        """Update alert thresholds."""
        self.positive_threshold = positive_threshold
        self.negative_threshold = negative_threshold
        print(f"Alert thresholds updated: +{positive_threshold * 100:.3f}% / {negative_threshold * 100:.3f}%")

    def send_startup_notification(self, accounts: List[str]):
        """Send startup notification via Discord."""
        if self.discord_service.webhook_url:
            self.discord_service.send_startup_message(accounts)

    def send_shutdown_notification(self):
        """Send shutdown notification via Discord."""
        if self.discord_service.webhook_url:
            self.discord_service.send_shutdown_message()

    def test_alert_system(self) -> bool:
        """Test the alert system."""
        print("Testing alert system...")

        # Test Discord webhook
        webhook_test = self.discord_service.test_webhook()
        if webhook_test:
            print("✅ Discord webhook test passed")

            # Send a test alert
            test_result = self.discord_service.send_delta_alert(
                account_name="TEST_ACCOUNT",
                delta_value=0.0015,  # Above typical threshold
                threshold=0.0008,
                alert_type="system_test"
            )

            if test_result:
                print("✅ Test alert sent successfully")
                return True
            else:
                print("❌ Test alert failed to send")
                return False
        else:
            print("❌ Discord webhook test failed")
            return False


# Example usage
if __name__ == "__main__":
    from utils.config_manager import ConfigManager

    config = ConfigManager()
    alert_manager = AlertManager(config)

    # Test with sample values
    alert_manager.set_discord_webhook("YOUR_WEBHOOK_URL_HERE")

    # Test threshold checking
    test_accounts = ["TestAccount1", "TestAccount2"]
    test_deltas = [0.0005, 0.0012, -0.0015, 0.0003]  # Some above/below threshold

    for account in test_accounts:
        for delta in test_deltas:
            alert_manager.check_delta_threshold(account, delta)
            time.sleep(1)  # Small delay between tests

    # Print statistics
    stats = alert_manager.get_alert_statistics()
    print(f"Alert Statistics: {stats}")