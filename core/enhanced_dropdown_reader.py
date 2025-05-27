# Delta_Mon/core/enhanced_dropdown_reader.py

import cv2
import numpy as np
import pyautogui
import os
import time
from typing import List, Optional, Tuple, Dict
from core.tos_navigator import TosNavigator
from utils.ocr_utils import OCRUtils
from core.window_manager import WindowManager  # Keep this for the standalone test case


class EnhancedDropdownReader:
    def __init__(self, tos_navigator: TosNavigator):
        """
        Enhanced dropdown reader optimized for reading 25+ account names.

        Args:
            tos_navigator: TosNavigator instance for window operations
        """
        self.tos_navigator = tos_navigator  # Use the provided navigator
        self.ocr_utils = OCRUtils()

        # Dropdown detection settings optimized for large lists
        self.dropdown_settings = {
            'trigger_search_area': {
                'x_ratio': 0.02,  # Search top-left area for dropdown trigger
                'y_ratio': 0.05,
                'width_ratio': 0.4,
                'height_ratio': 0.15,
            },
            'list_capture_area': {
                'width': 350,  # Wider to catch longer account names
                'height': 500,  # Taller for 25+ accounts
                'offset_x': -10,  # Slight left offset
                'offset_y': 5,  # Below the trigger
            }
        }

    def read_all_accounts_from_dropdown(self, save_debug: bool = True) -> List[str]:
        """
        Read all account names from the dropdown list.

        Args:
            save_debug: Whether to save debug images

        Returns:
            List of account names found in dropdown
        """
        print("🔍 Reading all accounts from dropdown...")

        # Step 1: Find and click the dropdown trigger
        if not self._click_dropdown_trigger():
            print("❌ Failed to find/click dropdown trigger")
            return []

        # Step 2: Wait for dropdown to fully expand (important for 25 accounts!)
        print("⏳ Waiting for dropdown to fully expand...")
        time.sleep(2.0)  # Longer wait for large dropdown

        # Step 3: Capture the dropdown list area
        dropdown_image_path = self._capture_dropdown_list()
        if not dropdown_image_path:
            print("❌ Failed to capture dropdown list")
            return []

        # Step 4: Extract all account names using enhanced OCR
        account_names = self._extract_all_account_names(dropdown_image_path, save_debug)

        # Step 5: Click somewhere else to close dropdown
        self._close_dropdown()

        print(f"✅ Successfully extracted {len(account_names)} accounts from dropdown")
        return account_names

    def _click_dropdown_trigger(self) -> bool:
        """Find and click the dropdown trigger button."""
        print("🎯 Searching for dropdown trigger...")

        # Use enhanced search in upper left area
        found_coords = self.tos_navigator.find_element_in_upper_left(
            "account_dropdown_template.png",
            confidence=0.6,  # Lower confidence for better detection
            region_width_ratio=self.dropdown_settings['trigger_search_area']['width_ratio'],
            region_height_ratio=self.dropdown_settings['trigger_search_area']['height_ratio']
        )

        if found_coords:
            match_x_relative, match_y_relative, template_w, template_h = found_coords
            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect:
                return False
            win_left, win_top = window_rect[0], window_rect[1]
            click_x_absolute = win_left + match_x_relative + template_w // 2
            click_y_absolute = win_top + match_y_relative + template_h // 2
            print(f"🖱️ Clicking dropdown at: ({click_x_absolute}, {click_y_absolute})")
            pyautogui.click(click_x_absolute, click_y_absolute)
            return True
        else:
            print("❌ Could not find dropdown trigger ('account_dropdown_template.png'). Run 'Setup Template'.")
            return False

    def _capture_dropdown_list(self) -> Optional[str]:
        """Capture the expanded dropdown list area."""
        try:
            trigger_coords = self.tos_navigator.find_element_in_upper_left(
                "account_dropdown_template.png",
                confidence=0.5  # Be a bit lenient finding it again
            )

            if not trigger_coords:
                print("⚠️ Could not relocate dropdown trigger for list capture. Using fallback capture.")
                return self._capture_dropdown_fallback()

            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect: return None
            win_left, win_top = window_rect[0], window_rect[1]
            trigger_x, trigger_y, trigger_w, trigger_h = trigger_coords

            list_x = win_left + trigger_x + self.dropdown_settings['list_capture_area']['offset_x']
            list_y = win_top + trigger_y + trigger_h + self.dropdown_settings['list_capture_area']['offset_y']
            list_width = self.dropdown_settings['list_capture_area']['width']
            list_height = self.dropdown_settings['list_capture_area']['height']

            screen_width, screen_height = pyautogui.size()
            list_x = max(0, list_x)  # Ensure not off-screen left
            list_y = max(0, list_y)  # Ensure not off-screen top
            list_width = min(list_width, screen_width - list_x)
            list_height = min(list_height, screen_height - list_y)

            if list_width <= 0 or list_height <= 0:
                print(f"❌ Invalid dropdown capture dimensions: W={list_width}, H={list_height}")
                return self._capture_dropdown_fallback()

            save_dir = os.path.join(self.tos_navigator.captures_path,
                                    'dropdown_captures')  # Use navigator's captures_path
            os.makedirs(save_dir, exist_ok=True)
            # More descriptive filename
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            save_path = os.path.join(save_dir, f'dropdown_list_capture_{timestamp}.png')

            print(f"📸 Capturing dropdown list: {list_width}x{list_height} at ({list_x}, {list_y})")
            screenshot = pyautogui.screenshot(region=(list_x, list_y, list_width, list_height))
            screenshot.save(save_path)
            print(f"💾 Dropdown list saved: {save_path}")
            return save_path
        except Exception as e:
            print(f"❌ Error capturing dropdown list: {e}")
            return self._capture_dropdown_fallback()  # Try fallback on any error

    def _capture_dropdown_fallback(self) -> Optional[str]:
        """Fallback capture method when trigger can't be relocated."""
        print(" jatuh kembali menangkap dropdown...")
        try:
            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect: return None
            left, top, right, bottom = window_rect

            # Capture upper-left area where dropdown likely appeared
            # Based on the provided screenshot, the dropdown is in the very upper left.
            capture_x = left + 10  # Small offset from window edge
            capture_y = top + 70  # Below typical title bar / account bar area
            capture_width = 350  # Consistent with desired dropdown width
            capture_height = 500  # Consistent with desired dropdown height

            screen_width, screen_height = pyautogui.size()
            capture_x = max(0, capture_x)
            capture_y = max(0, capture_y)
            capture_width = min(capture_width, screen_width - capture_x)
            capture_height = min(capture_height, screen_height - capture_y)

            if capture_width <= 0 or capture_height <= 0:
                print(f"❌ Invalid fallback capture dimensions: W={capture_width}, H={capture_height}")
                return None

            save_dir = os.path.join(self.tos_navigator.captures_path, 'dropdown_captures')
            os.makedirs(save_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            save_path = os.path.join(save_dir, f'dropdown_list_fallback_{timestamp}.png')

            print(f"📸 Fallback capture: {capture_width}x{capture_height} at ({capture_x}, {capture_y})")
            screenshot = pyautogui.screenshot(region=(capture_x, capture_y, capture_width, capture_height))
            screenshot.save(save_path)
            return save_path
        except Exception as e:
            print(f"❌ Fallback capture error: {e}")
            return None

    def _extract_all_account_names(self, dropdown_image_path: str, save_debug: bool = True) -> List[str]:
        """Extract all account names from the dropdown image using enhanced OCR."""
        print("🔬 Extracting account names using enhanced OCR...")
        try:
            dropdown_image = cv2.imread(dropdown_image_path)
            if dropdown_image is None:
                print(f"❌ Could not load dropdown image: {dropdown_image_path}")
                return []
            print(f"📊 Dropdown image size: {dropdown_image.shape[1]}x{dropdown_image.shape[0]}")

            accounts_method1 = self._extract_accounts_direct_ocr(dropdown_image, dropdown_image_path, save_debug)
            accounts_method2 = self._extract_accounts_line_by_line(dropdown_image, dropdown_image_path, save_debug)
            accounts_method3 = self._extract_accounts_enhanced_preprocessing(dropdown_image, dropdown_image_path,
                                                                             save_debug)

            all_accounts = accounts_method1 + accounts_method2 + accounts_method3
            unique_accounts = self._deduplicate_and_clean_accounts(all_accounts)

            print(f"📈 OCR Results Summary:")
            print(f"   Method 1 (Direct): {len(accounts_method1)} accounts")
            print(f"   Method 2 (Line-by-line): {len(accounts_method2)} accounts")
            print(f"   Method 3 (Enhanced): {len(accounts_method3)} accounts")
            print(f"   Final unique accounts: {len(unique_accounts)}")
            return unique_accounts
        except Exception as e:
            print(f"❌ Error extracting account names: {e}")
            return []

    def _extract_accounts_direct_ocr(self, dropdown_image: np.ndarray, image_path: str, save_debug: bool) -> List[str]:
        try:
            print("🔍 Method 1: Direct OCR...")
            # Create a temporary path for OCRUtils to process, as it expects a path
            base_name = os.path.basename(image_path)
            temp_ocr_image_path = os.path.join(os.path.dirname(image_path), f"temp_direct_{base_name}")
            cv2.imwrite(temp_ocr_image_path, dropdown_image)

            accounts = self.ocr_utils.extract_account_names(temp_ocr_image_path, debug_save=save_debug)

            try:
                os.remove(temp_ocr_image_path)
            except:
                pass

            print(f"   Found {len(accounts)} accounts via direct OCR")
            return accounts
        except Exception as e:
            print(f"   ❌ Direct OCR error: {e}")
            return []

    def _extract_accounts_line_by_line(self, dropdown_image: np.ndarray, image_path: str, save_debug: bool) -> List[
        str]:
        try:
            print("🔍 Method 2: Line-by-line analysis...")
            gray = cv2.cvtColor(dropdown_image, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape

            # Improved line detection - adaptive thresholding and morphological ops
            # This helps in varying background/text colors in dropdowns
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

            # Detect horizontal lines to segment rows
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT,
                                                          (width // 2, 1))  # Kernel to detect long horizontal lines
            detected_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)

            contours, _ = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Get y-coordinates of rows based on detected lines or row-like structures
            # This part needs to be robust. For now, a simplified approach if lines are not clear:
            # Estimate row height if contours are not reliable.
            # For Pradeep's case, items are well separated. Let's try a simpler projection.

            # Horizontal projection sum
            h_projection = np.sum(gray, axis=1)  # Sum pixels across rows

            # Find gaps (low sum) between text lines (high sum)
            # This is a simplified segmentation; more advanced methods exist
            from scipy.signal import find_peaks
            # Invert projection to find valleys (gaps) as peaks
            inverted_projection = np.max(h_projection) - h_projection
            peaks, _ = find_peaks(inverted_projection, height=np.mean(inverted_projection),
                                  distance=10)  # distance is min px between rows

            accounts = []
            start_y = 0
            debug_dir = os.path.join(os.path.dirname(image_path), 'line_analysis_debug')
            if save_debug: os.makedirs(debug_dir, exist_ok=True)

            row_regions_y = []
            if len(peaks) > 0:
                row_regions_y.append(0)  # Start of first item
                for p in peaks:
                    row_regions_y.append(p)
                row_regions_y.append(height)  # End of last item
            else:  # Fallback if no clear peaks - treat whole image as one block
                row_regions_y = [0, height]

            for i in range(len(row_regions_y) - 1):
                y1, y2 = row_regions_y[i], row_regions_y[i + 1]
                if y2 - y1 < 8: continue  # Skip very small regions

                region_image = dropdown_image[y1:y2, :]

                temp_region_path = os.path.join(debug_dir, f"region_{i:02d}.png")
                if save_debug:
                    cv2.imwrite(temp_region_path, region_image)
                else:  # Need to save temporarily anyway for OCR if not debugging
                    temp_dir_for_ocr = os.path.join(self.tos_navigator.captures_path, "temp_ocr")
                    os.makedirs(temp_dir_for_ocr, exist_ok=True)
                    temp_region_path = os.path.join(temp_dir_for_ocr, f"temp_ocr_region_{i}.png")
                    cv2.imwrite(temp_region_path, region_image)

                region_accounts = self.ocr_utils.extract_account_names(temp_region_path,
                                                                       debug_save=False)  # Debug already saved if needed
                accounts.extend(region_accounts)

                if not save_debug and os.path.exists(temp_region_path) and "temp_ocr_region" in temp_region_path:
                    try:
                        os.remove(temp_region_path)
                    except:
                        pass

            print(f"   Found {len(accounts)} potential accounts via line-by-line analysis")
            return accounts
        except Exception as e:
            print(f"   ❌ Line-by-line analysis error: {e}")
            import traceback
            print(traceback.format_exc())
            return []

    def _extract_accounts_enhanced_preprocessing(self, dropdown_image: np.ndarray, image_path: str, save_debug: bool) -> \
    List[str]:
        try:
            print("🔍 Method 3: Enhanced preprocessing...")
            gray = cv2.cvtColor(dropdown_image, cv2.COLOR_BGR2GRAY)

            # Adaptive thresholding is often good for text
            # Using THRESH_BINARY_INV because OCR often prefers white text on black, or Tesseract handles it.
            # Let's try simple OTSU first, then adaptive.
            _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # If background is dark, text is light. OCR might prefer black text on white.
            # If mean is high (mostly white), invert it.
            if np.mean(th) > 128:
                th = cv2.bitwise_not(th)  # Invert to black text on white

            # Dilation and erosion to remove noise
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel)  # Open to remove small noise
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)  # Close to fill gaps in text

            temp_enhanced_path = ""
            if save_debug:
                debug_path = image_path.replace('.png', '_enhanced_method3.png')
                cv2.imwrite(debug_path, cleaned)
                print(f"   Enhanced image (Method 3) saved: {debug_path}")
                temp_enhanced_path = debug_path
            else:
                temp_dir_for_ocr = os.path.join(self.tos_navigator.captures_path, "temp_ocr")
                os.makedirs(temp_dir_for_ocr, exist_ok=True)
                temp_enhanced_path = os.path.join(temp_dir_for_ocr, f"temp_ocr_enhanced_{os.path.basename(image_path)}")
                cv2.imwrite(temp_enhanced_path, cleaned)

            accounts = self.ocr_utils.extract_account_names(temp_enhanced_path, debug_save=False)

            if not save_debug and os.path.exists(temp_enhanced_path) and "temp_ocr_enhanced" in temp_enhanced_path:
                try:
                    os.remove(temp_enhanced_path)
                except:
                    pass

            print(f"   Found {len(accounts)} accounts via enhanced preprocessing")
            return accounts
        except Exception as e:
            print(f"   ❌ Enhanced preprocessing error: {e}")
            return []

    def _deduplicate_and_clean_accounts(self, all_accounts: List[str]) -> List[str]:
        print("🧹 Deduplicating and cleaning account names...")
        seen = set()
        unique_accounts = []
        for account in all_accounts:
            if not account or len(account.strip()) < 2: continue
            cleaned = self._clean_account_name(account)
            if cleaned and cleaned not in seen:
                # Further check for very similar names (e.g. OCR artifacts like trailing chars)
                is_too_similar = False
                for existing_acc in seen:
                    # Using a simple similarity check (e.g. if one is a substring of other and close in length)
                    if (cleaned in existing_acc or existing_acc in cleaned) and \
                            abs(len(cleaned) - len(existing_acc)) < 3:
                        # Prefer the shorter one if one is substring of other, or the one already seen.
                        # This is a basic heuristic. More advanced: Levenshtein distance.
                        if len(cleaned) >= len(existing_acc):  # Current is longer or same, prefer existing
                            is_too_similar = True
                            break
                        else:  # Current is shorter, replace existing if it's very similar
                            seen.remove(existing_acc)
                            # find and remove from unique_accounts list
                            try:
                                unique_accounts.remove(existing_acc)
                            except ValueError:
                                pass  # Should not happen if logic is correct
                            break  # Add the new shorter one

                if not is_too_similar:
                    seen.add(cleaned)
                    unique_accounts.append(cleaned)
        unique_accounts.sort()
        print(f"   Cleaned and deduplicated: {len(unique_accounts)} unique accounts")
        return unique_accounts

    def _clean_account_name(self, raw_name: str) -> Optional[str]:
        import re
        cleaned = raw_name.strip()
        # Remove common OCR artifacts like leading/trailing junk, vertical bars, etc.
        cleaned = re.sub(r'^[^a-zA-Z0-9\(@-]+', '', cleaned)  # Remove leading non-alphanumeric (keep @, (), -)
        cleaned = re.sub(r'[^a-zA-Z0-9\s_@().-]+$', '', cleaned)  # Remove trailing
        cleaned = re.sub(r'[|/\\]+', '', cleaned)  # Remove | / \
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)  # Multiple spaces to one

        # More aggressive cleaning of non-alphanumeric chars if they are not typical for account names
        # This needs to be balanced. For now, let's be somewhat conservative.
        # cleaned = re.sub(r'[^\w\s@().-]', '', cleaned) # \w includes underscore

        if len(cleaned) < 3 or len(cleaned) > 50: return None  # Typical length constraints
        if not re.search(r'[a-zA-Z0-9]', cleaned): return None  # Must contain some alpha-numeric

        # Specific ToS pattern cleaning (e.g., "(Individual)" might be noisy)
        # This is optional and depends on how clean you want the names
        # cleaned = re.sub(r'\s*\(Individual\)\s*$', '', cleaned, flags=re.IGNORECASE).strip()
        # cleaned = re.sub(r'\s*\(IRA\)\s*$', '', cleaned, flags=re.IGNORECASE).strip()

        return cleaned

    def _close_dropdown(self):
        """Close the dropdown by clicking elsewhere."""
        try:
            self.tos_navigator.click_somewhere_else_to_close_dropdown()
            print("🖱️ Clicked to close dropdown")
        except Exception as e:
            print(f"⚠️ Could not close dropdown: {e}")


class DropdownAccountDiscovery:
    def __init__(self, tos_navigator: Optional[TosNavigator] = None):  # Accept optional TosNavigator
        """Initialize dropdown-based account discovery."""
        if tos_navigator:
            self.tos_navigator = tos_navigator
        else:
            # This block is for standalone testing or if a navigator isn't provided externally
            print("ℹ️ DropdownAccountDiscovery creating its own WindowManager and TosNavigator.")
            self.window_manager = WindowManager(
                target_exact_title="Main@thinkorswim [build 1985]",
                exclude_title_substring="DeltaMon"
            )
            tos_hwnd = self.window_manager.find_tos_window()
            if not tos_hwnd:
                raise RuntimeError(
                    "ToS window not found. Cannot initialize DropdownAccountDiscovery without a valid ToS window.")
            if not self.window_manager.focus_tos_window():
                print("⚠️ Warning: Could not focus ToS window during DropdownAccountDiscovery init.")
            self.tos_navigator = TosNavigator(tos_hwnd)

        self.dropdown_reader = EnhancedDropdownReader(self.tos_navigator)
        self.discovered_accounts = []

    def discover_all_accounts(self, status_callback=None) -> List[str]:
        """
        Discover all accounts from the dropdown.
        Args:
            status_callback: Optional callback for status updates
        Returns:
            List of discovered account names
        """

        def update_status(message: str):
            print(message)
            if status_callback:
                status_callback(message)

        try:
            update_status("🔍 Starting dropdown account discovery...")

            # Ensure ToS window is focused (if navigator was provided, this should be handled by caller)
            # If navigator was created internally, focus was attempted in __init__
            if not self.tos_navigator.hwnd:  # Should not happen if init was successful
                update_status("❌ ToS Navigator has no valid HWND.")
                return []

            # Check if main trading window is available - this is a good sanity check
            if not self.tos_navigator._get_window_rect():  # A simple check if window is valid
                update_status("❌ ToS window seems to be unavailable or minimized.")
                return []

            update_status("📖 Reading accounts from dropdown using EnhancedDropdownReader...")
            self.discovered_accounts = self.dropdown_reader.read_all_accounts_from_dropdown(save_debug=True)

            if self.discovered_accounts:
                update_status(f"✅ Successfully discovered {len(self.discovered_accounts)} accounts!")
                for i, account in enumerate(self.discovered_accounts, 1):
                    update_status(f"   {i:2d}. {account}")
            else:
                update_status("❌ No accounts found in dropdown by EnhancedDropdownReader.")
            return self.discovered_accounts
        except Exception as e:
            update_status(f"❌ Discovery error: {e}")
            import traceback
            update_status(traceback.format_exc())
            return []

    def get_discovered_accounts(self) -> List[str]:
        """Get the list of discovered account names."""
        return self.discovered_accounts.copy()


# Test function
if __name__ == "__main__":
    print("Enhanced Dropdown Reader - Standalone Test")
    print("=" * 40)
    print("ENSURE TOS IS RUNNING AND THE MAIN WINDOW IS ACTIVE BEFORE STARTING.")
    input("Press Enter to begin test...")

    try:
        discovery = DropdownAccountDiscovery()  # Will create its own navigator for this test
        accounts = discovery.discover_all_accounts()

        if accounts:
            print(f"\n✅ SUCCESS! Found {len(accounts)} accounts:")
            for i, account in enumerate(accounts, 1):
                print(f"   {i:2d}. {account}")
        else:
            print("\n❌ No accounts found or an error occurred.")
    except Exception as e:
        print(f"❌ CRITICAL ERROR during test: {e}")
        import traceback

        print(traceback.format_exc())