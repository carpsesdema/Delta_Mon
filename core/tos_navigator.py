# Delta_Mon/core/tos_navigator.py
from typing import Optional

import pyautogui
import time
import os
import cv2  # OpenCV for template matching
import numpy as np
import win32gui  # For GetWindowRect


class TosNavigator:
    def __init__(self, hwnd: int):
        if not isinstance(hwnd, int) or hwnd == 0:
            raise ValueError("Invalid HWND provided to TosNavigator.")
        self.hwnd = hwnd
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_path = os.path.join(project_root, 'assets')
        self.captures_path = os.path.join(self.assets_path, 'captures')
        self.templates_path = os.path.join(self.assets_path, 'templates')
        os.makedirs(self.captures_path, exist_ok=True)
        os.makedirs(self.templates_path, exist_ok=True)

    def _get_window_rect(self) -> tuple[int, int, int, int] | None:
        try:
            return win32gui.GetWindowRect(self.hwnd)
        except Exception as e:
            print(f"Error getting window rect for HWND {self.hwnd}: {e}")
            return None

    def _get_window_screenshot_cv(self, region_rect=None):
        """Takes a screenshot of the ToS window (or a region) and returns as OpenCV image."""
        target_rect = region_rect if region_rect else self._get_window_rect()
        if not target_rect:
            print("ToS window HWND not valid or rect not found for screenshot.")
            return None

        left, top, right, bottom = target_rect
        width = right - left
        height = bottom - top

        if width <= 0 or height <= 0:
            print(f"Invalid window/region dimensions for screenshot: w={width}, h={height} for HWND {self.hwnd}.")
            return None
        try:
            # Use pyautogui for screenshot, then convert
            screenshot_pil = pyautogui.screenshot(region=(left, top, width, height))
            screenshot_cv = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)
            return screenshot_cv
        except Exception as e:
            print(f"Error taking window/region screenshot: {e}")
            return None

    def capture_upper_left_region(self, filename="debug_upper_left.png", width_ratio=0.3, height_ratio=0.15) -> \
    Optional[str]:
        """Captures the upper-left region of the ToS window."""
        window_rect = self._get_window_rect()
        if not window_rect:
            print("Cannot capture upper-left region: ToS window rect not found.")
            return None

        win_left, win_top, win_right, win_bottom = window_rect
        window_width = win_right - win_left
        window_height = win_bottom - win_top

        capture_width = int(window_width * width_ratio)
        capture_height = int(window_height * height_ratio)

        # Region is absolute screen coordinates
        capture_region_abs = (win_left, win_top, capture_width, capture_height)

        save_path = os.path.join(self.captures_path, filename)

        try:
            print(
                f"Capturing upper-left region: (L:{win_left}, T:{win_top}, W:{capture_width}, H:{capture_height}) to {filename}")
            screenshot = pyautogui.screenshot(region=capture_region_abs)
            screenshot.save(save_path)
            print(f"Upper-left region captured to: {save_path}")
            return save_path
        except Exception as e:
            print(f"Error capturing upper-left region: {e}")
            return None

    def _create_template_from_difference(self, before_image_path: str, after_image_path: str,
                                         output_template_name="account_dropdown_template.png") -> bool:
        """Creates a template by finding the difference between two images."""
        try:
            img_before = cv2.imread(before_image_path)
            img_after = cv2.imread(after_image_path)

            if img_before is None or img_after is None:
                print("Error: Could not read 'before' or 'after' images for diff.")
                return False

            # Resize 'before' to match 'after' if they are different (common if capture area changed)
            if img_before.shape != img_after.shape:
                print(
                    f"Warning: 'before' ({img_before.shape}) and 'after' ({img_after.shape}) images have different sizes. Resizing 'before' to match 'after'.")
                img_before = cv2.resize(img_before, (img_after.shape[1], img_after.shape[0]))

            diff = cv2.absdiff(img_before, img_after)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh_diff = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)

            # Dilate to make the differences more pronounced and connect nearby areas
            kernel = np.ones((3, 3), np.uint8)
            dilated_diff = cv2.dilate(thresh_diff, kernel, iterations=2)

            contours, _ = cv2.findContours(dilated_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                print("No significant differences found to create a template.")
                # Save the diff image for debugging
                cv2.imwrite(os.path.join(self.captures_path, "debug_diff_no_contours.png"), dilated_diff)
                return False

            # Find the largest contour, assuming it's the dropdown trigger
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Add a small padding to the bounding box
            padding = 5
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(img_after.shape[1] - x, w + 2 * padding)
            h = min(img_after.shape[0] - y, h + 2 * padding)

            # Ensure width and height are reasonable for a template
            if w < 10 or h < 5 or w > img_after.shape[1] * 0.8 or h > img_after.shape[0] * 0.8:  # Basic sanity check
                print(
                    f"Warning: Calculated template dimensions ({w}x{h}) seem unreasonable. Using a default or skipping.")
                # Fallback or specific error handling might be needed here.
                # For now, let's try to save it anyway for inspection.
                # If too large, it might be the whole screen diff.
                if w > 200 or h > 100:  # Arbitrary limits for a typical small button/trigger
                    print("Template dimensions too large, likely incorrect diff. Saving debug_diff.png")
                    cv2.imwrite(os.path.join(self.captures_path, "debug_diff_large_template.png"),
                                img_after[y:y + h, x:x + w])
                    return False

            # Crop the template from the 'after' image (which shows the clicked state)
            # Or, more robustly, from the 'before' image if the trigger itself doesn't change much visually but is just a location.
            # Let's try cropping from 'before' as the trigger itself might be static.
            template_roi = img_before[y:y + h, x:x + w]

            template_save_path = os.path.join(self.templates_path, output_template_name)
            cv2.imwrite(template_save_path, template_roi)
            print(f"Template created and saved to: {template_save_path} ({w}x{h})")

            # For debugging, save the diff and contour images
            debug_contour_img = img_after.copy()
            cv2.rectangle(debug_contour_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.imwrite(os.path.join(self.captures_path, "debug_diff_contours.png"), debug_contour_img)
            cv2.imwrite(os.path.join(self.captures_path, "debug_diff_thresholded.png"), dilated_diff)

            return True
        except Exception as e:
            print(f"Error creating template from difference: {e}")
            import traceback
            print(traceback.format_exc())
            return False

    def find_element_in_upper_left(self, template_filename: str, confidence=0.7, region_width_ratio=0.3,
                                   region_height_ratio=0.15):
        """Finds an element in the upper-left region of the ToS window."""
        template_path = os.path.join(self.templates_path, template_filename)
        if not os.path.exists(template_path):
            print(f"Template image not found for upper-left search: {template_path}")
            return None

        template_img = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template_img is None:
            print(f"Could not read template: {template_path}")
            return None
        template_h, template_w = template_img.shape[:2]

        window_rect = self._get_window_rect()
        if not window_rect: return None

        win_left, win_top, win_right, win_bottom = window_rect
        # Define the upper-left region within the window, in absolute screen coordinates
        search_width = int((win_right - win_left) * region_width_ratio)
        search_height = int((win_bottom - win_top) * region_height_ratio)
        search_region_abs = (win_left, win_top, search_width, search_height)

        # Screenshot only the search region for efficiency
        region_screenshot_cv = self._get_window_screenshot_cv(region_rect=search_region_abs)
        if region_screenshot_cv is None:
            print(f"Failed to get screenshot of upper-left region for template matching.")
            return None

        # Perform template matching
        result = cv2.matchTemplate(region_screenshot_cv, template_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            # max_loc is relative to the region_screenshot_cv
            # Convert to be relative to the main window's top-left (0,0)
            # Since search_region_abs starts at (win_left, win_top), and our region_screenshot_cv
            # is that region, max_loc is already relative to the start of that search region.
            # The coordinates returned should be relative to the ToS window's origin.
            # The upper-left search region starts at (0,0) relative to the window.
            match_x_relative_to_window = max_loc[0]
            match_y_relative_to_window = max_loc[1]

            print(
                f"Found '{template_filename}' in upper-left with confidence {max_val:.2f} at window coords ({match_x_relative_to_window}, {match_y_relative_to_window})")
            return (match_x_relative_to_window, match_y_relative_to_window, template_w, template_h)
        else:
            # print(f"Could not find '{template_filename}' in upper-left with confidence {max_val:.2f} (threshold {confidence})")
            return None

    def click_somewhere_else_to_close_dropdown(self):
        """Clicks in a neutral area of the ToS window to close an open dropdown."""
        window_rect = self._get_window_rect()
        if not window_rect:
            print("Cannot click to close dropdown: ToS window rect not found.")
            return

        win_left, win_top, win_right, win_bottom = window_rect

        # Click somewhere typically neutral, e.g., center-right of the window
        # Avoid clicking too close to where the dropdown might be (upper-left)
        click_x_abs = win_left + int((win_right - win_left) * 0.75)  # 75% from left
        click_y_abs = win_top + int((win_bottom - win_top) * 0.5)  # Middle vertically

        print(f"Clicking at ({click_x_abs}, {click_y_abs}) to close dropdown...")
        pyautogui.click(click_x_abs, click_y_abs)
        time.sleep(0.5)  # Allow UI to react

    # --- Methods below are more generic and might be refactored or moved if not specific to ToS Navigator ---

    def find_element_on_screen(self, template_filename: str, confidence=0.7):
        """
        Finds an element within the ENTIRE ToS window using template matching.
        Returns the (x, y, w, h) of the found element relative to the window, or None.
        This is less efficient than region-specific searches if the window is large.
        """
        template_path = os.path.join(self.templates_path, template_filename)
        if not os.path.exists(template_path):
            print(f"Template image not found: {template_path}")
            return None

        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            print(f"Could not read template image: {template_path}")
            return None
        template_h, template_w = template.shape[:2]

        window_image_cv = self._get_window_screenshot_cv()  # Gets screenshot of whole window
        if window_image_cv is None:
            return None

        result = cv2.matchTemplate(window_image_cv, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            match_x, match_y = max_loc  # These are relative to the window's top-left
            print(f"Found '{template_filename}' with confidence {max_val:.2f} at window coords ({match_x}, {match_y})")
            return (match_x, match_y, template_w, template_h)
        else:
            # print(f"Could not find '{template_filename}' in window with conf {max_val:.2f} (thresh {confidence})")
            return None

    def click_account_dropdown(self) -> bool:
        """
        Finds and clicks the account dropdown trigger using the dynamically created template.
        It now uses find_element_in_upper_left for efficiency.
        """
        # This relies on "account_dropdown_template.png" being correctly created by the setup process
        found_element_coords = self.find_element_in_upper_left("account_dropdown_template.png", confidence=0.7)

        if found_element_coords:
            match_x_relative, match_y_relative, template_w, template_h = found_element_coords

            window_rect = self._get_window_rect()
            if not window_rect:
                print("Cannot click dropdown: ToS window rect not found.")
                return False
            win_left, win_top = window_rect[0], window_rect[1]

            # Absolute screen coordinates for the click (center of the found template)
            # The coords from find_element_in_upper_left are already relative to window's (0,0)
            click_x_absolute = win_left + match_x_relative + template_w // 2
            click_y_absolute = win_top + match_y_relative + template_h // 2

            print(
                f"Clicking account dropdown (template center) at screen coords: ({click_x_absolute}, {click_y_absolute})")
            pyautogui.click(click_x_absolute, click_y_absolute)
            return True
        else:
            print(
                "Account dropdown template ('account_dropdown_template.png') not found in upper-left region. Run 'Setup Template'.")
            return False

    def capture_dropdown_area(self, filename="debug_dropdown_capture.png",
                              offset_x_from_trigger=0, offset_y_from_trigger_bottom=5,
                              width=300, height=400) -> Optional[str]:  # Increased default height
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

        dropdown_trigger_info = self.find_element_in_upper_left("account_dropdown_template.png",
                                                                confidence=0.65)  # Slightly lower conf for robustness
        if not dropdown_trigger_info:
            print("Cannot capture dropdown area: 'account_dropdown_template.png' not found. Run 'Setup Template'.")
            return None

        trigger_x_relative, trigger_y_relative, trigger_w, trigger_h = dropdown_trigger_info

        # Calculate capture region in absolute screen coordinates
        # Dropdown appears below and slightly to the right/left of trigger based on offsets
        capture_left_absolute = win_left + trigger_x_relative + offset_x_from_trigger
        capture_top_absolute = win_top + trigger_y_relative + trigger_h + offset_y_from_trigger_bottom

        # Ensure capture area doesn't go off-screen
        screen_width, screen_height = pyautogui.size()
        capture_width = min(width, screen_width - capture_left_absolute)
        capture_height = min(height, screen_height - capture_top_absolute)

        if capture_width <= 0 or capture_height <= 0:
            print(f"Error: Invalid capture dimensions for dropdown: W={capture_width}, H={capture_height}")
            return None

        save_dir = os.path.join(self.captures_path, 'dropdown_captures')  # Specific subfolder
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)

        try:
            print(
                f"Capturing dropdown region at screen coords: (L:{capture_left_absolute}, T:{capture_top_absolute}, W:{capture_width}, H:{capture_height})")
            screenshot = pyautogui.screenshot(
                region=(capture_left_absolute, capture_top_absolute, capture_width, capture_height))
            screenshot.save(save_path)
            print(f"Dropdown area captured and saved to: {save_path}")
            return save_path
        except Exception as e:
            print(f"Error capturing dropdown area: {e}")
            return None