# Delta_Mon/services/discord_service.py

import requests
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime


class DiscordService:
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Discord service.

        Args:
            webhook_url: Discord webhook URL for sending messages
        """
        self.webhook_url = webhook_url
        self.last_message_time = {}  # Rate limiting per account
        self.min_message_interval = 300  # 5 minutes between messages per account

    def set_webhook_url(self, webhook_url: str):
        """Set or update the Discord webhook URL."""
        self.webhook_url = webhook_url

    def send_delta_alert(self, account_name: str, delta_value: float, threshold: float,
                         alert_type: str = "threshold_exceeded") -> bool:
        """
        Send a delta threshold alert to Discord.

        Args:
            account_name: Name of the account
            delta_value: The delta value that triggered the alert
            threshold: The threshold that was exceeded
            alert_type: Type of alert (threshold_exceeded, error, etc.)

        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.webhook_url:
            print("Discord webhook URL not configured")
            return False

        # Rate limiting check
        now = time.time()
        last_sent = self.last_message_time.get(account_name, 0)
        if now - last_sent < self.min_message_interval:
            print(f"Rate limiting: Skipping Discord alert for {account_name} (last sent {int(now - last_sent)}s ago)")
            return False

        try:
            embed = self._create_delta_alert_embed(account_name, delta_value, threshold, alert_type)

            payload = {
                "embeds": [embed],
                "username": "DeltaMon Bot"
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code == 204:
                print(f"✅ Discord alert sent successfully for {account_name}")
                self.last_message_time[account_name] = now
                return True
            else:
                print(f"❌ Discord webhook failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error sending Discord alert: {e}")
            return False

    def _create_delta_alert_embed(self, account_name: str, delta_value: float,
                                  threshold: float, alert_type: str) -> Dict[str, Any]:
        """
        Create a Discord embed for delta alerts.

        Args:
            account_name: Account name
            delta_value: Delta value
            threshold: Threshold value
            alert_type: Type of alert

        Returns:
            Discord embed dictionary
        """
        # Determine alert color and emoji based on delta value
        if delta_value > 0:
            color = 0x00ff00  # Green for positive
            emoji = "📈"
            direction = "above"
        else:
            color = 0xff0000  # Red for negative
            emoji = "📉"
            direction = "below"

        # Format percentage values
        delta_percent = f"{delta_value * 100:+.3f}%"
        threshold_percent = f"{abs(threshold) * 100:.3f}%"

        timestamp = datetime.utcnow().isoformat()

        embed = {
            "title": f"{emoji} Delta Alert - {account_name}",
            "description": f"Delta value {direction} threshold!",
            "color": color,
            "fields": [
                {
                    "name": "Account",
                    "value": f"```{account_name}```",
                    "inline": True
                },
                {
                    "name": "Delta Value",
                    "value": f"```{delta_percent}```",
                    "inline": True
                },
                {
                    "name": "Threshold",
                    "value": f"```±{threshold_percent}```",
                    "inline": True
                }
            ],
            "footer": {
                "text": "DeltaMon • Pradeep's Trading Monitor"
            },
            "timestamp": timestamp
        }

        return embed

    def send_system_message(self, message: str, message_type: str = "info") -> bool:
        """
        Send a system status message to Discord.

        Args:
            message: Message content
            message_type: Type of message (info, warning, error, success)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.webhook_url:
            return False

        try:
            # Color coding for different message types
            colors = {
                "info": 0x3498db,  # Blue
                "warning": 0xf39c12,  # Orange
                "error": 0xe74c3c,  # Red
                "success": 0x2ecc71  # Green
            }

            emojis = {
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "success": "✅"
            }

            embed = {
                "title": f"{emojis.get(message_type, '📢')} DeltaMon System",
                "description": message,
                "color": colors.get(message_type, 0x95a5a6),
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "DeltaMon System"
                }
            }

            payload = {
                "embeds": [embed],
                "username": "DeltaMon System"
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            return response.status_code == 204

        except Exception as e:
            print(f"Error sending Discord system message: {e}")
            return False

    def send_startup_message(self, accounts: list) -> bool:
        """
        Send a startup notification with discovered accounts.

        Args:
            accounts: List of discovered account names

        Returns:
            True if sent successfully
        """
        account_list = "\n".join([f"• {acc}" for acc in accounts])
        if not account_list:
            account_list = "No accounts discovered"

        message = f"🚀 **DeltaMon Started**\n\n**Monitoring Accounts:**\n{account_list}\n\n*Ready to monitor delta thresholds...*"
        return self.send_system_message(message, "success")

    def send_shutdown_message(self) -> bool:
        """Send a shutdown notification."""
        message = "🛑 **DeltaMon Stopped**\n\nMonitoring has been stopped."
        return self.send_system_message(message, "warning")

    def test_webhook(self) -> bool:
        """
        Test the Discord webhook connection.

        Returns:
            True if webhook is working, False otherwise
        """
        if not self.webhook_url:
            print("No Discord webhook URL configured")
            return False

        test_message = "🧪 **DeltaMon Test**\n\nDiscord webhook is working correctly!"
        return self.send_system_message(test_message, "info")


# Example usage and testing
if __name__ == "__main__":
    # For testing - replace with your actual webhook URL
    webhook_url = "YOUR_DISCORD_WEBHOOK_URL_HERE"

    discord = DiscordService(webhook_url)

    # Test basic functionality
    if discord.test_webhook():
        print("✅ Discord webhook test successful")

        # Test alert message
        discord.send_delta_alert("TestAccount", 0.0012, 0.0008, "threshold_exceeded")

        # Test system messages
        discord.send_startup_message(["Account1", "Account2", "TestAccount"])

    else:
        print("❌ Discord webhook test failed")