# Delta_Mon/test_dropdown_reading.py

"""
Test script specifically for testing dropdown reading with Pradeep's accounts.
Run this to verify the dropdown detection and account extraction works properly.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.enhanced_dropdown_reader import DropdownAccountDiscovery
import time


def test_dropdown_reading():
    """Test the dropdown reading functionality for accounts."""
    print("🧪 Testing Dropdown Reading for Account Discovery")
    print("=" * 60)
    print()

    print("📋 Prerequisites for this test:")
    print("   ✅ Thinkorswim must be running")
    print("   ✅ ToS window should be visible (not minimized)")
    print("   ✅ Account dropdown should be in the upper-left area")
    print("   ✅ All accounts should be loaded and accessible")
    print("   ✅ Make sure you can manually click the dropdown and see all accounts")
    print()

    input("Press Enter when ToS is ready and you've verified the dropdown works manually...")
    print()

    # Initialize dropdown discovery
    print("🔧 Initializing dropdown discovery system...")
    discovery = DropdownAccountDiscovery()

    # Status callback for real-time updates
    def status_update(message):
        print(f"   {message}")

    print()
    print("🚀 Starting dropdown reading test...")
    print("-" * 50)

    try:
        # Run discovery
        start_time = time.time()
        discovered_accounts = discovery.discover_all_accounts(status_callback=status_update)
        end_time = time.time()

        print("-" * 50)
        print()

        if discovered_accounts:
            account_count = len(discovered_accounts)
            print(f"✅ SUCCESS! Found {account_count} accounts in {end_time - start_time:.1f} seconds")
            print()

            # Display all found accounts
            print("📋 Complete account list:")
            for i, account in enumerate(discovered_accounts, 1):
                print(f"   {i:2d}. {account}")

            print()

            # Analysis
            print("📊 ANALYSIS:")
            print("=" * 30)

            if account_count >= 20:
                print("🎉 EXCELLENT: Found 20+ accounts - perfect for large-scale monitoring!")
            elif account_count >= 15:
                print("👍 GREAT: Found 15+ accounts - excellent for monitoring!")
            elif account_count >= 10:
                print("✅ GOOD: Found 10+ accounts - solid for monitoring")
            elif account_count >= 5:
                print("⚡ DECENT: Found 5+ accounts - good start")
            elif account_count >= 3:
                print("⚠️ PARTIAL: Found some accounts but may be missing some")
            else:
                print("❌ LIMITED: Found few accounts - likely OCR or detection issues")

            print()
            print("📈 QUALITY METRICS:")

            # Check for obviously valid account names
            valid_looking = 0
            for account in discovered_accounts:
                if len(account) >= 3 and any(c.isalnum() for c in account):
                    valid_looking += 1

            print(
                f"   • Valid-looking names: {valid_looking}/{account_count} ({valid_looking / account_count * 100:.1f}%)")

            # Check for duplicates
            unique_count = len(set(discovered_accounts))
            print(f"   • Unique accounts: {unique_count}/{account_count}")

            # Check name lengths
            avg_length = sum(len(name) for name in discovered_accounts) / account_count
            print(f"   • Average name length: {avg_length:.1f} characters")

            print()
            print("💡 RECOMMENDATIONS:")

            if account_count < 15:
                print("   • Check if all accounts are loaded in ToS dropdown")
                print("   • Ensure dropdown fully expands to show all accounts")
                print("   • Try running 'Setup Template' for better dropdown detection")

            if valid_looking < account_count:
                print("   • Some account names look malformed - may need OCR tuning")
                print("   • Check dropdown capture images in assets/captures/dropdown/")

            if unique_count < account_count:
                print("   • Found duplicate accounts - OCR may be reading same account multiple times")

            print("   • This looks ready for the main monitoring application!")

            # Integration test suggestion
            print()
            print("🔗 INTEGRATION TEST:")
            print("   • Run the main DeltaMon app")
            print("   • Use 'Read Accounts from Dropdown' button")
            print("   • Verify the same accounts appear in the monitoring table")
            print("   • Test 'Start Monitoring' to ensure full workflow works")

        else:
            print("❌ FAILED: Could not read any accounts from dropdown")
            print()
            print("💡 TROUBLESHOOTING:")
            print("   • Check that ToS is running with title 'Main@thinkorswim [build 1985]'")
            print("   • Ensure the account dropdown is visible in upper-left area")
            print("   • Try manually clicking the dropdown to verify it works")
            print("   • Check if dropdown trigger template exists in assets/templates/")
            print("   • Run 'Setup Template' in the main app to create proper template")
            print("   • Ensure ToS window is not obstructed by other windows")
            print()
            print("🔍 DEBUG STEPS:")
            print("   1. Check if template exists: assets/templates/account_dropdown_template.png")
            print("   2. Look for captured images: assets/captures/dropdown/")
            print("   3. Try running with ToS window maximized")
            print("   4. Verify dropdown opens when clicked manually")
            print("   5. Check that accounts are actually loaded in ToS")

    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        print()
        print("💡 This error suggests a setup issue:")
        print("   • Check that all required dependencies are installed")
        print("   • Ensure ToS is running and accessible")
        print("   • Try running as administrator if needed")
        print("   • Check Python path and module imports")

    print()
    print("🏁 Dropdown reading test complete!")
    print()

    # Ask if they want to see debug images
    if discovered_accounts:
        show_debug = input("Would you like to open the captured dropdown image for review? (y/n): ").lower().strip()
        if show_debug == 'y':
            try:
                import subprocess
                import os

                captures_dir = os.path.join(project_root, 'assets', 'captures', 'dropdown')
                if os.path.exists(captures_dir):
                    print(f"📂 Opening captures directory: {captures_dir}")
                    if os.name == 'nt':  # Windows
                        subprocess.run(['explorer', captures_dir])
                    else:  # macOS/Linux
                        subprocess.run(['open', captures_dir])
            except Exception as e:
                print(f"Could not open directory: {e}")

    input("Press Enter to exit...")


if __name__ == "__main__":
    test_dropdown_reading()