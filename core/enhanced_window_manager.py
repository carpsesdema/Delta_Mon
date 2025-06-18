# Delta_Mon/core/enhanced_window_manager.py

import win32gui
import win32con
import win32api
import time
from typing import Optional, List, Dict


class EnhancedWindowManager:
    def __init__(self, exclude_title_substring="DeltaMon"):
        self.exclude_title_substring = exclude_title_substring.lower() if exclude_title_substring else None
        self.hwnd = None
        self.launcher_hwnd = None

        # Keywords to identify ToS-related windows
        self.tos_core_keywords = [
            "thinkorswim",
            "td ameritrade",
            "charles schwab",
        ]
        self.category_keywords = {
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
        }

        for window_info in all_windows:
            title_lower = window_info['title'].lower()

            if self.exclude_title_substring and self.exclude_title_substring in title_lower:
                continue

            # Primary check: Must contain a core ToS keyword
            is_tos_window = any(core_keyword in title_lower for core_keyword in self.tos_core_keywords)

            if is_tos_window:
                category = self._categorize_tos_window(title_lower)
                if category:
                    categorized[category].append(window_info)

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

    def _categorize_tos_window(self, title_lower: str) -> Optional[str]:
        # Check for main trading window (most specific and important)
        if "main@thinkorswim" in title_lower and "build" in title_lower:
            return 'main_trading'

        # Check for login windows
        if any(keyword in title_lower for keyword in self.category_keywords['login']):
            return 'login'

        # Check for launcher/updater windows
        if any(keyword in title_lower for keyword in self.category_keywords['launcher']):
            # Avoid miscategorizing the main window if "welcome" is in its title
            if "main@thinkorswim" in title_lower and "welcome" in title_lower:
                return 'main_trading'
            return 'launcher'

        # If it contained a core ToS keyword but didn't fit above, it's 'other'
        return 'other_tos'

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

    def _find_main_trading_window(self) -> Optional[int]:
        hwnds = []

        def callback(hwnd, hwnds_list):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).lower()
                if self.exclude_title_substring and self.exclude_title_substring in title:
                    return True

                if "main@thinkorswim" in title and "build" in title:
                    hwnds_list.append(hwnd)
                    return False  # Exact match found, stop searching
            return True

        win32gui.EnumWindows(callback, hwnds)
        return hwnds[0] if hwnds else None

    def get_window_rect(self) -> Optional[tuple]:
        if not self.hwnd:
            print("No ToS window handle (HWND) available for get_window_rect.")
            return None
        try:
            return win32gui.GetWindowRect(self.hwnd)
        except Exception as e:
            print(f"Error getting window rect for HWND {self.hwnd}: {e}")
            self.hwnd = None
            return None

    def focus_tos_window(self) -> bool:
        if not self.hwnd:
            print("No ToS window handle available for focusing. Finding it first...")
            self.hwnd = self._find_main_trading_window()
            if not self.hwnd:
                print("Focus failed: ToS window could not be found.")
                return False
            print(f"Found ToS window (HWND: {self.hwnd}) for focusing.")

        try:
            if win32gui.IsIconic(self.hwnd):
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                time.sleep(0.3)

            win32gui.SetForegroundWindow(self.hwnd)
            time.sleep(0.2)

            if win32gui.GetForegroundWindow() == self.hwnd:
                print(f"✅ Focused ToS window (HWND: {self.hwnd})")
                return True
            else:
                print("⚠️ SetForegroundWindow failed. Trying alternative focus...")
                try:
                    import win32com.client
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shell.SendKeys('%')
                    win32gui.SetForegroundWindow(self.hwnd)
                    time.sleep(0.2)
                    if win32gui.GetForegroundWindow() == self.hwnd:
                        print("✅ Alternative focus successful.")
                        return True
                except Exception as com_e:
                    print(f"   Alternative focus error: {com_e}")

                print(f"❌ Failed to robustly focus ToS window (HWND {self.hwnd}).")
                return False
        except Exception as e:
            print(f"Error focusing ToS window (HWND {self.hwnd}): {e}")
            self.hwnd = None
            return False

    def is_main_trading_window_available(self) -> bool:
        return self._find_main_trading_window() is not None

    def get_tos_status_report(self) -> Dict:
        categorized = self.find_all_tos_windows()
        main_available = bool(categorized.get('main_trading'))
        if main_available:
            self.hwnd = categorized['main_trading'][0]['hwnd']

        return {
            'main_trading_available': main_available,
            'launcher_open': bool(categorized.get('launcher')),
            'login_required': bool(categorized.get('login')),
            'other_tos_windows': len(categorized.get('other_tos', [])),
            'total_tos_windows': sum(len(windows) for windows in categorized.values()),
            'recommended_action': self._get_recommended_action(categorized)
        }

    def _get_recommended_action(self, categorized: Dict) -> str:
        if categorized.get('main_trading'):
            return "Ready for monitoring - main trading window available"
        elif categorized.get('login'):
            return "Complete login process in ToS"
        elif categorized.get('launcher'):
            return "ToS is starting/updating. Wait for platform or login screen"
        elif categorized.get('other_tos'):
            return "Main trading window may be loading or other ToS components are open. Wait or restart ToS."
        else:
            return "Start Thinkorswim application"


if __name__ == "__main__":
    print("Enhanced ToS Window Manager Test")
    print("=" * 40)
    wm = EnhancedWindowManager()
    status = wm.get_tos_status_report()
    print("\n📊 ToS Status Report:")
    for key, value in status.items():
        print(f"   {key}: {value}")
    print()

    if wm.hwnd:
        print(f"✅ Main window found: {wm.hwnd} ('{win32gui.GetWindowText(wm.hwnd)}')")
        rect = wm.get_window_rect()
        if rect:
            print(f"📐 Window rect: {rect}")
        focus_success = wm.focus_tos_window()
        print(f"🎯 Focus success: {focus_success}")
    else:
        print("❌ No usable ToS window found.")