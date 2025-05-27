# Delta_Mon/setup_pradeep_config.py

"""
Setup configuration script for Pradeep's DeltaMon system.
This creates the initial configuration based on the OptionDelta values we saw in the screenshot.
"""

import configparser
import os
from typing import Dict, Any


def create_pradeep_config():
    """Create Pradeep's personalized configuration file."""
    print("🔧 Setting up DeltaMon configuration for Pradeep...")
    print("=" * 50)
    print()

    # Configuration file path
    config_file = "pradeep_config.ini"

    # Create configuration
    config = configparser.ConfigParser()

    # Alert Thresholds (based on the screenshot analysis)
    print("🎯 Setting up alert thresholds...")
    config['AlertThresholds'] = {
        'positive_threshold': '0.08',  # Alert when delta > +0.08 (8%)
        'negative_threshold': '-0.05',  # Alert when delta < -0.05 (-5%)
    }
    print(f"   • High delta alert: when delta > +0.08 (+8%)")
    print(f"   • Low delta alert: when delta < -0.05 (-5%)")

    # Alert Settings
    print("🔔 Configuring alert behavior...")
    config['AlertSettings'] = {
        'alert_cooldown_minutes': '5',  # 5 minutes between alerts per account
        'max_alerts_per_hour': '20',  # Maximum 20 alerts per hour
        'discord_webhook_url': '',  # To be filled in later
        'telegram_bot_token': '',  # For future Telegram integration
        'telegram_chat_id': '',  # For future Telegram integration
    }
    print(f"   • Alert cooldown: 5 minutes per account")
    print(f"   • Max alerts per hour: 20")

    # Monitoring Settings
    print("⚙️ Setting up monitoring parameters...")
    config['MonitoringSettings'] = {
        'scan_interval_seconds': '45',  # Scan every 45 seconds
        'fast_mode': 'false',  # Standard accuracy mode
        'parallel_scanning': 'true',  # Enable parallel scanning for multiple accounts
        'max_parallel_workers': '3',  # Up to 3 accounts scanned simultaneously
        'delta_column_name': 'OptionDelta',  # Exact column name from screenshot
        'save_debug_images': 'true',  # Save debug images for troubleshooting
        'max_consecutive_errors': '3',  # Max errors before marking account as problematic
        'account_scan_timeout': '10',  # Timeout per account scan in seconds
    }
    print(f"   • Scan interval: 45 seconds")
    print(f"   • Target column: OptionDelta")
    print(f"   • Parallel scanning: enabled")

    # OCR Settings
    print("👁️ Configuring OCR settings...")
    config['OCRSettings'] = {
        'tesseract_path': '',  # Auto-detect tesseract
        'confidence_threshold': '30',  # Minimum OCR confidence
        'enhance_images': 'true',  # Enhance images for better OCR
        'save_enhanced_images': 'true',  # Save enhanced images for debugging
        'ocr_timeout_seconds': '5',  # OCR timeout per image
    }
    print(f"   • OCR confidence threshold: 30%")
    print(f"   • Image enhancement: enabled")

    # Performance Settings
    print("🚀 Setting performance options...")
    config['PerformanceSettings'] = {
        'image_scale_factor': '3.0',  # Scale images for better OCR
        'cache_column_location': 'true',  # Cache column location between scans
        'max_cache_age_minutes': '30',  # Refresh cache every 30 minutes
        'screenshot_compression': '90',  # JPEG compression for debug images
        'cleanup_old_captures': 'true',  # Clean up old capture files
        'max_capture_files': '100',  # Keep max 100 capture files
    }
    print(f"   • Image scaling: 3x for better OCR")
    print(f"   • Column location caching: enabled")

    # Account Discovery Settings
    print("📋 Configuring account discovery...")
    config['AccountDiscovery'] = {
        'dropdown_capture_width': '350',  # Width of dropdown capture area
        'dropdown_capture_height': '500',  # Height for many accounts
        'dropdown_wait_time': '2.0',  # Wait time for dropdown to expand
        'ocr_methods': 'direct,line_by_line,enhanced',  # Multiple OCR methods
        'min_account_name_length': '3',  # Minimum valid account name length
        'max_account_name_length': '50',  # Maximum valid account name length
    }
    print(f"   • Dropdown capture: 350x500 pixels")
    print(f"   • Multiple OCR methods: enabled")

    # Thresholds Explanation
    print()
    print("📊 THRESHOLD EXPLANATION:")
    print("=" * 30)
    print("Based on your screenshot showing OptionDelta values:")
    print("   • Values like -0.19, -0.08 would trigger LOW alerts (< -0.05)")
    print("   • Values like +0.12, +0.15 would trigger HIGH alerts (> +0.08)")
    print("   • Values like -0.03, +0.05, 1.0 would be within safe range")
    print()

    # Write configuration to file
    print("💾 Saving configuration...")
    try:
        with open(config_file, 'w') as f:
            config.write(f)
        print(f"✅ Configuration saved to: {config_file}")
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

    # Create necessary directories
    print("📁 Creating necessary directories...")
    directories = [
        'assets',
        'assets/templates',
        'assets/captures',
        'assets/captures/dropdown',
        'assets/captures/portfolio',
        'assets/captures/delta_values',
        'debug_images',
        'logs'
    ]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"   ✅ {directory}/")
        except Exception as e:
            print(f"   ❌ Failed to create {directory}: {e}")

    print()
    print("🎉 SETUP COMPLETE!")
    print("=" * 20)
    print()
    print("🚀 NEXT STEPS:")
    print("1. 📋 Run: python test_dropdown_reading.py")
    print("   → Test account discovery from ToS dropdown")
    print()
    print("2. 🎯 Run: python test_optiondelta_extraction.py")
    print("   → Test OptionDelta column detection and value extraction")
    print()
    print("3. ⚙️ Run: python main.py")
    print("   → Start the main DeltaMon application")
    print("   → Use 'Setup Template' button for better dropdown detection")
    print("   → Use 'Read Accounts from Dropdown' to discover accounts")
    print("   → Configure Discord webhook in settings")
    print("   → Start monitoring!")
    print()
    print("📋 CONFIGURATION SUMMARY:")
    print(f"   • Config file: {config_file}")
    print(f"   • High delta threshold: +0.08 (+8%)")
    print(f"   • Low delta threshold: -0.05 (-5%)")
    print(f"   • Scan interval: 45 seconds")
    print(f"   • Target column: OptionDelta")
    print()
    print("💡 You can edit thresholds anytime in the main app or by editing the config file!")

    return True


def show_configuration_summary():
    """Show current configuration if file exists."""
    config_file = "pradeep_config.ini"

    if not os.path.exists(config_file):
        print(f"Configuration file {config_file} not found.")
        return

    print("📋 CURRENT CONFIGURATION:")
    print("=" * 30)

    try:
        config = configparser.ConfigParser()
        config.read(config_file)

        # Show key settings
        if config.has_section('AlertThresholds'):
            pos_thresh = config.get('AlertThresholds', 'positive_threshold', fallback='N/A')
            neg_thresh = config.get('AlertThresholds', 'negative_threshold', fallback='N/A')
            print(f"🎯 Alert Thresholds:")
            print(f"   • High delta alert: > +{pos_thresh}")
            print(f"   • Low delta alert: < {neg_thresh}")

        if config.has_section('MonitoringSettings'):
            scan_interval = config.get('MonitoringSettings', 'scan_interval_seconds', fallback='N/A')
            column_name = config.get('MonitoringSettings', 'delta_column_name', fallback='N/A')
            print(f"⚙️ Monitoring:")
            print(f"   • Scan interval: {scan_interval} seconds")
            print(f"   • Target column: {column_name}")

        if config.has_section('AlertSettings'):
            webhook = config.get('AlertSettings', 'discord_webhook_url', fallback='')
            webhook_status = "configured" if webhook else "not configured"
            cooldown = config.get('AlertSettings', 'alert_cooldown_minutes', fallback='N/A')
            print(f"🔔 Alerts:")
            print(f"   • Discord webhook: {webhook_status}")
            print(f"   • Cooldown: {cooldown} minutes")

    except Exception as e:
        print(f"Error reading configuration: {e}")


def main():
    """Main setup function."""
    print("🚀 DeltaMon Setup for Pradeep's Trading Operation")
    print("=" * 55)
    print()

    config_file = "pradeep_config.ini"

    if os.path.exists(config_file):
        print(f"⚠️ Configuration file {config_file} already exists.")
        print()
        show_configuration_summary()
        print()

        choice = input("Do you want to recreate the configuration? (y/n): ").lower().strip()
        if choice != 'y':
            print("Setup cancelled. Existing configuration preserved.")
            return
        print()

    # Create the configuration
    success = create_pradeep_config()

    if success:
        print()
        input("Press Enter to continue...")
    else:
        print("Setup failed. Please check the errors above and try again.")


if __name__ == "__main__":
    main()