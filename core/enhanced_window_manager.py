# Delta_Mon/core/enhanced_window_manager.py

import win32gui
import win32con
import win32api
import time
from typing import Optional, List, Dict

from scipy.signal.windows import windows


class EnhancedWindowManager:
    def __init__(self,
                 main_window_title="Main@thinkorswim [build 1985]",
                 exclude_title_substring="DeltaMon"):

        self.main_window_title = main_window_title.lower() if main_window_title else None
        self.exclude_title_substring = exclude_title_substring.lower() if exclude_title_substring else None
        self.hwnd = None
        self.launcher_hwnd = None

        # More specific core keywords to identify a ToS-related window
        self.tos_core_keywords = [
            "thinkorswim",
            "td ameritrade",  # For older installations
            "charles schwab",  # For newer installations
            # "tos", # Could be too generic, use with caution or specific contexts
        ]
        # Secondary keywords for categorization once a window is deemed ToS-related
        self.category_keywords = {
            'main_trading': ["main@thinkorswim"],  # 'build' check is also good
            'login': ["login", "logon", "sign in", "authenticate", "password"],
            'launcher': ["launcher", "start", "welcome", "updater", "client loader"],
        }

    def find_all_tos_windows(self) -> Dict[str, List[Dict]]:
        print("🔍 Scanning for all Thinkorswim windows (Enhanced)...")

        all_windows = []
        try:
            win32gui.EnumWindows(self._collect_windows_callback, all_windows)
        except Exception as e:
            print(f"Error enumerating windows: {e}")
            return {}

        categorized = {
            'main_trading': [],
            'launcher': [],
            'login': [],
            'other_tos': [],
            'unknown_tos_related': []  # For windows that match core_keywords but not specific categories
        }

        for window_info in all_windows:
            title_lower = window_info['title'].lower()

            if self.exclude_title_substring and self.exclude_title_substring in title_lower:
                continue

            # Primary check: Must contain a core ToS keyword
            is_tos_window = False
            for core_keyword in self.tos_core_keywords:
                if core_keyword in title_lower:
                    is_tos_window = True
                    break

            if is_tos_window:
                print(f"   संभावित ToS विंडो मिली: '{window_info['title']}' (HWND: {window_info['hwnd']})")
                category = self._categorize_tos_window(window_info, title_lower)
                categorized[category].append(window_info)
            # else:
            # print(f"  Skipping non-ToS window: '{window_info['title']}'")

        self._print_window_analysis(categorized)
        return categorized

    def _collect_windows_callback(self, hwnd, windows_list):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        try:
            title = win32gui.GetWindowText(hwnd)
            if title:
                windows_list.append({
                    'hwnd': hwnd,
                    'title': title,
                    'class': win32gui.GetClassName(hwnd)
                })
        except:
            pass
        return True

    def _categorize_tos_window(self, window_info: Dict, title_lower: str) -> str:
        # Check for main trading window (most specific)
        if "main@thinkorswim" in title_lower and "build" in title_lower:
            # Check if it's the one we're targeting, if a specific title was given
            if self.main_window_title and self.main_window_title == title_lower:
                return 'main_trading'
            elif not self.main_window_title:  # If no specific main title, any main@thinkorswim is fine
                return 'main_trading'
            # If it's a main@thinkorswim but not matching a specific target, treat as other_tos for now
            # This handles cases where multiple main windows might be open (e.g. paper money + live)

        # Check for login windows
        for keyword in self.category_keywords['login']:
            if keyword in title_lower:
                return 'login'

        # Check for launcher/updater windows
        for keyword in self.category_keywords['launcher']:
            if keyword in title_lower:
                # Avoid miscategorizing the main window if "welcome" is in its title too
                if "main@thinkorswim" in title_lower and keyword == "welcome":
                    continue
                return 'launcher'

        # If it contained a core ToS keyword but didn't fit above categories
        if any(core_keyword in title_lower for core_keyword in self.tos_core_keywords):
            # If it's a main window but didn't match the specific self.main_window_title
            if "main@thinkorswim" in title_lower:
                return 'other_tos'  # Or a new category like 'other_main_trading'
            return 'other_tos'  # General ToS window (e.g., charts, tools detached)

        return 'unknown_tos_related'  # Should ideally not be reached if primary filter is good

    def _print_window_analysis(self, categorized: Dict):
        total_tos = sum(len(windows) for windows in categorized.values())
        print(f"📊 Found {total_tos} ToS-related windows:")
        for category, windows in categorized.items():
            if windows:
                print(f"   {category.replace('_', ' ').title()}: {len(windows)}")
                for window in windows[:3]:
                    print(f"      • '{window['title']}' (HWND: {window['hwnd']})")
                if len(windows) > 3:
                    print(f"      ... and {len(windows) - 3} more")

    def wait_for_main_trading_window(self, timeout_seconds: int = 60, check_interval: float = 2.0) -> Optional[int]:
        print(
            f"⏳ Waiting up to {timeout_seconds}s for main trading window ('{self.main_window_title or 'any main@thinkorswim'}')...")
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            main_hwnd = self._find_main_trading_window()
            if main_hwnd:
                self.hwnd = main_hwnd
                print(f"✅ Found main trading window: '{win32gui.GetWindowText(main_hwnd)}' (HWND: {main_hwnd})")
                return main_hwnd

            # Show current status briefly without re-running full find_all_tos_windows if too frequent
            if int(time.time() - start_time) % 5 == 0:  # Update status every 5s
                self._show_current_tos_status(quick_check=True)

            print(f"   Waiting... ({time.time() - start_time:.1f}s elapsed)")
            time.sleep(check_interval)
        print(f"❌ Timeout: Main trading window did not appear within {timeout_seconds}s")
        return None

    def _find_main_trading_window(self) -> Optional[int]:
        # More direct search for the main window
        hwnds = []

        def callback(hwnd, hwnds_list):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).lower()
                if self.exclude_title_substring and self.exclude_title_substring in title:
                    return True

                # Check for specific main window title if provided
                if self.main_window_title and self.main_window_title == title:
                    hwnds_list.append(hwnd)
                    return False  # Exact match found
                # Fallback to generic main window pattern if no specific title or not matched yet
                elif not self.main_window_title and "main@thinkorswim" in title and "build" in title:
                    hwnds_list.append(hwnd)
                    return False  # Generic main window found
            return True

        win32gui.EnumWindows(callback, hwnds)
        if hwnds:
            return hwnds[0]
        return None

    def _show_current_tos_status(self, quick_check=False):
        if quick_check:  # Avoid full re-scan if just providing interim update
            if self.hwnd and win32gui.IsWindow(self.hwnd) and "main@thinkorswim" in win32gui.GetWindowText(
                    self.hwnd).lower():
                print("   (Quick Status) ✅ Main trading window still seems present.")
                return

        categorized = self.find_all_tos_windows()
        if categorized['main_trading']:
            print("   ✅ Main trading window found!")
        elif categorized['login']:
            print("   🔑 Login window detected - please complete login")
        elif categorized['launcher']:
            print("   🚀 Launcher/Updater window detected - ToS is starting/updating")
        elif categorized['other_tos']:
            print("   ⚠️ Other ToS windows found - main trading window may be loading")
        else:
            print("   ❌ No ToS windows detected - please start Thinkorswim")

    def find_tos_window_smart(self) -> Optional[int]:
        print("🧠 Smart ToS window detection...")
        categorized = self.find_all_tos_windows()

        if categorized['main_trading']:
            main_window = categorized['main_trading'][0]
            self.hwnd = main_window['hwnd']
            print(f"🎯 Using main trading window: '{main_window['title']}' (HWND: {self.hwnd})")
            return self.hwnd

        if categorized['login']:
            login_window = categorized['login'][0]
            print(f"🔑 Login window detected: '{login_window['title']}'")
            print("💡 Please complete login, then main trading window should appear.")
            try:
                response = input("Wait for main trading window to appear? (y/n): ").lower().strip()
                if response == 'y':
                    return self.wait_for_main_trading_window()
            except:
                pass
            return None

        if categorized['launcher']:
            launcher_window = categorized['launcher'][0]
            print(f"🚀 Launcher/Updater window detected: '{launcher_window['title']}'")
            print("💡 ToS is starting or updating. Please wait for it to open the trading platform or login screen.")
            try:
                response = input("Wait for main trading window to appear? (y/n): ").lower().strip()
                if response == 'y':
                    return self.wait_for_main_trading_window()
            except:
                pass
            return None

        if categorized['other_tos']:
            other_window = categorized['other_tos'][0]
            print(f"⚠️ Found other ToS window: '{other_window['title']}' (HWND: {other_window['hwnd']})")
            print("⚠️ This may not be the main trading interface. Attempting to use it.")
            self.hwnd = other_window['hwnd']
            return self.hwnd

        print("❌ No usable ToS windows found by smart detection.")
        print("💡 Please start Thinkorswim and ensure it's fully loaded, or check logs for scan details.")
        return None

    def get_window_rect(self) -> Optional[tuple]:
        if not self.hwnd:
            # Attempt to find it if not set, but don't trigger interactive smart find here
            # self.hwnd = self._find_main_trading_window() # a non-interactive find
            # if not self.hwnd:
            print("No ToS window handle (HWND) available for get_window_rect.")
            return None
        try:
            return win32gui.GetWindowRect(self.hwnd)
        except Exception as e:
            print(f"Error getting window rect for HWND {self.hwnd}: {e}")
            self.hwnd = None  # Invalidate HWND if GetWindowRect fails
            return None

    def focus_tos_window(self) -> bool:
        if not self.hwnd:
            print("No ToS window handle available for focusing. Attempting to find one first...")
            self.hwnd = self._find_main_trading_window()  # Try a non-interactive find
            if not self.hwnd:
                print("Focus failed: ToS window could not be found.")
                return False
            print(f"Found ToS window (HWND: {self.hwnd}) for focusing.")

        try:
            if win32gui.IsIconic(self.hwnd):  # Minimized
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                time.sleep(0.3)

            # Simple SetForegroundWindow
            win32gui.SetForegroundWindow(self.hwnd)
            time.sleep(0.2)  # Brief pause

            # Check if successful
            if win32gui.GetForegroundWindow() == self.hwnd:
                print(f"✅ Focused ToS window (HWND: {self.hwnd})")
                return True
            else:  # More aggressive focus attempt if first failed
                print(
                    f"⚠️ SetForegroundWindow for HWND {self.hwnd} might not have been fully successful. Trying alternative focus...")
                # Alt focus: Shell object to activate (often more robust)
                try:
                    import win32com.client
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shell.SendKeys('%')  # Send ALT to clear any menu state
                    win32gui.SetForegroundWindow(self.hwnd)
                    time.sleep(0.2)
                    if win32gui.GetForegroundWindow() == self.hwnd:
                        print(f"✅ Alternative focus for HWND {self.hwnd} successful.")
                        return True
                except Exception as com_e:
                    print(f"   Alternative focus error: {com_e}")

                print(
                    f"❌ Failed to robustly focus ToS window (HWND {self.hwnd}). Current foreground: {win32gui.GetForegroundWindow()}")
                return False

        except Exception as e:
            print(f"Error focusing ToS window (HWND {self.hwnd}): {e}")
            self.hwnd = None  # Invalidate HWND if focus operations fail badly
            return False

    def is_main_trading_window_available(self) -> bool:
        return self._find_main_trading_window() is not None

    def get_tos_status_report(self) -> Dict:
        categorized = self.find_all_tos_windows()
        main_available = bool(categorized['main_trading'])
        if main_available:  # If main is found, update self.hwnd
            self.hwnd = categorized['main_trading'][0]['hwnd']

        return {
            'main_trading_available': main_available,
            'launcher_open': bool(categorized['launcher']),
            'login_required': bool(categorized['login']),
            'other_tos_windows': len(categorized['other_tos']),
            'total_tos_windows': sum(len(windows) for category_windows in categorized.values() if category_windows),
            # Sum only non-empty lists
            'recommended_action': self._get_recommended_action(categorized)
        }

    def _get_recommended_action(self, categorized: Dict) -> str:
        if categorized['main_trading']:
            return "Ready for monitoring - main trading window available"
        elif categorized['login']:
            return "Complete login process in ToS or use Auto-Login"
        elif categorized['launcher']:
            return "ToS is starting/updating. Wait for platform or login screen, or use Auto-Login"
        elif categorized['other_tos']:
            return "Main trading window may be loading or other ToS components are open. Wait or restart ToS."
        else:
            return "Start Thinkorswim application or use Auto-Login"


if __name__ == "__main__":
    print("Enhanced ToS Window Manager Test")
    print("=" * 40)
    wm = EnhancedWindowManager()
    status = wm.get_tos_status_report()
    print(f"📊 ToS Status Report:")
    for key, value in status.items():
        print(f"   {key}: {value}")
    print()
    tos_hwnd = wm.find_tos_window_smart()
    if tos_hwnd:
        print(f"✅ Smart find successful: {tos_hwnd} ('{win32gui.GetWindowText(tos_hwnd)}')")
        rect = wm.get_window_rect()
        if rect: print(f"📐 Window rect: {rect}")
        focus_success = wm.focus_tos_window()
        print(f"🎯 Focus success: {focus_success}")
    else:
        print("❌ No usable ToS window found by smart detection.")