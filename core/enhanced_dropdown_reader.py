# Delta_Mon/core/enhanced_dropdown_reader.py

import cv2
import numpy as np
import pyautogui
import os
import time
from typing import List, Optional, Tuple, Dict
from core.tos_navigator import TosNavigator
from utils.ocr_utils import OCRUtils


class EnhancedDropdownReader:
    FIXED_TRIGGER_BASE_X_RELATIVE = 404
    FIXED_TRIGGER_BASE_Y_RELATIVE = 16
    ASSUMED_TRIGGER_HEIGHT = 25
    CLICK_OFFSET_X_IN_TRIGGER = 20
    CLICK_OFFSET_Y_IN_TRIGGER = 8

    def __init__(self, tos_navigator: TosNavigator):
        self.tos_navigator = tos_navigator
        self.ocr_utils = OCRUtils()

    def read_all_accounts_from_dropdown(self, save_debug: bool = True) -> List[str]:
        print("🔍 Reading all accounts from dropdown using before/after detection...")

        # Take BEFORE screenshot
        before_path = self._capture_area_before_click()
        if not before_path:
            print("❌ Failed to capture 'before' state")
            return []

        # Click dropdown
        if not self._click_dropdown_trigger():
            print("❌ Failed to click dropdown trigger")
            return []

        print("⏳ Waiting for dropdown to fully expand...")
        time.sleep(2.0)

        # Take AFTER screenshot
        after_path = self._capture_area_after_click()
        if not after_path:
            print("❌ Failed to capture 'after' state")
            return []

        # Find the dropdown by comparing before/after
        dropdown_area = self._find_dropdown_by_difference(before_path, after_path, save_debug)
        if not dropdown_area:
            print("❌ Could not detect dropdown area from difference")
            self._close_dropdown()
            return []

        # Extract accounts from the detected dropdown area
        account_names = self._extract_accounts_from_dropdown_area(dropdown_area, save_debug)

        self._close_dropdown()

        print(f"✅ Successfully extracted {len(account_names)} accounts from dropdown")
        return account_names

    def _capture_area_before_click(self) -> Optional[str]:
        """Capture the area before clicking dropdown"""
        window_rect = self.tos_navigator._get_window_rect()
        if not window_rect:
            return None

        win_left, win_top = window_rect[0], window_rect[1]

        # Capture a wide area around where dropdown might appear
        capture_x = win_left + 50
        capture_y = win_top + 40
        capture_width = 600
        capture_height = 400

        save_dir = os.path.join(self.tos_navigator.captures_path, 'dropdown_captures')
        os.makedirs(save_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        save_path = os.path.join(save_dir, f'before_dropdown_{timestamp}.png')

        try:
            screenshot = pyautogui.screenshot(region=(capture_x, capture_y, capture_width, capture_height))
            screenshot.save(save_path)
            print(f"📸 Before screenshot: {save_path}")
            return save_path
        except Exception as e:
            print(f"❌ Error capturing before state: {e}")
            return None

    def _capture_area_after_click(self) -> Optional[str]:
        """Capture the same area after clicking dropdown"""
        window_rect = self.tos_navigator._get_window_rect()
        if not window_rect:
            return None

        win_left, win_top = window_rect[0], window_rect[1]

        # Same area as before
        capture_x = win_left + 50
        capture_y = win_top + 40
        capture_width = 600
        capture_height = 400

        save_dir = os.path.join(self.tos_navigator.captures_path, 'dropdown_captures')
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        save_path = os.path.join(save_dir, f'after_dropdown_{timestamp}.png')

        try:
            screenshot = pyautogui.screenshot(region=(capture_x, capture_y, capture_width, capture_height))
            screenshot.save(save_path)
            print(f"📸 After screenshot: {save_path}")
            return save_path
        except Exception as e:
            print(f"❌ Error capturing after state: {e}")
            return None

    def _find_dropdown_by_difference(self, before_path: str, after_path: str, save_debug: bool) -> Optional[str]:
        """Find dropdown area by comparing before/after images"""
        try:
            img_before = cv2.imread(before_path)
            img_after = cv2.imread(after_path)

            if img_before is None or img_after is None:
                print("❌ Could not read before/after images")
                return None

            if img_before.shape != img_after.shape:
                print(f"⚠️ Image size mismatch, resizing...")
                img_before = cv2.resize(img_before, (img_after.shape[1], img_after.shape[0]))

            # Find difference
            diff = cv2.absdiff(img_before, img_after)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh_diff = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)

            # Find contours of differences
            kernel = np.ones((5, 5), np.uint8)
            dilated = cv2.dilate(thresh_diff, kernel, iterations=2)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                print("❌ No differences found between before/after images")
                if save_debug:
                    cv2.imwrite(before_path.replace('.png', '_diff_debug.png'), thresh_diff)
                return None

            # Find the largest difference (should be the dropdown)
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Add some padding
            padding = 10
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(img_after.shape[1] - x, w + 2 * padding)
            h = min(img_after.shape[0] - y, h + 2 * padding)

            print(f"🎯 Detected dropdown area: ({x}, {y}) size: {w}x{h}")

            # Extract just the dropdown area from the after image
            dropdown_roi = img_after[y:y + h, x:x + w]

            dropdown_path = before_path.replace('before_dropdown', 'detected_dropdown')
            cv2.imwrite(dropdown_path, dropdown_roi)
            print(f"💾 Dropdown area saved: {dropdown_path}")

            if save_debug:
                # Save debug image showing the detected area
                debug_img = img_after.copy()
                cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 3)
                cv2.imwrite(before_path.replace('.png', '_detected_area.png'), debug_img)

            return dropdown_path

        except Exception as e:
            print(f"❌ Error finding dropdown by difference: {e}")
            import traceback
            print(traceback.format_exc())
            return None

    def _click_dropdown_trigger(self) -> bool:
        print("🎯 Clicking dropdown trigger using fixed relative coordinates...")
        window_rect = self.tos_navigator._get_window_rect()
        if not window_rect:
            print("❌ Cannot click dropdown: ToS window rect not found.")
            return False

        win_left, win_top, _, _ = window_rect

        click_x_absolute = win_left + self.FIXED_TRIGGER_BASE_X_RELATIVE + self.CLICK_OFFSET_X_IN_TRIGGER
        click_y_absolute = win_top + self.FIXED_TRIGGER_BASE_Y_RELATIVE + self.CLICK_OFFSET_Y_IN_TRIGGER

        print(f"🖱️ Clicking dropdown at: ({click_x_absolute}, {click_y_absolute})")
        try:
            pyautogui.click(click_x_absolute, click_y_absolute)
            return True
        except Exception as e:
            print(f"❌ Error clicking dropdown: {e}")
            return False

    def _extract_accounts_from_dropdown_area(self, dropdown_image_path: str, save_debug: bool) -> List[str]:
        """Extract account names from the precisely detected dropdown area"""
        print("🔬 Extracting account names from detected dropdown area...")

        accounts = self.ocr_utils.extract_account_names(dropdown_image_path, debug_save=save_debug)

        if accounts:
            print(f"✅ Found {len(accounts)} accounts:")
            for i, account in enumerate(accounts, 1):
                print(f"   {i}. {account}")
        else:
            print("❌ No accounts extracted from dropdown area")

        return accounts

    def _close_dropdown(self):
        try:
            self.tos_navigator.click_somewhere_else_to_close_dropdown()
            print("🖱️ Clicked to close dropdown")
        except Exception as e:
            print(f"⚠️ Could not close dropdown: {e}")


class DropdownAccountDiscovery:
    def __init__(self, tos_navigator: Optional[TosNavigator] = None):
        if tos_navigator:
            self.tos_navigator = tos_navigator
        else:
            from core.window_manager import WindowManager
            print("ℹ️ DropdownAccountDiscovery creating its own WindowManager and TosNavigator.")
            self.window_manager = WindowManager(
                target_exact_title="Main@thinkorswim [build 1985]",
                exclude_title_substring="DeltaMon"
            )
            tos_hwnd = self.window_manager.find_tos_window()
            if not tos_hwnd:
                raise RuntimeError("ToS window not found.")
            if not self.window_manager.focus_tos_window():
                print("⚠️ Warning: Could not focus ToS window.")
            self.tos_navigator = TosNavigator(tos_hwnd)

        self.dropdown_reader = EnhancedDropdownReader(self.tos_navigator)
        self.discovered_accounts = []

    def discover_all_accounts(self, status_callback=None) -> List[str]:
        def update_status(message: str):
            print(message)
            if status_callback:
                status_callback(message)

        try:
            update_status("🔍 Starting before/after dropdown detection...")
            self.discovered_accounts = self.dropdown_reader.read_all_accounts_from_dropdown(save_debug=True)

            if self.discovered_accounts:
                update_status(f"✅ Successfully discovered {len(self.discovered_accounts)} accounts!")
                for i, account in enumerate(self.discovered_accounts, 1):
                    update_status(f"   {i:2d}. {account}")
            else:
                update_status("❌ No accounts found via before/after detection.")
            return self.discovered_accounts
        except Exception as e:
            update_status(f"❌ Discovery error: {e}")
            return []

    def get_discovered_accounts(self) -> List[str]:
        return self.discovered_accounts.copy()


if __name__ == "__main__":
    print("Enhanced Dropdown Reader - Before/After Detection Test")
    print("=" * 60)
    input("Press Enter to test before/after dropdown detection...")

    try:
        discovery = DropdownAccountDiscovery()
        accounts = discovery.discover_all_accounts()

        if accounts:
            print(f"\n✅ SUCCESS! Found {len(accounts)} accounts:")
            for i, account in enumerate(accounts, 1):
                print(f"   {i:2d}. {account}")
        else:
            print("\n❌ No accounts found.")
    except Exception as e:
        print(f"❌ ERROR: {e}")