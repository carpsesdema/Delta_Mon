# Delta_Mon/utils/config_manager.py

import configparser
import os


class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()

        if not os.path.exists(self.config_file):
            self._create_default_config()

        self.config.read(self.config_file)

    def _create_default_config(self):
        """Creates a default config file if one doesn't exist."""
        self.config['Accounts'] = {
            'list': '\nAccount1\nAccount2'  # Default example accounts
        }
        self.config['Settings'] = {
            'scan_interval_seconds': '60',
            'delta_threshold_positive': '0.0008',  # Example: 0.08%
            'delta_threshold_negative': '-0.0008'  # Example: -0.08%
        }
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        print(f"Default configuration file created at {self.config_file}")

    def get_account_list(self) -> list[str]:
        """Retrieves the list of accounts from the config file."""
        try:
            accounts_str = self.config.get('Accounts', 'list', fallback='')
            # Split by newline, filter out empty strings, and strip whitespace
            account_list = [acc.strip() for acc in accounts_str.splitlines() if acc.strip()]
            return account_list
        except (configparser.NoSectionError, configparser.NoOptionError):
            return []

    def get_setting(self, section: str, option: str, fallback=None):
        """Retrieves a specific setting."""
        return self.config.get(section, option, fallback=fallback)

    # Example of how to get specific typed settings
    def get_scan_interval(self) -> int:
        return self.config.getint('Settings', 'scan_interval_seconds', fallback=60)

    def get_delta_thresholds(self) -> tuple[float, float]:
        positive = self.config.getfloat('Settings', 'delta_threshold_positive', fallback=0.0008)
        negative = self.config.getfloat('Settings', 'delta_threshold_negative', fallback=-0.0008)
        return positive, negative


# Example usage (optional, for testing this module directly)
if __name__ == '__main__':
    config_manager = ConfigManager()
    accounts = config_manager.get_account_list()
    print("Configured Accounts:", accounts)

    interval = config_manager.get_scan_interval()
    print(f"Scan Interval: {interval} seconds")

    pos_thresh, neg_thresh = config_manager.get_delta_thresholds()
    print(f"Delta Thresholds: +{pos_thresh * 100:.2f}% / {neg_thresh * 100:.2f}%")

    # Create a dummy config if it doesn't exist for the test
    if not accounts:
        print("No accounts found, check your config.ini")