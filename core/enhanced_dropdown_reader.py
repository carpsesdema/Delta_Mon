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
    """
    Reads account names from the ToS dropdown, specifically designed to handle
    long lists that require scrolling.
    """
    TRIGGER_TEMPLATE_NAME = "account_trigger.png"

    # Define a generous area to capture below where the trigger is clicked.
    # This should be large enough to contain the entire visible portion of the dropdown.
    CAPTURE_OFFSET_X = -20  # Start capture slightly left of the trigger text
    CAPTURE_OFFSET_Y = 25  # Start capture below the trigger bar
    CAPTURE_WIDTH = 350
    CAPTURE_HEIGHT = 500

    SCROLL_AMOUNT = -500  # A large negative value for a significant scroll down
    SCROLL_PAUSE = 0.75  # Time to wait for the UI to update after scrolling

    def __init__(self, tos_navigator: TosNavigator):
        self.tos_navigator = tos_navigator
        self.ocr_utils = OCRUtils()

    def read_all_accounts_from_dropdown(self, save_debug: bool = True) -> List[str]:
        """
        Orchestrates the entire process of finding, clicking, scrolling,
        and reading all accounts from the dropdown list.
        """
        print("🔍 Reading all accounts using scroll-and-capture method...")

        trigger_location = self._find_and_click_trigger()
        if not trigger_location:
            print("❌ Failed to find and click the dropdown trigger. Aborting.")
            return []

        # Wait for the dropdown to fully open
        time.sleep(1.5)

        all_accounts = set()
        last_known_count = -1  # Start at -1 to ensure the first loop runs

        # Loop a max of 15 times (should be more than enough for any list)
        for i in range(15):
            print(f"--- Capture & Scroll Attempt #{i + 1} ---")

            # Capture the current view of the dropdown
            capture_path = self._capture_dropdown_area(trigger_location, i, save_debug)
            if not capture_path:
                print("⚠️ Failed to capture dropdown area, stopping scroll.")
                break

            # Read the text from the captured image
            accounts_in_view = self.ocr_utils.extract_account_names(capture_path)
            if accounts_in_view:
                print(f"   Found {len(accounts_in_view)} potential names in this view.")
                for acc in accounts_in_view:
                    all_accounts.add(acc)
            else:
                print("   No text found in this view.")

            # Check if we've reached the end of the list
            if len(all_accounts) == last_known_count:
                print("✅ No new accounts found after scrolling. Assuming end of list.")
                break

            last_known_count = len(all_accounts)
            print(f"   Total unique accounts so far: {last_known_count}")

            # Scroll for the next iteration
            self._scroll_dropdown(trigger_location)
            time.sleep(self.SCROLL_PAUSE)

        self._close_dropdown(trigger_location)

        if not all_accounts:
            print("❌ No accounts were extracted. Please check the trigger template and OCR settings.")
            return []

        final_list = sorted(list(all_accounts))
        print(f"✅🎉 Success! Found a total of {len(final_list)} unique accounts from dropdown.")
        return final_list

    def _find_and_click_trigger(self) -> Optional[Tuple[int, int]]:
        """Finds the 'Account:' trigger on screen using a template and clicks it."""
        print(f"🎯 Searching for trigger template: '{self.TRIGGER_TEMPLATE_NAME}'...")
        template_path = os.path.join(self.tos_navigator.templates_path, self.TRIGGER_TEMPLATE_NAME)

        if not os.path.exists(template_path):
            print(f"❌ CRITICAL: Trigger template not found at {template_path}")
            print("   Please ensure the screenshot is saved in the correct assets/templates/ folder.")
            return None

        try:
            # Locate the center of the template on the screen with high confidence
            location = pyautogui.locateCenterOnScreen(template_path, confidence=0.8)
            if location:
                print(f"   ✅ Found trigger at screen coordinates: {location}. Clicking...")
                pyautogui.click(location)
                return location
            else:
                print(f"   ❌ Could not locate the trigger template '{self.TRIGGER_TEMPLATE_NAME}' on the screen.")
                print("      - Is the ToS window visible and not obstructed?")
                print("      - Is the template image a clear, cropped screenshot?")
                return None
        except Exception as e:
            print(f"❌ An error occurred during template matching: {e}")
            return None

    def _capture_dropdown_area(self, trigger_location: Tuple[int, int], attempt: int, save_debug: bool) -> Optional[
        str]:
        """Captures a fixed-size area below the trigger location."""
        # Calculate the top-left corner of our capture zone
        # *** FIX: Convert NumPy int64 to standard Python int ***
        capture_x = int(trigger_location[0] + self.CAPTURE_OFFSET_X)
        capture_y = int(trigger_location[1] + self.CAPTURE_OFFSET_Y)

        capture_region = (capture_x, capture_y, self.CAPTURE_WIDTH, self.CAPTURE_HEIGHT)
        print(f"   📸 Capturing dropdown area: {capture_region}")

        save_dir = os.path.join(self.tos_navigator.captures_path, 'dropdown_scroll_captures')
        os.makedirs(save_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        save_path = os.path.join(save_dir, f'dropdown_view_{attempt}_{timestamp}.png')

        try:
            screenshot = pyautogui.screenshot(region=capture_region)
            if save_debug:
                screenshot.save(save_path)
                print(f"      💾 Debug image saved to: {os.path.basename(save_path)}")
            return save_path
        except Exception as e:
            print(f"   ❌ Error capturing dropdown area: {e}")
            return None

    def _scroll_dropdown(self, trigger_location: Tuple[int, int]):
        """Scrolls the mouse wheel down while the cursor is over the dropdown area."""
        # Move mouse over the capture area to ensure it has focus for scrolling
        # *** FIX: Convert NumPy int64 to standard Python int ***
        scroll_target_x = int(trigger_location[0])
        scroll_target_y = int(trigger_location[1] + self.CAPTURE_OFFSET_Y + 50)

        print(f"   📜 Scrolling down at ({scroll_target_x}, {scroll_target_y})...")
        pyautogui.moveTo(scroll_target_x, scroll_target_y)
        pyautogui.scroll(self.SCROLL_AMOUNT)

    def _close_dropdown(self, trigger_location: Tuple[int, int]):
        """Closes the dropdown by clicking the trigger again or clicking away."""
        print("   🖱️ Closing dropdown menu...")
        try:
            # A reliable way to close it is to just click the trigger again
            pyautogui.click(trigger_location)
            time.sleep(0.5)
        except Exception as e:
            print(f"   ⚠️ Could not click to close dropdown: {e}")


class DropdownAccountDiscovery:
    """A wrapper class to simplify the process of discovering accounts for the UI."""

    def __init__(self, tos_navigator: Optional[TosNavigator] = None):
        if tos_navigator:
            self.tos_navigator = tos_navigator
        else:
            # This fallback is for standalone testing of the script
            from core.window_manager import WindowManager
            print("ℹ️ DropdownAccountDiscovery creating its own WindowManager and TosNavigator.")
            # Use the robust manager
            from core.enhanced_window_manager import EnhancedWindowManager
            self.window_manager = EnhancedWindowManager()
            status_report = self.window_manager.get_tos_status_report()
            if not status_report['main_trading_available']:
                raise RuntimeError("ToS main trading window not found.")

            if not self.window_manager.focus_tos_window():
                print("⚠️ Warning: Could not focus ToS window.")
            self.tos_navigator = TosNavigator(self.window_manager.hwnd)

        self.dropdown_reader = EnhancedDropdownReader(self.tos_navigator)
        self.discovered_accounts = []

    def discover_all_accounts(self, status_callback=None) -> List[str]:
        def update_status(message: str):
            print(message)
            if status_callback:
                status_callback(message)

        try:
            update_status("🔍 Starting scroll-and-capture account discovery...")
            self.discovered_accounts = self.dropdown_reader.read_all_accounts_from_dropdown(save_debug=True)

            if self.discovered_accounts:
                update_status(f"✅ Successfully discovered {len(self.discovered_accounts)} accounts!")
                for i, account in enumerate(self.discovered_accounts, 1):
                    update_status(f"   {i:2d}. {account}")
            else:
                update_status("❌ No accounts found. Check logs and debug captures.")
            return self.discovered_accounts
        except Exception as e:
            update_status(f"❌ Discovery error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_discovered_accounts(self) -> List[str]:
        return self.discovered_accounts.copy()