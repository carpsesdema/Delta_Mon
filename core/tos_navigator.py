# Delta_Mon/core/tos_navigator.py
from typing import Optional

import pyautogui
import time
import os
import cv2
import numpy as np
import win32gui


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

            screenshot_pil = pyautogui.screenshot(region=(left, top, width, height))
            screenshot_cv = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)
            return screenshot_cv
        except Exception as e:
            print(f"Error taking window/region screenshot: {e}")
            return None

    def capture_upper_left_region(self, filename="debug_upper_left.png", width_ratio=0.3, height_ratio=0.15) -> \
            Optional[str]:
        window_rect = self._get_window_rect()
        if not window_rect:
            print("Cannot capture upper-left region: ToS window rect not found.")
            return None

        win_left, win_top, win_right, win_bottom = window_rect
        window_width = win_right - win_left
        window_height = win_bottom - win_top

        capture_width = int(window_width * width_ratio)
        capture_height = int(window_height * height_ratio)

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
        try:
            img_before = cv2.imread(before_image_path)
            img_after = cv2.imread(after_image_path)

            if img_before is None or img_after is None:
                print("Error: Could not read 'before' or 'after' images for diff.")
                return False

            if img_before.shape != img_after.shape:
                print(
                    f"Warning: 'before' ({img_before.shape}) and 'after' ({img_after.shape}) images have different sizes. Resizing 'before' to match 'after'.")
                img_before = cv2.resize(img_before, (img_after.shape[1], img_after.shape[0]))

            diff = cv2.absdiff(img_before, img_after)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh_diff = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)

            kernel = np.ones((3, 3), np.uint8)
            dilated_diff = cv2.dilate(thresh_diff, kernel, iterations=2)

            contours, _ = cv2.findContours(dilated_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                print("No significant differences found to create a template.")

                cv2.imwrite(os.path.join(self.captures_path, "debug_diff_no_contours.png"), dilated_diff)
                return False

            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)

            padding = 5
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(img_after.shape[1] - x, w + 2 * padding)
            h = min(img_after.shape[0] - y, h + 2 * padding)

            if w < 10 or h < 5 or w > img_after.shape[1] * 0.8 or h > img_after.shape[0] * 0.8:
                print(
                    f"Warning: Calculated template dimensions ({w}x{h}) seem unreasonable. Using a default or skipping.")

                if w > 200 or h > 100:
                    print("Template dimensions too large, likely incorrect diff. Saving debug_diff.png")
                    cv2.imwrite(os.path.join(self.captures_path, "debug_diff_large_template.png"),
                                img_after[y:y + h, x:x + w])
                    return False

            template_roi = img_before[y:y + h, x:x + w]

            template_save_path = os.path.join(self.templates_path, output_template_name)
            cv2.imwrite(template_save_path, template_roi)
            print(f"Template created and saved to: {template_save_path} ({w}x{h})")

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

        search_width = int((win_right - win_left) * region_width_ratio)
        search_height = int((win_bottom - win_top) * region_height_ratio)
        search_region_abs = (win_left, win_top, search_width, search_height)

        region_screenshot_cv = self._get_window_screenshot_cv(region_rect=search_region_abs)
        if region_screenshot_cv is None:
            print(f"Failed to get screenshot of upper-left region for template matching.")
            return None

        result = cv2.matchTemplate(region_screenshot_cv, template_img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:

            match_x_relative_to_window = max_loc[0]
            match_y_relative_to_window = max_loc[1]

            print(
                f"Found '{template_filename}' in upper-left with confidence {max_val:.2f} at window coords ({match_x_relative_to_window}, {match_y_relative_to_window})")
            return (match_x_relative_to_window, match_y_relative_to_window, template_w, template_h)
        else:

            return None

    def click_somewhere_else_to_close_dropdown(self):
        window_rect = self._get_window_rect()
        if not window_rect:
            print("Cannot click to close dropdown: ToS window rect not found.")
            return

        win_left, win_top, win_right, win_bottom = window_rect

        click_x_abs = win_left + int((win_right - win_left) * 0.75)
        click_y_abs = win_top + int((win_bottom - win_top) * 0.5)

        print(f"Clicking at ({click_x_abs}, {click_y_abs}) to close dropdown...")
        pyautogui.click(click_x_abs, click_y_abs)
        time.sleep(0.5)

    def find_element_on_screen(self, template_filename: str, confidence=0.7):
        template_path = os.path.join(self.templates_path, template_filename)
        if not os.path.exists(template_path):
            print(f"Template image not found: {template_path}")
            return None

        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            print(f"Could not read template image: {template_path}")
            return None
        template_h, template_w = template.shape[:2]

        window_image_cv = self._get_window_screenshot_cv()
        if window_image_cv is None:
            return None

        result = cv2.matchTemplate(window_image_cv, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            match_x, match_y = max_loc
            print(f"Found '{template_filename}' with confidence {max_val:.2f} at window coords ({match_x}, {match_y})")
            return (match_x, match_y, template_w, template_h)
        else:

            return None

    def click_account_dropdown(self) -> bool:

        found_element_coords = self.find_element_in_upper_left("account_dropdown_template.png", confidence=0.7)

        if found_element_coords:
            match_x_relative, match_y_relative, template_w, template_h = found_element_coords

            window_rect = self._get_window_rect()
            if not window_rect:
                print("Cannot click dropdown: ToS window rect not found.")
                return False
            win_left, win_top = window_rect[0], window_rect[1]

            click_x_absolute = win_left + match_x_relative + template_w // 2
            click_y_offset_in_template = template_h // 3
            click_y_absolute = win_top + match_y_relative + click_y_offset_in_template

            print(
                f"Clicking account dropdown (template top + 1/3 height) at screen coords: ({click_x_absolute}, {click_y_absolute})")
            pyautogui.click(click_x_absolute, click_y_absolute)
            return True
        else:
            print(
                "Account dropdown template ('account_dropdown_template.png') not found in upper-left region. Run 'Setup Template'.")
            return False

    def capture_dropdown_area(self, filename="debug_dropdown_capture.png",
                              offset_x_from_trigger=0, offset_y_from_trigger_bottom=5,
                              width=300, height=400) -> Optional[str]:
        window_rect = self._get_window_rect()
        if not window_rect:
            print("Cannot capture dropdown: ToS window rect not found.")
            return None
        win_left, win_top = window_rect[0], window_rect[1]

        dropdown_trigger_info = self.find_element_in_upper_left("account_dropdown_template.png",
                                                                confidence=0.65)
        if not dropdown_trigger_info:
            print("Cannot capture dropdown area: 'account_dropdown_template.png' not found. Run 'Setup Template'.")
            return None

        trigger_x_relative, trigger_y_relative, trigger_w, trigger_h = dropdown_trigger_info

        capture_left_absolute = win_left + trigger_x_relative + offset_x_from_trigger
        capture_top_absolute = win_top + trigger_y_relative + trigger_h + offset_y_from_trigger_bottom

        screen_width, screen_height = pyautogui.size()
        capture_width = min(width, screen_width - capture_left_absolute)
        capture_height = min(height, screen_height - capture_top_absolute)

        if capture_width <= 0 or capture_height <= 0:
            print(f"Error: Invalid capture dimensions for dropdown: W={capture_width}, H={capture_height}")
            return None

        save_dir = os.path.join(self.captures_path, 'dropdown_captures')
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