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
        # Common installation paths
        self.common_paths = [
            os.path.join(os.path.expanduser('~'), 'Desktop', 'thinkorswim.exe'),
            os.path.join(os.path.expanduser('~'), 'Desktop', 'thinkorswim'),
            os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'thinkorswim',
                         'thinkorswim.exe'),
            # Add more common paths as needed
        ]

    def find_tos_executable(self) -> Optional[str]:
        """
        Find the ThinkOrSwim executable path.

        Returns:
            Path to TOS executable or None if not found
        """
        # Check common paths first
        for path in self.common_paths:
            if os.path.exists(path):
                print(f"Found TOS at common path: {path}")
                return path

        # Try searching in common locations
        search_locations = [
            os.path.expanduser('~'),
            os.path.join(os.path.expanduser('~'), 'Desktop'),
            os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
            os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'),
            os.environ.get('APPDATA', ''),
            os.environ.get('LOCALAPPDATA', '')
        ]

        for location in search_locations:
            if not location or not os.path.exists(location):
                continue

            for root, dirs, files in os.walk(location):
                # Don't search too deep to avoid performance issues
                if root.count(os.path.sep) - location.count(os.path.sep) > 3:
                    continue

                for file in files:
                    if file.lower() in ['thinkorswim.exe', 'thinkorswim']:
                        path = os.path.join(root, file)
                        print(f"Found TOS at: {path}")
                        return path

        print("TOS executable not found")
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
            executable_path = self.find_tos_executable()

        if not executable_path:
            print("Cannot launch TOS: Executable not found")
            return False

        try:
            # Launch the application
            subprocess.Popen([executable_path])
            print(f"Launched TOS from: {executable_path}")

            # Wait for the application to start
            time.sleep(5)
            return True

        except Exception as e:
            print(f"Error launching TOS: {e}")
            return False

    def login_to_tos(self, username: str, password: str, max_wait: int = 30) -> bool:
        """
        Login to ThinkOrSwim with credentials.

        Args:
            username: TOS username
            password: TOS password
            max_wait: Maximum time to wait for login window

        Returns:
            True if login successful, False otherwise
        """
        print("Attempting to login to ThinkOrSwim...")

        # Wait for login window to appear
        login_window_found = False
        login_hwnd = None

        start_time = time.time()
        while time.time() - start_time < max_wait:
            # Find window by title (adjust as needed based on actual TOS login window title)
            login_hwnd = win32gui.FindWindow(None, "thinkorswim Login")

            if not login_hwnd:
                # Try alternative title
                login_hwnd = win32gui.FindWindow(None, "Login - thinkorswim")

            if login_hwnd:
                login_window_found = True
                break

            time.sleep(1)

        if not login_window_found:
            print("Login window not found after timeout")
            return False

        # Focus the login window
        win32gui.SetForegroundWindow(login_hwnd)
        time.sleep(1)

        try:
            # Enter username
            pyautogui.typewrite(username)
            pyautogui.press('tab')
            time.sleep(0.5)

            # Enter password
            pyautogui.typewrite(password)
            time.sleep(0.5)

            # Click login button (typically Enter works)
            pyautogui.press('enter')

            # Wait for main application to load
            time.sleep(10)

            print("Login sequence completed")
            return True

        except Exception as e:
            print(f"Error during login: {e}")
            return False

    def launch_and_login(self, username: str, password: str) -> bool:
        """
        Launch ThinkOrSwim and login with credentials.

        Args:
            username: TOS username
            password: TOS password

        Returns:
            True if successful, False otherwise
        """
        # Launch TOS
        if not self.launch_tos():
            return False

        # Login
        return self.login_to_tos(username, password)