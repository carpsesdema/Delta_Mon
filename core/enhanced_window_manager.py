# Delta_Mon/core/enhanced_window_manager.py

import win32gui
import win32con
import win32api
import time
from typing import Optional, List, Dict


class EnhancedWindowManager:
    def __init__(self,
                 main_window_title="Main@thinkorswim [build 1985]",
                 exclude_title_substring="DeltaMon"):

        self.main_window_title = main_window_title.lower() if main_window_title else None
        self.exclude_title_substring = exclude_title_substring.lower() if exclude_title_substring else None
        self.hwnd = None  # Main trading window handle
        self.launcher_hwnd = None  # Launcher window handle

        # Known ToS window patterns
        self.tos_window_patterns = [
            "main@thinkorswim",  # Main trading window
            "thinkorswim",  # General ToS windows
            "login",  # Login window
            "account",  # Account selection
            "launcher",  # Launcher window
            "td ameritrade",  # Legacy patterns
        ]

    def find_all_tos_windows(self) -> Dict[str, List[Dict]]:
        """
        Find all ToS-related windows and categorize them.

        Returns:
            Dictionary with categorized ToS windows
        """
        print("🔍 Scanning for all Thinkorswim windows...")

        all_windows = []
        try:
            win32gui.EnumWindows(self._collect_windows_callback, all_windows)
        except Exception as e:
            print(f"Error enumerating windows: {e}")
            return {}

        # Categorize ToS windows
        categorized = {
            'main_trading': [],
            'launcher': [],
            'login': [],
            'other_tos': [],
            'unknown': []
        }

        for window_info in all_windows:
            title = window_info['title'].lower()

            # Skip our own app
            if self.exclude_title_substring and self.exclude_title_substring in title:
                continue

            # Check if it's a ToS window
            if any(pattern in title for pattern in self.tos_window_patterns):
                category = self._categorize_tos_window(window_info)
                categorized[category].append(window_info)

        # Print findings
        self._print_window_analysis(categorized)

        return categorized

    def _collect_windows_callback(self, hwnd, windows_list):
        """Callback to collect all visible windows."""
        if not win32gui.IsWindowVisible(hwnd):
            return True

        try:
            title = win32gui.GetWindowText(hwnd)
            if title:  # Only collect windows with titles
                windows_list.append({
                    'hwnd': hwnd,
                    'title': title,
                    'class': win32gui.GetClassName(hwnd)
                })
        except:
            pass  # Skip windows we can't read

        return True

    def _categorize_tos_window(self, window_info: Dict) -> str:
        """Categorize a ToS window based on its title and class."""
        title = window_info['title'].lower()
        class_name = window_info['class'].lower()

        # Main trading window
        if 'main@thinkorswim' in title and 'build' in title:
            return 'main_trading'

        # Login/launcher windows
        if any(keyword in title for keyword in ['login', 'sign in', 'authenticate']):
            return 'login'

        if any(keyword in title for keyword in ['launcher', 'start', 'welcome']):
            return 'launcher'

        # Other ToS windows
        if 'thinkorswim' in title or 'td ameritrade' in title:
            return 'other_tos'

        return 'unknown'

    def _print_window_analysis(self, categorized: Dict):
        """Print analysis of found ToS windows."""
        total_tos = sum(len(windows) for windows in categorized.values())

        print(f"📊 Found {total_tos} ToS-related windows:")

        for category, windows in categorized.items():
            if windows:
                print(f"   {category.replace('_', ' ').title()}: {len(windows)}")
                for window in windows[:3]:  # Show first 3 of each type
                    print(f"      • '{window['title']}' (HWND: {window['hwnd']})")
                if len(windows) > 3:
                    print(f"      ... and {len(windows) - 3} more")

    def wait_for_main_trading_window(self, timeout_seconds: int = 60, check_interval: float = 2.0) -> Optional[int]:
        """
        Wait for the main trading window to appear.

        Args:
            timeout_seconds: Maximum time to wait
            check_interval: How often to check (seconds)

        Returns:
            HWND of main trading window or None if timeout
        """
        print(f"⏳ Waiting up to {timeout_seconds}s for main trading window...")

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            # Check for main trading window
            main_hwnd = self._find_main_trading_window()
            if main_hwnd:
                self.hwnd = main_hwnd
                print(f"✅ Found main trading window (HWND: {main_hwnd})")
                return main_hwnd

            # Show current status
            self._show_current_tos_status()

            print(f"   Waiting... ({time.time() - start_time:.1f}s elapsed)")
            time.sleep(check_interval)

        print(f"❌ Timeout: Main trading window did not appear within {timeout_seconds}s")
        return None

    def _find_main_trading_window(self) -> Optional[int]:
        """Find the main trading window specifically."""
        categorized = self.find_all_tos_windows()
        main_windows = categorized.get('main_trading', [])

        if main_windows:
            # Return the first main trading window
            return main_windows[0]['hwnd']
        return None

    def _show_current_tos_status(self):
        """Show current status of ToS windows."""
        categorized = self.find_all_tos_windows()

        if categorized['main_trading']:
            print("   ✅ Main trading window found!")
        elif categorized['login']:
            print("   🔑 Login window detected - please complete login")
        elif categorized['launcher']:
            print("   🚀 Launcher window detected - please open trading platform")
        elif categorized['other_tos']:
            print("   ⚠️ Other ToS windows found - main trading window may be loading")
        else:
            print("   ❌ No ToS windows detected - please start Thinkorswim")

    def find_tos_window_smart(self) -> Optional[int]:
        """
        Smart ToS window detection with launcher handling.

        Returns:
            HWND of usable ToS window or None
        """
        print("🧠 Smart ToS window detection...")

        categorized = self.find_all_tos_windows()

        # Priority 1: Main trading window (ideal)
        if categorized['main_trading']:
            main_window = categorized['main_trading'][0]
            self.hwnd = main_window['hwnd']
            print(f"🎯 Using main trading window: '{main_window['title']}'")
            return self.hwnd

        # Priority 2: Check for launcher/login and guide user
        if categorized['login']:
            login_window = categorized['login'][0]
            print(f"🔑 Login window detected: '{login_window['title']}'")
            print("💡 Please complete login, then main trading window should appear")

            # Ask user if they want to wait
            try:
                response = input("Wait for main trading window to appear? (y/n): ").lower().strip()
                if response == 'y':
                    return self.wait_for_main_trading_window()
            except:
                pass  # Handle cases where input isn't available

            return None

        if categorized['launcher']:
            launcher_window = categorized['launcher'][0]
            print(f"🚀 Launcher window detected: '{launcher_window['title']}'")
            print("💡 Please open the trading platform from the launcher")

            try:
                response = input("Wait for main trading window to appear? (y/n): ").lower().strip()
                if response == 'y':
                    return self.wait_for_main_trading_window()
            except:
                pass

            return None

        # Priority 3: Other ToS windows (may work)
        if categorized['other_tos']:
            other_window = categorized['other_tos'][0]
            print(f"⚠️ Found other ToS window: '{other_window['title']}'")
            print("⚠️ This may not be the main trading interface")

            # We can try to use it, but warn the user
            self.hwnd = other_window['hwnd']
            return self.hwnd

        # Priority 4: No ToS windows found
        print("❌ No ToS windows found")
        print("💡 Please start Thinkorswim and ensure it's fully loaded")
        return None

    def get_window_rect(self) -> Optional[tuple]:
        """Get bounding rectangle of the found ToS window."""
        if not self.hwnd:
            return None

        try:
            return win32gui.GetWindowRect(self.hwnd)
        except Exception as e:
            print(f"Error getting window rect for HWND {self.hwnd}: {e}")
            return None

    def focus_tos_window(self) -> bool:
        """Focus the ToS window."""
        if not self.hwnd:
            print("No ToS window handle available for focusing")
            return False

        try:
            # Restore if minimized
            if win32gui.IsIconic(self.hwnd):
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                time.sleep(0.5)

            # Bring to foreground
            win32gui.SetForegroundWindow(self.hwnd)
            print(f"✅ Focused ToS window (HWND: {self.hwnd})")
            return True

        except Exception as e:
            print(f"Error focusing ToS window (HWND {self.hwnd}): {e}")
            return False

    def is_main_trading_window_available(self) -> bool:
        """Check if main trading window is currently available."""
        return self._find_main_trading_window() is not None

    def get_tos_status_report(self) -> Dict:
        """Get comprehensive status report of ToS windows."""
        categorized = self.find_all_tos_windows()

        return {
            'main_trading_available': bool(categorized['main_trading']),
            'launcher_open': bool(categorized['launcher']),
            'login_required': bool(categorized['login']),
            'other_tos_windows': len(categorized['other_tos']),
            'total_tos_windows': sum(len(windows) for windows in categorized.values()),
            'recommended_action': self._get_recommended_action(categorized)
        }

    def _get_recommended_action(self, categorized: Dict) -> str:
        """Get recommended action based on current ToS window state."""
        if categorized['main_trading']:
            return "Ready for monitoring - main trading window available"
        elif categorized['login']:
            return "Complete login process in ToS"
        elif categorized['launcher']:
            return "Open trading platform from ToS launcher"
        elif categorized['other_tos']:
            return "Main trading window may be loading - wait or restart ToS"
        else:
            return "Start Thinkorswim application"


# Test function
if __name__ == "__main__":
    print("Enhanced ToS Window Manager Test")
    print("=" * 40)

    wm = EnhancedWindowManager()

    # Get comprehensive status
    status = wm.get_tos_status_report()
    print(f"📊 ToS Status Report:")
    for key, value in status.items():
        print(f"   {key}: {value}")

    print()

    # Try smart detection
    tos_hwnd = wm.find_tos_window_smart()

    if tos_hwnd:
        print(f"✅ Successfully found ToS window: {tos_hwnd}")

        # Test window operations
        rect = wm.get_window_rect()
        if rect:
            print(f"📐 Window rect: {rect}")

        focus_success = wm.focus_tos_window()
        print(f"🎯 Focus success: {focus_success}")

    else:
        print("❌ No usable ToS window found")
        print("💡 Follow the recommendations above to resolve this")