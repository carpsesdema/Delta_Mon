# Delta_Mon/core/tos_navigator.py

import pyautogui
import time
import os
import cv2  # OpenCV for template matching
import numpy as np
import win32gui  # For GetWindowRect


class TosNavigator:
    def __init__(self, hwnd: int):  # Expects a window handle (HWND)
        if not isinstance(hwnd, int) or hwnd == 0:
            raise ValueError("Invalid HWND provided to TosNavigator.")
        self.hwnd = hwnd
        # Correctly determine the project root and then assets path
        # Assuming core/ is one level down from project_root (Delta_Mon/)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_path = os.path.join(project_root, 'assets')

    def _get_window_rect(self) -> tuple[int, int, int, int] | None:
        """Gets the window's screen coordinates (left, top, right, bottom)."""
        try:
            return win32gui.GetWindowRect(self.hwnd)
        except Exception as e:
            print(f"Error getting window rect for HWND {self.hwnd}: {e}")
            return None

    def _get_window_screenshot(self):
        """Takes a screenshot of the ToS window identified by self.hwnd."""
        rect = self._get_window_rect()
        if not rect:
            print("ToS window HWND not valid or rect not found for screenshot.")
            return None

        left, top, right, bottom = rect
        width = right - left
        height = bottom - top

        if width <= 0 or height <= 0:
            # This can happen if the window is minimized completely or has no drawable area
            print(
                f"Invalid window dimensions for screenshot: w={width}, h={height} for HWND {self.hwnd}. Window might be minimized.")
            # Attempt to restore if minimized (though WindowManager should ideally handle focus)
            # if win32gui.IsIconic(self.hwnd):
            #     win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
            #     time.sleep(0.5) # Give time to restore
            #     rect = self._get_window_rect()
            #     if not rect: return None
            #     left, top, right, bottom = rect
            #     width = right - left
            #     height = bottom - top
            #     if width <= 0 or height <= 0:
            #         return None
            return None  # Still return None if dimensions are invalid after attempt

        try:
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return screenshot_cv
        except Exception as e:
            print(f"Error taking window screenshot via PyAutoGUI: {e}")
            return None

    def find_element_on_screen(self, template_filename: str, confidence=0.7):
        """
        Finds an element within the ToS window using template matching.
        Returns the (x, y, w, h) of the found element relative to the window, or None.
        """
        template_path = os.path.join(self.assets_path, 'templates', template_filename)
        if not os.path.exists(template_path):
            print(f"Template image not found: {template_path}")
            # Check if assets_path is correct
            # print(f"DEBUG: Assets path: {self.assets_path}")
            # print(f"DEBUG: Current working directory: {os.getcwd()}")
            # print(f"DEBUG: Calculated template_path: {template_path}")
            return None

        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            print(f"Could not read template image: {template_path}")
            return None

        template_h, template_w = template.shape[:2]

        window_image = self._get_window_screenshot()
        if window_image is None:
            return None

        result = cv2.matchTemplate(window_image, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            match_x, match_y = max_loc
            print(f"Found '{template_filename}' with confidence {max_val:.2f} at window coords ({match_x}, {match_y})")
            return (match_x, match_y, template_w, template_h)
        else:
            print(
                f"Could not find '{template_filename}' with confidence {max_val:.2f} (threshold {confidence}) in window HWND {self.hwnd}")
            return None

    def click_account_dropdown(self) -> bool:
        """
        Finds and clicks the account dropdown trigger.
        Returns True if successful, False otherwise.
        """
        # WindowManager should handle focusing the window before this is called.

        found_element_coords = self.find_element_on_screen("account_dropdown_template.png", confidence=0.7)
        if found_element_coords:
            match_x_relative, match_y_relative, template_w, template_h = found_element_coords

            window_rect = self._get_window_rect()
            if not window_rect:
                print("Cannot click dropdown: ToS window rect not found.")
                return False

            win_left, win_top = window_rect[0], window_rect[1]

            # Calculate absolute screen coordinates for the click (center of the found template)
            click_x_absolute = win_left + match_x_relative + template_w // 2
            click_y_absolute = win_top + match_y_relative + template_h // 2

            print(f"Clicking account dropdown at screen coordinates: ({click_x_absolute}, {click_y_absolute})")
            pyautogui.click(click_x_absolute, click_y_absolute)
            return True
        return False

    def capture_dropdown_area(self, filename="debug_dropdown_capture.png",
                              offset_x_from_trigger=0, offset_y_from_trigger_bottom=5,
                              width=300, height=250) -> str | None:
        """
        Captures a region where the account dropdown is expected to appear,
        relative to the found account dropdown trigger template.
        Returns path to saved image or None.
        """
        window_rect = self._get_window_rect()
        if not window_rect:
            print("Cannot capture dropdown: ToS window rect not found.")
            return None
        win_left, win_top = window_rect[0], window_rect[1]

        # Find the dropdown trigger again to get its precise location for relative capture
        dropdown_trigger_info = self.find_element_on_screen("account_dropdown_template.png", confidence=0.7)
        if not dropdown_trigger_info:
            print("Cannot capture dropdown area: account_dropdown_template.png not found.")
            return None

        trigger_x_relative, trigger_y_relative, trigger_w, trigger_h = dropdown_trigger_info

        # Calculate capture region in absolute screen coordinates
        # Dropdown appears below the trigger
        capture_left_absolute = win_left + trigger_x_relative + offset_x_from_trigger
        capture_top_absolute = win_top + trigger_y_relative + trigger_h + offset_y_from_trigger_bottom

        save_dir = os.path.join(self.assets_path, 'captures')
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)

        try:
            print(
                f"Attempting to capture dropdown region at screen coords: (L:{capture_left_absolute}, T:{capture_top_absolute}, W:{width}, H:{height})")
            screenshot = pyautogui.screenshot(region=(capture_left_absolute, capture_top_absolute, width, height))
            screenshot.save(save_path)
            print(f"Dropdown area captured and saved to: {save_path}")
            return save_path
        except Exception as e:
            print(f"Error capturing dropdown area: {e}")
            # print(f"Details - Region: L={capture_left_absolute}, T={capture_top_absolute}, W={width}, H={height}")
            return None