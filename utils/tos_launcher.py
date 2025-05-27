# utils/tos_launcher.py

import os
import time
import subprocess
import pyautogui
import win32gui
import win32con
from typing import Optional, Tuple


class TosLauncher:
    def __init__(self):
        self.common_paths = [
            os.path.join(os.path.expanduser('~'), 'Desktop', 'thinkorswim.lnk'),
            os.path.join(os.path.expanduser('~'), 'Desktop', 'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles(X86)', 'C:\\Program Files (x86)'), 'thinkorswim',
                         'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles(X86)', 'C:\\Program Files (x86)'), 'Charles Schwab',
                         'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Charles Schwab', 'thinkorswim',
                         'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles(X86)', 'C:\\Program Files (x86)'), 'TD Ameritrade', 'thinkorswim',
                         'thinkorswim.exe'),
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'TD Ameritrade', 'thinkorswim',
                         'thinkorswim.exe'),
            os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('APPDATA', ''), 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('APPDATA', ''), 'Charles Schwab', 'thinkorswim', 'thinkorswim.exe'),
            os.path.join(os.environ.get('APPDATA', ''), 'TD Ameritrade', 'thinkorswim', 'thinkorswim.exe'),
        ]
        if os.name != 'nt':
            self.common_paths.extend([
                os.path.join(os.path.expanduser('~'), 'thinkorswim', 'thinkorswim'),
                '/opt/thinkorswim/thinkorswim',
                '/Applications/thinkorswim/thinkorswim.app/Contents/MacOS/thinkorswim',
            ])

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_path = os.path.join(project_root, 'assets')
        self.login_templates_path = os.path.join(self.assets_path, 'templates')

        if not os.path.exists(self.login_templates_path):
            os.makedirs(self.login_templates_path)
            print(f"Created directory: {self.login_templates_path}")
            print(f"‼️ IMPORTANT: Please place login template images in this directory.")

        self.updater_keywords = ["updater", "loading", "installing", "thinkorswim client loader",
                                 "starting thinkorswim", "downloading", "applying", "extracting"]

    def find_tos_executable(self) -> Optional[str]:
        print("🕵️‍♀️ Searching for ThinkOrSwim executable (verbose)...")

        for path_candidate in self.common_paths:
            normalized_path = os.path.normpath(path_candidate)
            print(f"\n   [Path Check] Trying common path: '{normalized_path}'")

            exists = os.path.exists(normalized_path)
            print(f"      os.path.exists() returned: {exists}")

            if exists:
                if os.name == 'nt' and normalized_path.lower().endswith('.lnk'):
                    print(f"      Path is a .lnk file. Attempting to resolve target...")
                    try:
                        from win32com.client import Dispatch
                        shell = Dispatch("WScript.Shell")
                        shortcut = shell.CreateShortCut(normalized_path)
                        target_path = shortcut.TargetPath
                        print(f"      .lnk target path: '{target_path}'")

                        target_exists = os.path.exists(target_path)
                        print(f"      Target os.path.exists() returned: {target_exists}")
                        if target_exists:
                            print(f"✅ Found TOS (via .lnk): '{target_path}'")
                            return target_path
                        else:
                            print(f"      ⚠️ .lnk target '{target_path}' does not exist. Skipping this .lnk.")
                    except ImportError:
                        print(
                            "      ⚠️ 'pywin32' (win32com) not installed. Cannot resolve .lnk. Will try to use .lnk directly if no other .exe found.")
                    except Exception as e:
                        print(f"      ⚠️ Error resolving .lnk '{normalized_path}': {e}. Skipping this .lnk.")
                else:
                    print(f"✅ Found TOS (direct path): '{normalized_path}'")
                    return normalized_path

        if os.name == 'nt':
            print("\n   [LNK Fallback Check] Reviewing .lnk paths again in case pywin32 was missing...")
            for path_candidate in self.common_paths:
                normalized_path = os.path.normpath(path_candidate)
                if normalized_path.lower().endswith('.lnk') and os.path.exists(normalized_path):
                    print(
                        f"      Found existing .lnk file: '{normalized_path}'. Considerring this as a fallback if pywin32 was unavailable.")
                    print(f"✅ Using .lnk path directly (os.startfile might handle it): '{normalized_path}'")
                    return normalized_path

        print("\n❌ TOS executable not found in any common locations after verbose search.")
        print("💡 Please ensure ToS is installed or provide the path manually via '✏️ Edit Credentials' in the UI.")
        return None

    def launch_tos(self, executable_path: Optional[str] = None) -> bool:
        print(f"\n[Launch Control] launch_tos called. Provided executable_path: '{executable_path}'")
        if not executable_path:
            print("   Provided executable_path is None. Calling find_tos_executable()...")
            executable_path = self.find_tos_executable()

        if not executable_path:
            print("❌ [Launch Control] Cannot launch TOS: Executable path could not be determined.")
            return False

        normalized_path = os.path.normpath(executable_path)
        print(f"ℹ️ [Launch Control] Attempting to launch TOS using resolved path: '{normalized_path}'")

        if not os.path.exists(normalized_path):
            print(f"❌ CRITICAL [Launch Control]: The executable path does not exist: '{normalized_path}'")
            return False

        try:
            if os.name == 'nt':
                print(f"🚀 [Launch Control] Launching TOS on Windows: '{normalized_path}' using os.startfile()")
                os.startfile(normalized_path)
            else:
                print(f"🚀 [Launch Control] Launching TOS on non-Windows: '{normalized_path}' using subprocess.Popen()")
                if not os.access(normalized_path, os.X_OK):
                    print(f"   ⚠️ Path is not executable: '{normalized_path}'. Attempting to set +x.")
                    try:
                        os.chmod(normalized_path, 0o755)
                        print(f"   ✅ Set +x on '{normalized_path}'")
                    except Exception as chmod_e:
                        print(f"   ❌ Failed to set +x on '{normalized_path}': {chmod_e}. Proceeding...")
                subprocess.Popen([normalized_path])

            print(f"✅ [Launch Control] TOS launch command sent for: '{normalized_path}'")

            print("⏳ [Launch Control] Initial short wait for process to spawn (5s)...")
            time.sleep(5)

            print("🕵️ [Launch Control] Searching for ToS updater/loader window (up to 30s)...")
            updater_hwnd = self._find_tos_window_by_keywords(self.updater_keywords, wait_time=30)

            if updater_hwnd:
                updater_title = win32gui.GetWindowText(updater_hwnd)
                print(
                    f"📊 [Launch Control] Found updater/loader window: '{updater_title}'. Waiting for it to close (timeout 180s)...")
                wait_for_updater_start = time.time()
                max_updater_wait = 180
                while win32gui.IsWindow(updater_hwnd) and win32gui.IsWindowVisible(updater_hwnd):
                    if time.time() - wait_for_updater_start > max_updater_wait:
                        print("❌ [Launch Control] Timeout waiting for updater window to close.")
                        break
                    print(
                        f"   Waiting for updater '{updater_title}' to close... ({int(time.time() - wait_for_updater_start)}s / {max_updater_wait}s)")
                    time.sleep(2)
                if not (win32gui.IsWindow(updater_hwnd) and win32gui.IsWindowVisible(updater_hwnd)):
                    print("✅ [Launch Control] Updater window appears to have closed.")
                else:
                    print("⚠️ [Launch Control] Updater window might still be open after timeout.")
            else:
                print(
                    "ℹ️ [Launch Control] No specific updater/loader window found quickly. Assuming direct to login or brief load.")
                print("   Proceeding with a moderate wait for login screen (15s)...")
                time.sleep(15)

            print("✅ [Launch Control] Initial launch and updater wait phase complete.")
            return True

        except FileNotFoundError:
            print(f"❌ Error [Launch Control]: FileNotFoundError. Path: '{normalized_path}'.")
            return False
        except PermissionError:
            print(f"❌ Error [Launch Control]: PermissionError. Path: '{normalized_path}'.")
            return False
        except Exception as e:
            print(f"❌ An unexpected error occurred launching TOS from '{normalized_path}': {e}")
            import traceback
            print(traceback.format_exc())
            return False

    def _wait_for_window_to_close(self, hwnd: int, description: str, timeout: int = 30) -> bool:
        """Waits for a specific window (by HWND) to close or become invisible."""
        print(f"⏳ Waiting for '{description}' window (HWND: {hwnd}) to close (timeout: {timeout}s)...")
        start_wait = time.time()
        while win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):  # Check both IsWindow and IsWindowVisible
            if time.time() - start_wait > timeout:
                print(f"❌ Timeout waiting for '{description}' (HWND: {hwnd}) to close.")
                return False
            time.sleep(0.5)
            # Removed the repetitive "Still waiting" log from here to reduce noise, timeout message is enough.
        print(f"✅ '{description}' window (HWND: {hwnd}) appears to have closed or become invisible.")
        return True

    def _find_tos_window_by_keywords(self, keywords: list, wait_time: int, exact_match=False) -> Optional[int]:
        print(f"⏳ Searching for window with keywords {keywords} for {wait_time}s (exact: {exact_match})...")
        start_search_time = time.time()
        iteration_count = 0
        while time.time() - start_search_time < wait_time:
            iteration_count += 1
            hwnds = []
            enumerated_windows_titles = []

            def callback(hwnd, hwnds_list):
                if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                    window_text_raw = win32gui.GetWindowText(hwnd)
                    window_text = window_text_raw.lower()
                    enumerated_windows_titles.append(window_text_raw)

                    match_found = False
                    if exact_match:
                        if any(kw.lower() == window_text for kw in keywords):
                            match_found = True
                    else:
                        if any(kw.lower() in window_text for kw in keywords):
                            match_found = True

                    if match_found:
                        is_early_stage_search = any(upd_kw.lower() in [k.lower() for k in keywords] for upd_kw in
                                                    self.updater_keywords + ["login", "logon", "password", "welcome",
                                                                             "authenticating"])

                        if "main@thinkorswim" in window_text and is_early_stage_search:
                            # print(f"   Skipping main platform window '{window_text_raw}' during early stage (updater/login) search.")
                            return True
                        hwnds_list.append(hwnd)
                        return False
                return True

            win32gui.EnumWindows(callback, hwnds)

            if iteration_count > 1 and iteration_count % 20 == 0:
                # print(f"   [Debug Enum - Iter {iteration_count}] Visible windows: {list(set(enumerated_windows_titles[:10]))}...")
                pass  # Reduce noise

            if hwnds:
                found_hwnd = hwnds[0]
                title_found = win32gui.GetWindowText(found_hwnd)
                print(
                    f"✅ Found window: '{title_found}' (HWND: {found_hwnd}) after {time.time() - start_search_time:.2f}s")
                return found_hwnd
            time.sleep(0.25)

        print(f"❌ Window with keywords {keywords} not found within {wait_time}s.")
        if enumerated_windows_titles:
            print(f"   [Debug Enum - Final] Last seen visible windows: {list(set(enumerated_windows_titles[:15]))}...")
        else:
            print(f"   [Debug Enum - Final] No visible windows enumerated that matched basic criteria.")
        return None

    def _click_element_by_template(self, hwnd: int, template_name: str, description: str,
                                   confidence=0.75, grayscale=False) -> bool:
        template_path = os.path.join(self.login_templates_path, template_name)
        if not os.path.exists(template_path):
            print(f"❌ CRITICAL: Template image not found: {template_path}")
            return False

        try:
            # print(f"🎯 Attempting to focus window HWND: {hwnd} for '{description}'") # Reduced noise
            if not win32gui.IsWindow(hwnd):  # Check if HWND is still valid before trying to use it
                print(f"❌ Window HWND {hwnd} is no longer valid before attempting to focus for '{description}'.")
                return False
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)  # Reduced sleep

            active_hwnd = win32gui.GetForegroundWindow()
            if active_hwnd != hwnd:
                # print(f"⚠️ Window HWND {hwnd} not focused (active is {active_hwnd}). Retrying for '{description}'.") # Reduced noise
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.3)  # Reduced sleep
                active_hwnd = win32gui.GetForegroundWindow()
                if active_hwnd != hwnd:
                    print(f"❌ CRITICAL: Failed to focus window HWND {hwnd} for '{description}'.")
                    return False

            # print(f"👍 Window HWND {hwnd} focused for '{description}'.") # Reduced noise

            window_rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = window_rect
            width = right - left
            height = bottom - top

            if width <= 0 or height <= 0:
                print(
                    f"❌ Invalid window dimensions for HWND {hwnd}: W={width}, H={height}. Cannot search for '{description}'.")
                return False

            search_region_for_pyautogui = (left, top, width, height)
            # print(f"🖼️ Looking for '{description}' ({template_name}) in window region {search_region_for_pyautogui}...") # Reduced noise

            # time.sleep(0.1) # Reduced sleep

            location = pyautogui.locateCenterOnScreen(template_path,
                                                      confidence=confidence,
                                                      region=search_region_for_pyautogui,
                                                      grayscale=grayscale)

            if location:
                print(f"✅ Found '{description}' at screen coordinates {location}. Clicking...")
                pyautogui.click(location)
                time.sleep(0.5)  # Keep this pause after click
                return True
            else:
                if not grayscale:  # Try grayscale only once
                    # print(f"ℹ️ '{description}' not found. Retrying with grayscale=True...") # Reduced noise
                    return self._click_element_by_template(hwnd, template_name, description, confidence, True)

                print(
                    f"❌ Could not find '{description}' ({template_name}) in window HWND {hwnd} (Confidence: {confidence}, Grayscale: {grayscale}).")
                debug_capture_path = os.path.join(self.assets_path, "captures",
                                                  f"debug_template_fail_{description.replace(' ', '_')}_{int(time.time())}.png")
                try:
                    pyautogui.screenshot(debug_capture_path, region=search_region_for_pyautogui)
                    print(f"   📸 Debug screenshot of window HWND {hwnd} saved to: {debug_capture_path}")
                except Exception as capture_err:
                    print(f"   ⚠️ Could not save debug screenshot for HWND {hwnd}: {capture_err}")
                return False
        except Exception as e:
            if not win32gui.IsWindow(hwnd):  # Check if the window disappeared during operations
                print(f"❌ Window HWND {hwnd} became invalid during operations for '{description}'. Error: {e}")
            else:
                print(f"❌ Error clicking element '{description}' in window HWND {hwnd}: {e}")
            # import traceback # Keep for deeper debugging if needed
            # print(traceback.format_exc())
            return False

    def login_to_tos(self, username: str, password: str, max_wait_login_prompt: int = 30,
                     max_wait_password_prompt: int = 30,  # Kept this generous
                     ui_transition_pause: float = 3.0) -> bool:  # Pause for UI to change
        print("🔐 Initiating ToS Login Sequence (Window Transformation Logic)...")
        typing_interval = 0.07

        # --- Stage 1: Username Entry ---
        print("\n--- Stage 1: Username ---")
        print(f"⏳ Searching for initial login prompt window (up to {max_wait_login_prompt}s)...")
        initial_login_titles = ["thinkorswim", "Welcome", "Login ID", "Logon to thinkorswim"]
        login_window_hwnd = self._find_tos_window_by_keywords(initial_login_titles, max_wait_login_prompt)

        if not login_window_hwnd:
            print("❌ Initial login prompt window not found. Cannot proceed.")
            return False

        login_window_description = f"Login Window (HWND: {login_window_hwnd}, Title: '{win32gui.GetWindowText(login_window_hwnd)}')"
        print(f"ℹ️ Using {login_window_description} for username and password stages.")

        if not self._click_element_by_template(login_window_hwnd, "login_id_field.png", "Login ID Field",
                                               confidence=0.7):
            print(f"❌ Could not find or click 'Login ID Field' in {login_window_description}.")
            return False
        print(f"⌨️ Typing username into {login_window_description}...")
        pyautogui.typewrite(username, interval=typing_interval)
        time.sleep(0.2)

        if not self._click_element_by_template(login_window_hwnd, "continue_button.png", "Continue Button",
                                               confidence=0.7):
            print(
                f"ℹ️ 'Continue Button' template not found in {login_window_description}. Attempting to press Enter as fallback...")
            pyautogui.press('enter')

        print(f"✅ Username submitted for {login_window_description}.")
        print(f"⏸️ Pausing {ui_transition_pause}s for UI to transition to password prompt...")
        time.sleep(ui_transition_pause)

        # --- Stage 2: Password Entry (using the same login_window_hwnd) ---
        print("\n--- Stage 2: Password ---")

        # Verify the window handle is still valid before proceeding
        if not win32gui.IsWindow(login_window_hwnd) or not win32gui.IsWindowVisible(login_window_hwnd):
            print(
                f"❌ {login_window_description} is no longer valid or visible before password entry. Searching for new password window...")
            # Optionally, try to re-find a password window here if needed, though user implies it's the same one
            password_screen_titles = ["thinkorswim", "Welcome", "Password", "Enter Password", "Logon to thinkorswim",
                                      "challenge questions"]
            login_window_hwnd = self._find_tos_window_by_keywords(password_screen_titles, max_wait_password_prompt)
            if not login_window_hwnd:
                print("❌ Could not find a suitable window for password entry.")
                return False
            login_window_description = f"Password Window (Re-found) (HWND: {login_window_hwnd}, Title: '{win32gui.GetWindowText(login_window_hwnd)}')"
            print(f"ℹ️ Using re-found {login_window_description} for password stage.")

        if not self._click_element_by_template(login_window_hwnd, "password_field.png", "Password Field",
                                               confidence=0.7):
            print(f"❌ Could not find or click 'Password Field' in {login_window_description}.")
            return False
        print(f"⌨️ Typing password into {login_window_description}...")
        pyautogui.typewrite(password, interval=typing_interval)
        time.sleep(0.2)

        if not self._click_element_by_template(login_window_hwnd, "final_login_button.png",
                                               "Final Log In Button", confidence=0.7):
            print(
                f"ℹ️ 'Final Log In Button' template not found in {login_window_description}. Attempting to press Enter as fallback...")
            pyautogui.press('enter')

        print(f"✅ Password submitted for {login_window_description}.")

        # Now, wait for the login window to ACTUALLY close as the main platform loads
        if not self._wait_for_window_to_close(login_window_hwnd, login_window_description + " (post-final login)",
                                              timeout=45):  # Generous timeout
            print(
                f"⚠️ {login_window_description} did not close after final login submission. Main platform might be loading, or login failed.")
            # At this point, login might have failed, or it's just slow.
            # The next step in the main app (finding main trading window) will be the ultimate test.
        else:
            print(f"✅ {login_window_description} closed after final login. Expecting main platform.")

        print("✅ Login sequence interaction completed.")
        return True

    def launch_and_login(self, username: str, password: str, executable_path: Optional[str] = None) -> bool:
        if not self.launch_tos(executable_path=executable_path):
            print("❌ ToS launch (including updater wait) failed, aborting login.")
            return False

        print("ℹ️ Launch phase complete. Proceeding to login interaction...")
        return self.login_to_tos(username, password)