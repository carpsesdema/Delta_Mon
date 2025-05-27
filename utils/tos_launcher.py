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
        self.common_paths = [
            os.path.join(os.path.expanduser('~'), 'Desktop', 'thinkorswim.lnk'),
            os.path.join(os.path.expanduser('~'), 'Desktop', 'thinkorswim.exe'),
            os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles(X86)', 'C:\\Program Files (x86)'), 'thinkorswim',
                         'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Charles Schwab', 'thinkorswim',
                         'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles(X86)', 'C:\\Program Files (x86)'), 'Charles Schwab',
                         'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'TD Ameritrade', 'thinkorswim',
                         'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles(X86)', 'C:\\Program Files (x86)'), 'TD Ameritrade', 'thinkorswim',
                         'thinkorswim.exe'),
        ]
        if os.name != 'nt':
            self.common_paths.extend([
                os.path.join(os.path.expanduser('~'), 'thinkorswim', 'thinkorswim'),
                '/opt/thinkorswim/thinkorswim',
            ])

        # Determine project root to build assets path correctly
        # Assuming this file (tos_launcher.py) is in Delta_Mon/utils/
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_path = os.path.join(project_root, 'assets')
        self.login_templates_path = os.path.join(self.assets_path, 'templates', 'login')

        # Ensure the login templates directory exists
        if not os.path.exists(self.login_templates_path):
            os.makedirs(self.login_templates_path)
            print(f"Created directory: {self.login_templates_path}")
            print(
                f"‼️ IMPORTANT: Please place login template images (login_id_field.png, continue_button.png, etc.) in this directory.")

    def find_tos_executable(self) -> Optional[str]:
        print("🕵️‍♀️ Searching for ThinkOrSwim executable...")
        for path in self.common_paths:
            if os.path.exists(path):
                print(f"✅ Found TOS at common path: {path}")
                return path
            if os.name == 'nt' and path.endswith('.lnk') and os.path.exists(path):
                try:
                    from win32com.client import Dispatch
                    shell = Dispatch("WScript.Shell")
                    shortcut = shell.CreateShortCut(path)
                    target_path = shortcut.TargetPath
                    if os.path.exists(target_path):
                        print(f"✅ Resolved .lnk and found TOS at: {target_path}")
                        return target_path
                except ImportError:
                    print("⚠️ 'pywin32' (win32com) not installed correctly, cannot resolve .lnk files.")
                except Exception as e:
                    print(f"⚠️ Error resolving .lnk {path}: {e}")

        search_roots = [
            os.path.expanduser('~'),
            os.environ.get('ProgramFiles', 'C:\\Program Files'),
            os.environ.get('ProgramFiles(X86)', 'C:\\Program Files (x86)'),
            os.environ.get('LOCALAPPDATA', os.path.join(os.path.expanduser('~'), 'AppData', 'Local')),
            os.environ.get('APPDATA', os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')),
        ]
        if os.name != 'nt':
            search_roots.extend(['/opt', '/Applications'])
        executable_names = ['thinkorswim.exe', 'thinkorswim']

        for root_dir in search_roots:
            if not root_dir or not os.path.exists(root_dir):
                continue
            print(f"🔍 Searching in '{root_dir}'...")
            for dirpath, dirnames, filenames in os.walk(root_dir):
                current_depth = dirpath.count(os.sep) - root_dir.count(os.sep)
                if current_depth > 4:
                    del dirnames[:]
                    continue
                relevant_dirs = [d for d in dirnames if
                                 'thinkorswim' in d.lower() or 'schwab' in d.lower() or 'td ameritrade' in d.lower()]
                if relevant_dirs:
                    dirnames[:] = relevant_dirs
                for exe_name in executable_names:
                    if exe_name in filenames:
                        found_path = os.path.join(dirpath, exe_name)
                        if 'temp' in found_path.lower() or 'cache' in found_path.lower():
                            if not any(rp in found_path for rp in [os.path.join('AppData', 'Local', 'thinkorswim'),
                                                                   os.path.join('AppData', 'Roaming', 'thinkorswim')]):
                                continue
                        print(f"✅ Found TOS during deeper search at: {found_path}")
                        return found_path
        print("❌ TOS executable not found after extensive search.")
        return None

    def launch_tos(self, executable_path: Optional[str] = None) -> bool:
        if not executable_path:
            print("ℹ️ Executable path not provided, attempting to find it...")
            executable_path = self.find_tos_executable()
        if not executable_path or not os.path.exists(executable_path):
            print(f"❌ Cannot launch TOS: Executable not found or path invalid: {executable_path}")
            return False
        try:
            if os.name == 'nt' and executable_path.lower().endswith('.lnk'):
                print(f"🚀 Launching TOS shortcut using os.startfile: {executable_path}")
                os.startfile(executable_path)
            else:
                print(f"🚀 Launching TOS executable: {executable_path}")
                subprocess.Popen([executable_path])
            print(f"✅ TOS launch command sent from: {executable_path}")
            print("⏳ Waiting for ToS launcher/updater to initialize (15s)...")  # Increased for updates
            time.sleep(15)
            return True
        except Exception as e:
            print(f"❌ Error launching TOS from {executable_path}: {e}")
            return False

    def _find_tos_window_by_keywords(self, keywords: list, wait_time: int, exact_match=False) -> Optional[int]:
        print(f"⏳ Searching for window with keywords {keywords} for {wait_time}s (exact: {exact_match})...")
        start_search_time = time.time()
        while time.time() - start_search_time < wait_time:
            hwnds = []

            def callback(hwnd, hwnds_list):
                if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                    window_text = win32gui.GetWindowText(hwnd).lower()
                    match_found = False
                    if exact_match:
                        if any(kw.lower() == window_text for kw in keywords):
                            match_found = True
                    else:  # Partial match
                        if any(kw.lower() in window_text for kw in keywords):
                            match_found = True

                    if match_found:
                        # Avoid matching the main platform if we are looking for login screens
                        if "main@thinkorswim" in window_text and any(
                                login_kw in keywords for login_kw in ["welcome", "login id", "password"]):
                            return True  # This is the main platform, not the login screen we want.

                        hwnds_list.append(hwnd)
                        return False
                return True

            win32gui.EnumWindows(callback, hwnds)
            if hwnds:
                found_hwnd = hwnds[0]
                title_found = win32gui.GetWindowText(found_hwnd)
                print(f"✅ Found window: '{title_found}' (HWND: {found_hwnd})")
                return found_hwnd
            time.sleep(0.5)
        print(f"❌ Window with keywords {keywords} not found within {wait_time}s.")
        return None

    def _click_element_by_template(self, hwnd: int, template_name: str, description: str, confidence=0.8,
                                   grayscale=False, region_offset=(0, 0, 0, 0)) -> bool:
        """Finds an element in the given window (HWND) and clicks it."""
        template_path = os.path.join(self.login_templates_path, template_name)
        if not os.path.exists(template_path):
            print(f"❌ CRITICAL: Template image not found: {template_path}")
            print(
                f"👉 Please create a small screenshot of the '{description}' and save it as '{template_name}' in '{self.login_templates_path}'")
            return False

        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.5)  # Let window come to front

            window_rect = win32gui.GetWindowRect(hwnd)
            # Define search region based on window rect and optional offset
            # region_offset is (left_add, top_add, right_subtract, bottom_subtract)
            search_region = (
                window_rect[0] + region_offset[0],
                window_rect[1] + region_offset[1],
                (window_rect[2] - window_rect[0]) - region_offset[0] - region_offset[2],  # width
                (window_rect[3] - window_rect[1]) - region_offset[1] - region_offset[3]  # height
            )
            if search_region[2] <= 0 or search_region[3] <= 0:
                print(f"⚠️ Invalid search region for {description}: {search_region}. Using full window.")
                search_region = (window_rect[0], window_rect[1], window_rect[2] - window_rect[0],
                                 window_rect[3] - window_rect[1])

            print(
                f"🖼️ Looking for '{description}' ({template_name}) in region {search_region} of window HWND {hwnd}...")
            time.sleep(0.2)  # Brief pause before screenshot

            location = pyautogui.locateCenterOnScreen(template_path, confidence=confidence, region=search_region,
                                                      grayscale=grayscale)

            if location:
                print(f"✅ Found '{description}' at {location}. Clicking...")
                pyautogui.click(location)
                time.sleep(0.75)  # Pause after click
                return True
            else:
                # Try again with grayscale if not already tried
                if not grayscale:
                    print(f"ℹ️ '{description}' not found. Retrying with grayscale...")
                    return self._click_element_by_template(hwnd, template_name, description, confidence, grayscale=True,
                                                           region_offset=region_offset)
                print(f"❌ Could not find '{description}' ({template_name}).")
                return False
        except Exception as e:
            print(f"❌ Error clicking element '{description}': {e}")
            return False

    def login_to_tos(self, username: str, password: str, max_wait_initial: int = 60,
                     max_wait_password: int = 45) -> bool:
        print("🔐 Initiating ToS Login Sequence (Template Matching Mode)...")

        # === Stage 1: Username Entry ===
        print("\n--- Stage 1: Username ---")
        # Wait for the initial "Welcome" or "Login ID" screen.
        # ToS often has an updater first, so wait longer.
        time.sleep(5)  # Extra wait for updater to finish if it runs
        initial_login_titles = ["thinkorswim", "Welcome", "Login ID"]  # Focus on these for first screen
        username_hwnd = self._find_tos_window_by_keywords(initial_login_titles, max_wait_initial)

        if not username_hwnd: return False

        if not self._click_element_by_template(username_hwnd, "login_id_field.png", "Login ID Field",
                                               confidence=0.7): return False
        print(f"⌨️ Typing username...")
        pyautogui.typewrite(username, interval=0.07)
        time.sleep(0.2)
        if not self._click_element_by_template(username_hwnd, "continue_button.png", "Continue Button",
                                               confidence=0.7): return False

        print("✅ Username stage submitted. Waiting for password screen (up to 15s)...")
        time.sleep(15)  # Generous wait for password screen to appear/update

        # === Stage 2: Password Entry ===
        print("\n--- Stage 2: Password ---")
        # Password screen might be same HWND or new. Re-find to be safe.
        # The window title might still be "thinkorswim" or "Welcome", or change to "Password"
        password_screen_titles = ["thinkorswim", "Welcome", "Password", "Enter Password"]
        password_hwnd = self._find_tos_window_by_keywords(password_screen_titles, max_wait_password)

        if not password_hwnd:
            # Fallback: check if the original window is still the one we need
            if username_hwnd and win32gui.IsWindow(username_hwnd) and win32gui.IsWindowVisible(username_hwnd):
                print(f"ℹ️ New password window not found. Re-checking original window (HWND {username_hwnd}).")
                password_hwnd = username_hwnd
            else:
                print("❌ Password screen not found and original window is gone.")
                return False

        if not self._click_element_by_template(password_hwnd, "password_field.png", "Password Field",
                                               confidence=0.7): return False
        print(f"⌨️ Typing password...")
        pyautogui.typewrite(password, interval=0.07)
        time.sleep(0.2)
        if not self._click_element_by_template(password_hwnd, "final_login_button.png", "Final Log In Button",
                                               confidence=0.7): return False

        print("✅ Password stage submitted.")
        return True

    def launch_and_login(self, username: str, password: str, executable_path: Optional[str] = None) -> bool:
        if not self.launch_tos(executable_path=executable_path):
            return False
        return self.login_to_tos(username, password)