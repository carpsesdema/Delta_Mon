# Delta_Mon/core/tab_detector.py

import cv2
import numpy as np
import pyautogui
import time
import os
from typing import List, Optional, Tuple
from core.tos_navigator import TosNavigator


class TabDetector:
    def __init__(self, tos_navigator: TosNavigator):
        self.tos_navigator = tos_navigator
        self.current_tab_index = 0
        self.total_tabs = 0
        self.tab_positions = []  # This will store the detected tab dicts

    def detect_account_tabs(self) -> List[dict]:
        print("Detecting account tabs...")
        # For Pradeep's setup, the account selection is via a dropdown,
        # not usually by clicking different tabs for different accounts after login.
        # The "tabs" in this context might refer to sections within ToS like "Monitor", "Trade", "Analyze".
        # However, if the goal is to select from the *account dropdown list*,
        # that's handled by EnhancedDropdownReader.

        # This TabDetector might be for navigating main sections of ToS if needed,
        # or it's a legacy component if account switching is solely via dropdown.

        # Let's assume for now this is about detecting main ToS section tabs (Monitor, Trade, etc.)
        # which might be less critical if the primary workflow is account dropdown -> OptionDelta.

        # If this TabDetector IS MEANT to find individual account *tabs* (not dropdown items),
        # then the logic below for finding tab areas and analyzing them would apply.
        # Given the error was "missed the account tab", it implies a click was attempted on a tab.

        # For now, let's keep the existing tab detection logic, assuming it might be used
        # for main ToS tabs or if some accounts *do* appear as tabs.

        tab_area_coords = self._find_tab_area_coordinates()  # Renamed for clarity
        if not tab_area_coords:
            print("Could not locate a general tab area in ToS window.")
            self.tab_positions = []
            return []

        tab_image_path = self._capture_tab_area_image(tab_area_coords)  # Renamed
        if not tab_image_path:
            print("Could not capture the tab area image.")
            self.tab_positions = []
            return []

        self.tab_positions = self._analyze_tab_positions_from_image(tab_image_path, tab_area_coords)  # Renamed

        if self.tab_positions:
            print(f"Detected {len(self.tab_positions)} potential main ToS tabs.")
            for i, tab_info in enumerate(self.tab_positions):
                print(
                    f"  Tab {i}: Name='{tab_info.get('name', 'N/A')}', Center=({tab_info.get('center_x')}, {tab_info.get('center_y')})")
        else:
            print("No main ToS tabs detected or analysis failed.")

        return self.tab_positions

    def _find_tab_area_coordinates(self) -> Optional[Tuple[int, int, int, int]]:
        print("  Locating tab area...")
        # This method would try to find the region where main ToS tabs (Monitor, Trade, etc.) are.
        # It's highly dependent on ToS layout.
        # For now, let's use a plausible estimate.
        window_rect = self.tos_navigator._get_window_rect()
        if not window_rect:
            print("  Cannot find tab area: ToS window rect not found.")
            return None

        left, top, right, bottom = window_rect
        window_width = right - left
        window_height = bottom - top

        # Estimate: Tabs are usually near the top, below the main title bar and account bar.
        # These are rough estimates and might need adjustment based on actual ToS UI.
        # Let's assume main tabs are below the account dropdown area.
        # The account dropdown itself is usually very top-left.
        # Main tabs like "Monitor", "Trade" are often below that.

        # Example: If account bar is ~30-50px high, and dropdown trigger is within that.
        # Main tabs could start around y=60-80px from top of window.
        tab_area_y_offset_from_window_top = 60
        tab_area_height = 35  # Approximate height of a tab bar
        tab_area_x_offset_from_window_left = 10  # Start a bit from the left
        tab_area_width = window_width - 20  # Almost full width

        # Ensure calculated values are within window bounds
        rel_x = tab_area_x_offset_from_window_left
        rel_y = tab_area_y_offset_from_window_top
        rel_w = tab_area_width
        rel_h = tab_area_height

        # Validate against window dimensions (relative to window, so max is window_width/height)
        if rel_x + rel_w > window_width: rel_w = window_width - rel_x
        if rel_y + rel_h > window_height: rel_h = window_height - rel_y
        if rel_w <= 0 or rel_h <= 0:
            print("  Calculated tab area has invalid dimensions.")
            return None

        print(f"  Estimated tab area (relative to window): X={rel_x}, Y={rel_y}, W={rel_w}, H={rel_h}")
        return (rel_x, rel_y, rel_w, rel_h)

    def _capture_tab_area_image(self, tab_area_coords: Tuple[int, int, int, int]) -> Optional[str]:
        print(f"  Capturing tab area image from relative coords: {tab_area_coords}")
        window_rect = self.tos_navigator._get_window_rect()
        if not window_rect:
            print("  Cannot capture tab area: ToS window rect not found.")
            return None

        win_left, win_top = window_rect[0], window_rect[1]
        rel_x, rel_y, width, height = tab_area_coords

        abs_x = win_left + rel_x
        abs_y = win_top + rel_y

        save_dir = os.path.join(self.tos_navigator.captures_path, 'tab_detector_debug')
        os.makedirs(save_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        save_path = os.path.join(save_dir, f'tab_area_capture_{timestamp}.png')

        try:
            screenshot = pyautogui.screenshot(region=(abs_x, abs_y, width, height))
            screenshot.save(save_path)
            print(f"  Tab area image captured: {save_path}")
            return save_path
        except Exception as e:
            print(f"  Error capturing tab area image: {e}")
            return None

    def _analyze_tab_positions_from_image(self, tab_image_path: str,
                                          tab_area_rel_coords: Tuple[int, int, int, int]) -> List[dict]:
        print(f"  Analyzing tab positions from image: {tab_image_path}")
        try:
            tab_image_cv = cv2.imread(tab_image_path)
            if tab_image_cv is None:
                print(f"  Could not read tab image: {tab_image_path}")
                return []

            gray = cv2.cvtColor(tab_image_cv, cv2.COLOR_BGR2GRAY)
            # Simple thresholding, might need to be adaptive based on ToS theme
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Dilate to connect text parts of tab names
            kernel = np.ones((3, 15), np.uint8)  # Rectangular kernel, wider than tall
            dilated = cv2.dilate(thresh, kernel, iterations=1)

            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            tabs = []
            # tab_area_rel_coords are (x, y, w, h) of the tab bar relative to the ToS window
            base_x_in_window = tab_area_rel_coords[0]
            base_y_in_window = tab_area_rel_coords[1]

            for i, contour in enumerate(contours):
                x, y, w, h = cv2.boundingRect(contour)
                # Filter contours: reasonable width and height for a tab
                # Tab height should be close to the captured tab_area_height
                # Tab width should be significant
                if w > 30 and h > tab_area_rel_coords[3] * 0.5:  # Tab width > 30px, height > 50% of bar height

                    # Coordinates of the tab relative to the ToS window
                    tab_x_in_window = base_x_in_window + x
                    tab_y_in_window = base_y_in_window + y

                    center_x_in_window = tab_x_in_window + w // 2
                    center_y_in_window = tab_y_in_window + h // 2

                    # Try to OCR the tab name from the contour area
                    tab_name_roi = tab_image_cv[y:y + h, x:x + w]
                    tab_name_path_temp = os.path.join(self.tos_navigator.captures_path, 'tab_detector_debug',
                                                      f'temp_tab_roi_{i}.png')
                    cv2.imwrite(tab_name_path_temp, tab_name_roi)

                    tab_text = "UnknownTab"  # Default
                    try:
                        # A more specific OCR config might be needed if names are short/stylized
                        ocr_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789&'
                        tab_text_raw = pyautogui.pytesseract.image_to_string(tab_name_roi, config=ocr_config).strip()
                        if tab_text_raw:
                            tab_text = "".join(filter(str.isalnum, tab_text_raw))  # Clean it
                        if not tab_text: tab_text = f"Tab{i}"

                    except Exception as ocr_e:
                        print(f"    OCR error for tab {i}: {ocr_e}")
                        tab_text = f"TabOCRFailed{i}"

                    tab_info = {
                        'index': i,
                        'name': tab_text,  # Placeholder, can be filled by OCR later
                        'account_name': tab_text,  # Initially same as name
                        'relative_x': tab_x_in_window,  # Relative to ToS window
                        'relative_y': tab_y_in_window,  # Relative to ToS window
                        'width': w,
                        'height': h,
                        'center_x': center_x_in_window,  # Relative to ToS window
                        'center_y': center_y_in_window,  # Relative to ToS window
                    }
                    tabs.append(tab_info)

            # Sort tabs by their x-coordinate
            tabs.sort(key=lambda t: t['relative_x'])
            for idx, tab_info in enumerate(tabs):  # Re-index after sorting
                tab_info['index'] = idx

            # Save debug image
            debug_image = tab_image_cv.copy()
            for tab in tabs:
                # Draw rectangle based on its coordinates within the tab_image_cv
                # Need to subtract base_x_in_window and base_y_in_window from tab's relative_x/y
                # if drawing on tab_image_cv. But tab['relative_x'] is already relative to tab_image_cv's origin
                # No, wait. x,y,w,h from boundingRect are relative to tab_image_cv.
                # tab['relative_x'] is x + base_x_in_window.
                # So, to draw on tab_image_cv, we use the original x,y,w,h from contour.

                # Find the original contour's x,y for drawing:
                # This requires finding which tab corresponds to which contour, or re-iterating contours
                # For simplicity, let's assume sorting keeps them somewhat aligned or just draw based on stored w/h
                # This debug drawing part might be tricky if coords are mixed up.

                # Let's use the (x,y,w,h) directly from when the contour was processed if possible,
                # or recalculate for drawing on the local tab_image_cv

                # Simplified: For debug, just show rough areas
                # To draw on tab_image_cv, use x,y,w,h that were relative to tab_image_cv
                # The stored tab['relative_x'] etc. are for clicking relative to main window.
                # Let's re-iterate contours for drawing to be safe.
                pass  # Debug drawing can be complex; focus on click logic first.

            if tabs:
                print(f"  Analyzed {len(tabs)} potential tab structures.")
            else:
                print(f"  No clear tab structures found via contour analysis.")
            return tabs

        except Exception as e:
            print(f"  Error analyzing tab positions: {e}")
            import traceback
            print(traceback.format_exc())
            return []

    def switch_to_tab(self, tab_info: dict) -> bool:
        """
        Switch to a specific account tab.
        The tab_info dictionary should contain coordinates relative to the ToS window.
        """
        try:
            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect:
                print("Cannot switch tab: ToS window rect not found.")
                return False

            win_left, win_top = window_rect[0], window_rect[1]

            # tab_info['center_x'] and tab_info['center_y'] are already relative to ToS window's top-left
            # We need to add the window's screen position to get absolute screen coordinates.

            # Let's adjust the click point to be more robust:
            # Click slightly down from the top of the tab, and a bit in from the left.
            # This avoids clicking exactly on edges or decorative elements.
            # Tab height is tab_info['height'], width is tab_info['width']
            # Click Y: a third of the way down the tab's height.
            # Click X: a quarter of the way into the tab's width.

            click_offset_x = tab_info['width'] // 4  # Click 25% into the tab from its left edge
            click_offset_y = tab_info['height'] // 3  # Click 33% into the tab from its top edge

            # These are relative to the ToS window's 0,0
            click_x_relative_to_window = tab_info['relative_x'] + click_offset_x
            click_y_relative_to_window = tab_info['relative_y'] + click_offset_y

            # Convert to absolute screen coordinates for pyautogui
            abs_click_x = win_left + click_x_relative_to_window
            abs_click_y = win_top + click_y_relative_to_window

            tab_name = tab_info.get('name', f"Index {tab_info.get('index', 'N/A')}")
            print(f"Attempting to switch to tab '{tab_name}'.")
            print(
                f"  Tab Rel Coords (X,Y,W,H): ({tab_info['relative_x']}, {tab_info['relative_y']}, {tab_info['width']}, {tab_info['height']})")
            print(f"  Calculated Rel Click (in window): ({click_x_relative_to_window}, {click_y_relative_to_window})")
            print(f"  Absolute Screen Click: ({abs_click_x}, {abs_click_y})")

            pyautogui.click(abs_click_x, abs_click_y)
            time.sleep(1.2)  # Slightly longer pause for tab content to load

            self.current_tab_index = tab_info.get('index', -1)  # Update current tab
            print(f"  Successfully clicked for tab '{tab_name}'. Current index: {self.current_tab_index}")
            return True

        except KeyError as ke:
            print(f"Error switching to tab: Missing key in tab_info - {ke}. Tab Info: {tab_info}")
            return False
        except Exception as e:
            print(f"Error switching to tab: {e}")
            import traceback
            print(traceback.format_exc())
            return False

    def get_current_tab_index(self) -> int:
        return self.current_tab_index

    def update_tab_names(self, detected_tabs: List[dict], account_names_from_dropdown: List[str]):
        """
        Update tab information with actual account names if this TabDetector is used for
        account tabs that are also discoverable via dropdown (less common for Pradeep's case).
        More likely, this would be used to name main ToS tabs (Monitor, Trade, etc.) via OCR.
        """
        print("Updating tab names (if applicable)...")
        # This function's utility depends on what these 'tabs' represent.
        # If they are main ToS sections, account_names_from_dropdown is irrelevant.
        # If they somehow correspond to accounts, then this logic applies.

        for i, tab_info in enumerate(detected_tabs):
            # If account_names_from_dropdown is provided and relevant:
            if account_names_from_dropdown and i < len(account_names_from_dropdown):
                tab_info['name'] = account_names_from_dropdown[i]
                tab_info['account_name'] = account_names_from_dropdown[i]  # If it's an account tab
                print(f"  Tab {i} updated with dropdown name: {tab_info['name']}")
            else:
                # If no dropdown names, or more tabs than names, rely on OCR'd name or default.
                # The name should have been set during _analyze_tab_positions_from_image.
                print(f"  Tab {i} using existing/default name: {tab_info.get('name', 'N/A')}")


# Example usage (for testing this module directly):
if __name__ == "__main__":
    print("TabDetector Standalone Test")


    # This requires a running ToS window and a TosNavigator instance.
    # For a real test, you'd integrate this with the main app's window finding.

    # Mocking TosNavigator for simple execution, real test needs actual HWND
    class MockTosNavigator:
        def __init__(self):
            self.assets_path = "assets"  # Adjust if needed
            self.captures_path = os.path.join(self.assets_path, "captures")
            os.makedirs(self.captures_path, exist_ok=True)
            self.hwnd = None  # Needs a real HWND for get_window_rect

        def _get_window_rect(self):
            # In a real test, this would come from win32gui.GetWindowRect(self.hwnd)
            # For mock, let's assume a window size if you can't get a real one.
            # Try to get a real window for testing if possible.
            try:
                # Attempt to find any visible window to test coordinate logic
                # This is NOT a ToS window, just for testing the screenshot part.
                test_hwnd = pyautogui.getWindowsWithTitle("")[0]._hWnd  # Get first available window
                if test_hwnd:
                    print(f"Mock using rect of window: {pyautogui.getWindowsWithTitle('')[0].title}")
                    return win32gui.GetWindowRect(test_hwnd)
            except:
                print(
                    "Mock _get_window_rect: Returning dummy rect 1000x800 at 0,0. For real test, ensure ToS is running.")
                return (0, 0, 1000, 800)  # Dummy rect: left, top, right, bottom


    # --- How to run a more meaningful test ---
    # 1. Ensure ToS is running.
    # 2. Manually find its HWND (e.g., using a tool like Spy++ or another script).
    # 3. Set mock_navigator.hwnd = YOUR_TOS_HWND

    mock_navigator = MockTosNavigator()

    # --- Find a real ToS window for testing ---
    try:
        tos_windows = pyautogui.getWindowsWithTitle("thinkorswim")
        if tos_windows:
            # Find the main one, often "Main@thinkorswim [build ...]"
            main_tos_window = None
            for w in tos_windows:
                if "main@thinkorswim" in w.title.lower():
                    main_tos_window = w
                    break
            if main_tos_window:
                mock_navigator.hwnd = main_tos_window._hWnd
                print(f"Using ToS window for test: '{main_tos_window.title}' HWND: {mock_navigator.hwnd}")
            else:
                print("Could not find 'Main@thinkorswim' window. Test might be less accurate.")
                if tos_windows:  # Fallback to any "thinkorswim" window
                    mock_navigator.hwnd = tos_windows[0]._hWnd
                    print(f"Fallback: Using generic ToS window: '{tos_windows[0].title}' HWND: {mock_navigator.hwnd}")

        else:
            print("No 'thinkorswim' window found. TabDetector test will be limited.")
    except Exception as e_find:
        print(f"Error trying to find ToS window for test: {e_find}")

    if not mock_navigator.hwnd:
        print("Cannot proceed with test without a window HWND for mock_navigator.")
    else:
        tab_detector = TabDetector(mock_navigator)
        detected_tabs_list = tab_detector.detect_account_tabs()

        if detected_tabs_list:
            print("\n[Test] Detected tabs summary:")
            for t_info in detected_tabs_list:
                print(
                    f"  - Name: {t_info['name']}, Rel Center: ({t_info['center_x']}, {t_info['center_y']}), Size: {t_info['width']}x{t_info['height']}")

            # Example of trying to switch to the first detected tab
            # Be careful: this will actually click on your screen if a ToS window is active!
            # choice = input("Attempt to click the first detected tab? (y/n): ").lower()
            # if choice == 'y':
            #     print(f"\n[Test] Attempting to switch to tab: {detected_tabs_list[0]['name']}")
            #     success = tab_detector.switch_to_tab(detected_tabs_list[0])
            #     print(f"[Test] Switch attempt result: {'Success' if success else 'Failed'}")
        else:
            print("\n[Test] No tabs were detected by the TabDetector.")