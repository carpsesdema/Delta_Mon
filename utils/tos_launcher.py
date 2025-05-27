# utils/tos_launcher.py

import os
import time
import subprocess
import pyautogui
import win32gui
import win32con
from typing import Optional, Tuple


class TosLauncher:
    """Find, launch, and login to ThinkOrSwim."""

    def __init__(self):
        """Initialize TOS launcher."""
        # Common installation paths for Windows
        # Adding more specific and common locations
        self.common_paths = [
            os.path.join(os.path.expanduser('~'), 'Desktop', 'thinkorswim.lnk'),  # Shortcut
            os.path.join(os.path.expanduser('~'), 'Desktop', 'thinkorswim.exe'),
            os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles(X86)', 'C:\\Program Files (x86)'), 'thinkorswim',
                         'thinkorswim.exe'),
            # Charles Schwab transition might place it differently
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Charles Schwab', 'thinkorswim',
                         'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles(X86)', 'C:\\Program Files (x86)'), 'Charles Schwab',
                         'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'thinkorswim', 'thinkorswim.exe'),
            # Default TD Ameritrade path often found via installer
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'TD Ameritrade', 'thinkorswim',
                         'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles(X86)', 'C:\\Program Files (x86)'), 'TD Ameritrade', 'thinkorswim',
                         'thinkorswim.exe'),
        ]
        # For non-Windows, though primary focus is Windows
        if os.name != 'nt':
            self.common_paths.extend([
                os.path.join(os.path.expanduser('~'), 'thinkorswim', 'thinkorswim'),
                '/opt/thinkorswim/thinkorswim',
            ])

    def find_tos_executable(self) -> Optional[str]:
        """
        Find the ThinkOrSwim executable path.
        Searches common locations and then performs a broader search.

        Returns:
            Path to TOS executable or None if not found
        """
        print("🕵️‍♀️ Searching for ThinkOrSwim executable...")

        # 1. Check common explicit paths first
        for path in self.common_paths:
            if os.path.exists(path):
                print(f"✅ Found TOS at common path: {path}")
                return path
            # Check for .lnk and resolve it
            if path.endswith('.lnk') and os.path.exists(path):
                try:
                    import winshell
                    from win32com.client import Dispatch
                    shell = Dispatch("WScript.Shell")
                    shortcut = shell.CreateShortCut(path)
                    target_path = shortcut.TargetPath
                    if os.path.exists(target_path):
                        print(f"✅ Resolved .lnk and found TOS at: {target_path}")
                        return target_path
                except ImportError:
                    print(
                        "⚠️ 'winshell' or 'pywin32' not installed, cannot resolve .lnk files directly. Skipping .lnk.")
                except Exception as e:
                    print(f"⚠️ Error resolving .lnk {path}: {e}")

        # 2. Broader search in typical user/program directories
        #    Limit search depth to avoid scanning entire system for too long.
        search_roots = [
            os.path.expanduser('~'),  # User's home directory
            os.environ.get('ProgramFiles', 'C:\\Program Files'),
            os.environ.get('ProgramFiles(X86)', 'C:\\Program Files (x86)'),
            os.environ.get('LOCALAPPDATA', os.path.join(os.path.expanduser('~'), 'AppData', 'Local')),  # For Windows
            os.environ.get('APPDATA', os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')),  # For Windows
        ]
        if os.name != 'nt':  # Add typical Linux/Mac install locations
            search_roots.extend(['/opt', '/Applications'])

        executable_names = ['thinkorswim.exe', 'thinkorswim']  # .exe for windows, plain for others

        for root_dir in search_roots:
            if not root_dir or not os.path.exists(root_dir):
                continue

            print(f"深入搜索 '{root_dir}'...")
            for dirpath, dirnames, filenames in os.walk(root_dir):
                # Limit search depth
                current_depth = dirpath.count(os.sep) - root_dir.count(os.sep)
                if current_depth > 4:  # Search up to 4 levels deep from the root
                    # Prune directories at this level to stop further descent
                    del dirnames[:]
                    continue

                # Optimize: if 'thinkorswim' or 'Charles Schwab' is in dirnames, prioritize those paths
                relevant_dirs = [d for d in dirnames if
                                 'thinkorswim' in d.lower() or 'schwab' in d.lower() or 'td ameritrade' in d.lower()]
                if relevant_dirs:
                    # Modify dirnames to only search these relevant subdirectories next
                    dirnames[:] = relevant_dirs

                for exe_name in executable_names:
                    if exe_name in filenames:
                        found_path = os.path.join(dirpath, exe_name)
                        # Additional check: ensure it's not in a temp or cache-like folder unless it's a known path
                        if 'temp' in found_path.lower() or 'cache' in found_path.lower():
                            if not any(rp in found_path for rp in [os.path.join('AppData', 'Local', 'thinkorswim'),
                                                                   os.path.join('AppData', 'Roaming', 'thinkorswim')]):
                                print(f"⚠️ Found '{exe_name}' in a temp/cache folder, skipping: {found_path}")
                                continue
                        print(f"✅ Found TOS during deeper search at: {found_path}")
                        return found_path

        print("❌ TOS executable not found after extensive search.")
        return None

    def launch_tos(self, executable_path: Optional[str] = None) -> bool:
        """
        Launch ThinkOrSwim application.

        Args:
            executable_path: Path to TOS executable (will search if None)

        Returns:
            True if launched successfully, False otherwise
        """
        if not executable_path:
            print("ℹ️ Executable path not provided, attempting to find it...")
            executable_path = self.find_tos_executable()

        if not executable_path or not os.path.exists(executable_path):
            print(f"❌ Cannot launch TOS: Executable not found or path invalid: {executable_path}")
            return False

        try:
            # Launch the application
            # For .lnk files on Windows, os.startfile is better
            if os.name == 'nt' and executable_path.lower().endswith('.lnk'):
                print(f"🚀 Launching TOS shortcut using os.startfile: {executable_path}")
                os.startfile(executable_path)
            else:
                print(f"🚀 Launching TOS executable: {executable_path}")
                subprocess.Popen([executable_path])

            print(f"✅ TOS launch command sent from: {executable_path}")

            # Wait for the application to start (initial splash/launcher)
            # This might need adjustment based on how fast ToS launcher appears.
            print("⏳ Waiting a few seconds for ToS launcher to initialize...")
            time.sleep(10)  # Increased wait time for launcher
            return True

        except Exception as e:
            print(f"❌ Error launching TOS from {executable_path}: {e}")
            return False

    def login_to_tos(self, username: str, password: str, max_wait: int = 60) -> bool:
        """
        Login to ThinkOrSwim with credentials.

        Args:
            username: TOS username
            password: TOS password
            max_wait: Maximum time to wait for login window (seconds)

        Returns:
            True if login successful, False otherwise
        """
        print("🔐 Attempting to login to ThinkOrSwim...")

        # Wait for login window to appear
        login_window_found = False
        login_hwnd = None
        possible_login_titles = [
            "thinkorswim Login",
            "Login - thinkorswim",
            "TD Ameritrade Login",  # Older versions or specific setups
            "Charles Schwab Login"  # For newer Schwab integrated versions
        ]

        start_time = time.time()
        print(f"⏳ Waiting up to {max_wait}s for login window...")
        while time.time() - start_time < max_wait:
            for title in possible_login_titles:
                login_hwnd = win32gui.FindWindow(None, title)
                if login_hwnd:
                    print(f"✅ Found login window with title: '{title}' (HWND: {login_hwnd})")
                    login_window_found = True
                    break
            if login_window_found:
                break
            time.sleep(1)  # Check every second

        if not login_window_found:
            print(f"❌ Login window not found after {max_wait}s timeout. Searched for titles: {possible_login_titles}")
            return False

        # Focus the login window
        try:
            print(f"🎯 Focusing login window (HWND: {login_hwnd})...")
            if win32gui.IsIconic(login_hwnd):  # If minimized
                win32gui.ShowWindow(login_hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(login_hwnd)
            time.sleep(1.5)  # Give it a moment to come to front and accept input
        except Exception as e:
            print(f"⚠️ Error focusing login window: {e}. Attempting to proceed...")

        try:
            # Ensure window is active for PyAutoGUI
            active_window_hwnd = win32gui.GetForegroundWindow()
            if active_window_hwnd != login_hwnd:
                print("⚠️ Login window not active after SetForegroundWindow. Trying again.")
                win32gui.SetForegroundWindow(login_hwnd)
                time.sleep(1)
                active_window_hwnd = win32gui.GetForegroundWindow()
                if active_window_hwnd != login_hwnd:
                    print("❌ Failed to make login window active. PyAutoGUI might target wrong window.")
                    # return False # Could be too strict, let's try anyway

            # Get window rect to potentially click into it first
            rect = win32gui.GetWindowRect(login_hwnd)
            pyautogui.click(rect[0] + 50, rect[1] + 50)  # Click near top-left of window to ensure focus
            time.sleep(0.5)

            print(f"⌨️ Typing username...")
            pyautogui.typewrite(username, interval=0.05)
            pyautogui.press('tab')
            time.sleep(0.5)

            print(f"⌨️ Typing password...")
            pyautogui.typewrite(password, interval=0.05)
            time.sleep(0.5)

            print(f"🚀 Submitting login...")
            pyautogui.press('enter')

            # Wait for main application to load after login
            # This is crucial and might take a while.
            print(f"⏳ Waiting for main application to load post-login (up to 45s)...")
            time.sleep(15)  # Initial wait
            # Add a check here for the main window title if possible, or just a longer fixed wait
            # For now, a longer fixed wait:
            # Consider using EnhancedWindowManager.wait_for_main_trading_window here for robustness
            time.sleep(30)  # Additional wait

            print("✅ Login sequence submitted. Main application should be loading.")
            return True

        except Exception as e:
            print(f"❌ Error during automated login input: {e}")
            return False

    def launch_and_login(self, username: str, password: str, executable_path: Optional[str] = None) -> bool:
        """
        Launch ThinkOrSwim and login with credentials.

        Args:
            username: TOS username
            password: TOS password
            executable_path: Optional path to TOS executable

        Returns:
            True if successful, False otherwise
        """
        # Launch TOS
        if not self.launch_tos(executable_path=executable_path):
            return False

        # Login
        return self.login_to_tos(username, password)