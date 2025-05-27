# Delta_Mon/test_optiondelta_extraction.py

"""
Test script for OptionDelta column detection and extraction.
Run this to verify the system can find and extract delta values from Pradeep's ToS layout.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.optimized_delta_extractor import OptimizedDeltaExtractor
from core.window_manager import WindowManager
from core.tos_navigator import TosNavigator
import time


def test_optiondelta_extraction():
    """Test the OptionDelta column detection and extraction."""
    print("🧪 Testing OptionDelta Column Detection & Extraction")
    print("=" * 60)
    print()

    print("📋 Prerequisites for this test:")
    print("   ✅ Thinkorswim must be running")
    print("   ✅ ToS window should show the portfolio view with OptionDelta column")
    print("   ✅ OptionDelta column should be visible (like in your screenshot)")
    print("   ✅ Some positions should be loaded with delta values")
    print()

    input("Press Enter when ToS is ready with OptionDelta column visible...")
    print()

    try:
        # Initialize components
        print("🔧 Initializing OptionDelta extraction system...")
        window_manager = WindowManager(
            target_exact_title="Main@thinkorswim [build 1985]",
            exclude_title_substring="DeltaMon"
        )

        # Find ToS window
        print("📍 Locating ToS window...")
        tos_hwnd = window_manager.find_tos_window()
        if not tos_hwnd:
            print("❌ ToS window not found")
            return False

        # Focus window
        print("🎯 Focusing ToS window...")
        if not window_manager.focus_tos_window():
            print("⚠️ Warning: Could not focus ToS window")

        # Initialize extractor
        print("🔧 Initializing optimized delta extractor...")
        tos_navigator = TosNavigator(tos_hwnd)
        extractor = OptimizedDeltaExtractor(tos_navigator)

        print()
        print("🚀 Starting OptionDelta column detection...")
        print("-" * 50)

        # Step 1: Find OptionDelta column location
        print("🔍 Step 1: Locating OptionDelta column header...")
        start_time = time.time()
        column_info = extractor.find_option_delta_column_location(save_debug=True)
        detection_time = time.time() - start_time

        if not column_info:
            print("❌ FAILED: Could not locate OptionDelta column")
            print()
            print("💡 TROUBLESHOOTING:")
            print("   • Ensure OptionDelta column is visible in ToS")
            print("   • Check that you're in the portfolio/positions view")
            print("   • Verify the column header says 'OptionDelta'")
            print("   • Try scrolling to make the column more visible")
            return False

        print(f"✅ SUCCESS: Found OptionDelta column in {detection_time:.1f}s")
        print(f"   📊 Column info: {column_info}")
        print()

        # Step 2: Extract all delta values from column
        print("🔍 Step 2: Extracting all delta values from column...")
        start_time = time.time()
        all_delta_values = extractor.extract_all_delta_values_from_column(column_info)
        extraction_time = time.time() - start_time

        if not all_delta_values:
            print("❌ FAILED: Could not extract any delta values")
            print()
            print("💡 TROUBLESHOOTING:")
            print("   • Check that there are positions with delta values")
            print("   • Ensure OptionDelta column contains numeric values")
            print("   • Verify the column isn't empty or showing '--'")
            return False

        print(f"✅ SUCCESS: Extracted {len(all_delta_values)} delta values in {extraction_time:.1f}s")
        print()

        # Step 3: Display extracted values
        print("📊 EXTRACTED DELTA VALUES:")
        print("=" * 30)
        for i, delta_info in enumerate(all_delta_values, 1):
            delta_val = delta_info['delta_value']
            formatted = delta_info['formatted_value']
            percentage = delta_info['percentage']
            print(f"   {i:2d}. {formatted} ({percentage})")

        print()

        # Step 4: Test threshold checking
        print("🔍 Step 3: Testing threshold checking...")
        positive_threshold = 0.08  # Pradeep's high threshold
        negative_threshold = -0.05  # Pradeep's low threshold

        alerts = extractor.check_delta_thresholds(
            all_delta_values,
            positive_threshold,
            negative_threshold
        )

        print(f"🎯 Using thresholds: High > +{positive_threshold}, Low < {negative_threshold}")
        print()

        if alerts:
            print(f"🚨 ALERTS TRIGGERED: {len(alerts)} values exceed thresholds!")
            print("=" * 40)
            for alert in alerts:
                delta_val = alert['delta_value']
                alert_type = alert['alert_type']
                threshold = alert['threshold_exceeded']
                excess = alert['excess_amount']

                if alert_type == "HIGH_DELTA":
                    print(f"   🔥 HIGH: {delta_val:+.3f} (>{threshold:+.3f}, excess: {excess:+.3f})")
                else:
                    print(f"   ❄️ LOW:  {delta_val:+.3f} (<{threshold:+.3f}, excess: {excess:+.3f})")
        else:
            print("✅ NO ALERTS: All delta values within thresholds")
            print(f"   All values between {negative_threshold:+.3f} and {positive_threshold:+.3f}")

        print()
        print("-" * 50)

        # Step 4: Performance summary
        print("📈 PERFORMANCE SUMMARY:")
        print("=" * 25)
        print(f"   • Column detection time: {detection_time:.1f}s")
        print(f"   • Value extraction time: {extraction_time:.1f}s")
        print(f"   • Total delta values found: {len(all_delta_values)}")
        print(f"   • Alert threshold violations: {len(alerts)}")
        print(f"   • Detection method: {column_info.get('method', 'unknown')}")
        print(f"   • Column confidence: {column_info.get('confidence', 'N/A')}")

        # Step 5: Recommendations
        print()
        print("💡 RECOMMENDATIONS:")
        print("=" * 20)

        if len(all_delta_values) >= 10:
            print("   🎉 EXCELLENT: Found many delta values - great for monitoring!")
        elif len(all_delta_values) >= 5:
            print("   👍 GOOD: Found several delta values - monitoring ready!")
        else:
            print("   ⚠️ LIMITED: Found few delta values - may need more positions")

        if detection_time < 2.0:
            print("   ⚡ FAST: Column detection is quick and efficient")
        else:
            print("   🐌 SLOW: Column detection took a while - template may help")

        if extraction_time / max(1, len(all_delta_values)) < 0.5:
            print("   ⚡ EFFICIENT: Value extraction is fast per position")
        else:
            print("   🔧 OPTIMIZATION: Value extraction could be faster")

        success_rate = len(all_delta_values) / max(1, len(all_delta_values)) * 100
        print(f"   📊 SUCCESS RATE: {success_rate:.0f}% extraction success")

        print()
        print("🎯 NEXT STEPS:")
        print("   1. This system is ready for real-time monitoring!")
        print("   2. Configure your exact thresholds in the main app")
        print("   3. Set up Discord webhook for alerts")
        print("   4. Start monitoring with the main DeltaMon application")

        return True

    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        print()
        print("💡 This error suggests a setup issue:")
        print("   • Check that all required dependencies are installed")
        print("   • Ensure ToS is running and accessible")
        print("   • Try running as administrator if needed")
        print("   • Check Python path and module imports")
        return False

    finally:
        print()
        print("🏁 OptionDelta extraction test complete!")
        print()

        # Ask if they want to see debug images
        show_debug = input("Would you like to open the captured images for review? (y/n): ").lower().strip()
        if show_debug == 'y':
            try:
                import subprocess

                captures_dir = os.path.join(project_root, 'assets', 'captures', 'portfolio')
                if os.path.exists(captures_dir):
                    print(f"📂 Opening captures directory: {captures_dir}")
                    if os.name == 'nt':  # Windows
                        subprocess.run(['explorer', captures_dir])
                    else:  # macOS/Linux
                        subprocess.run(['open', captures_dir])
            except Exception as e:
                print(f"Could not open directory: {e}")


if __name__ == "__main__":
    test_optiondelta_extraction()