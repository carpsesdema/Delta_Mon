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
    def __init__(self, tos_navigator: TosNavigator):
        """
        Enhanced dropdown reader optimized for reading 25+ account names.

        Args:
            tos_navigator: TosNavigator instance for window operations
        """
        self.tos_navigator = tos_navigator
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
            # Click the dropdown
            match_x_relative, match_y_relative, template_w, template_h = found_coords

            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect:
                return False

            win_left, win_top = window_rect[0], window_rect[1]

            # Click center of found template
            click_x_absolute = win_left + match_x_relative + template_w // 2
            click_y_absolute = win_top + match_y_relative + template_h // 2

            print(f"🖱️ Clicking dropdown at: ({click_x_absolute}, {click_y_absolute})")
            pyautogui.click(click_x_absolute, click_y_absolute)
            return True
        else:
            print("❌ Could not find dropdown trigger")
            return False

    def _capture_dropdown_list(self) -> Optional[str]:
        """Capture the expanded dropdown list area."""
        try:
            # Find the dropdown trigger again to get position for relative capture
            trigger_coords = self.tos_navigator.find_element_in_upper_left(
                "account_dropdown_template.png",
                confidence=0.5
            )

            if not trigger_coords:
                print("⚠️ Could not relocate dropdown trigger for list capture")
                # Fallback: capture a larger area where dropdown likely is
                return self._capture_dropdown_fallback()

            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect:
                return None

            win_left, win_top = window_rect[0], window_rect[1]
            trigger_x, trigger_y, trigger_w, trigger_h = trigger_coords

            # Calculate dropdown list position (usually appears below trigger)
            list_x = win_left + trigger_x + self.dropdown_settings['list_capture_area']['offset_x']
            list_y = win_top + trigger_y + trigger_h + self.dropdown_settings['list_capture_area']['offset_y']
            list_width = self.dropdown_settings['list_capture_area']['width']
            list_height = self.dropdown_settings['list_capture_area']['height']

            # Ensure we don't go off screen
            screen_width, screen_height = pyautogui.size()
            list_width = min(list_width, screen_width - list_x)
            list_height = min(list_height, screen_height - list_y)

            # Create save directory
            save_dir = os.path.join(self.tos_navigator.assets_path, 'captures', 'dropdown')
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, 'dropdown_list_25accounts.png')

            print(f"📸 Capturing dropdown list: {list_width}x{list_height} at ({list_x}, {list_y})")
            screenshot = pyautogui.screenshot(region=(list_x, list_y, list_width, list_height))
            screenshot.save(save_path)

            print(f"💾 Dropdown list saved: {save_path}")
            return save_path

        except Exception as e:
            print(f"❌ Error capturing dropdown list: {e}")
            return None

    def _capture_dropdown_fallback(self) -> Optional[str]:
        """Fallback capture method when trigger can't be relocated."""
        try:
            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect:
                return None

            left, top, right, bottom = window_rect

            # Capture upper-left area where dropdown likely appeared
            capture_width = 400
            capture_height = 600
            capture_x = left + 50  # Offset from window edge
            capture_y = top + 80  # Below title bar

            save_dir = os.path.join(self.tos_navigator.assets_path, 'captures', 'dropdown')
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, 'dropdown_list_fallback.png')

            print(f"📸 Fallback capture: {capture_width}x{capture_height}")
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
            # Load the dropdown image
            dropdown_image = cv2.imread(dropdown_image_path)
            if dropdown_image is None:
                print(f"❌ Could not load dropdown image: {dropdown_image_path}")
                return []

            print(f"📊 Dropdown image size: {dropdown_image.shape[1]}x{dropdown_image.shape[0]}")

            # Method 1: Direct OCR on full image
            accounts_method1 = self._extract_accounts_direct_ocr(dropdown_image, dropdown_image_path, save_debug)

            # Method 2: Line-by-line analysis
            accounts_method2 = self._extract_accounts_line_by_line(dropdown_image, dropdown_image_path, save_debug)

            # Method 3: Enhanced preprocessing + OCR
            accounts_method3 = self._extract_accounts_enhanced_preprocessing(dropdown_image, dropdown_image_path,
                                                                             save_debug)

            # Combine and deduplicate results
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

    def _extract_accounts_direct_ocr(self, dropdown_image: np.ndarray,
                                     image_path: str, save_debug: bool) -> List[str]:
        """Method 1: Direct OCR on the full dropdown image."""
        try:
            print("🔍 Method 1: Direct OCR...")

            # Use the existing OCR utility
            accounts = self.ocr_utils.extract_account_names(image_path, debug_save=save_debug)

            print(f"   Found {len(accounts)} accounts via direct OCR")
            return accounts

        except Exception as e:
            print(f"   ❌ Direct OCR error: {e}")
            return []

    def _extract_accounts_line_by_line(self, dropdown_image: np.ndarray,
                                       image_path: str, save_debug: bool) -> List[str]:
        """Method 2: Analyze dropdown line by line to extract individual accounts."""
        try:
            print("🔍 Method 2: Line-by-line analysis...")

            # Convert to grayscale
            gray = cv2.cvtColor(dropdown_image, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape

            # Find horizontal lines/separators that might divide accounts
            horizontal_projection = np.sum(gray, axis=1)  # Sum across each row

            # Smooth the projection to reduce noise
            from scipy import ndimage
            smoothed = ndimage.gaussian_filter1d(horizontal_projection, sigma=1)

            # Find potential line separators (darker horizontal lines)
            line_threshold = np.mean(smoothed) * 0.9
            potential_lines = []

            for i in range(1, len(smoothed) - 1):
                if smoothed[i] < line_threshold:
                    potential_lines.append(i)

            # Group consecutive line pixels into single separators
            separators = []
            if potential_lines:
                current_group = [potential_lines[0]]
                for line in potential_lines[1:]:
                    if line - current_group[-1] <= 3:  # Close together
                        current_group.append(line)
                    else:
                        separators.append(int(np.mean(current_group)))
                        current_group = [line]
                separators.append(int(np.mean(current_group)))

            # Extract text from regions between separators
            accounts = []
            if separators:
                regions = []
                prev_y = 0
                for sep_y in separators:
                    if sep_y - prev_y > 15:  # Minimum height for text
                        regions.append((prev_y, sep_y))
                    prev_y = sep_y + 1

                # Add final region
                if height - prev_y > 15:
                    regions.append((prev_y, height))

                # Extract text from each region
                for i, (start_y, end_y) in enumerate(regions):
                    region = gray[start_y:end_y, :]

                    if save_debug:
                        debug_dir = os.path.join(os.path.dirname(image_path), 'line_analysis')
                        os.makedirs(debug_dir, exist_ok=True)
                        region_path = os.path.join(debug_dir, f'region_{i:02d}.png')
                        cv2.imwrite(region_path, region)

                    # OCR on this region
                    temp_path = os.path.join(os.path.dirname(image_path), f'temp_region_{i}.png')
                    cv2.imwrite(temp_path, region)

                    region_accounts = self.ocr_utils.extract_account_names(temp_path, debug_save=False)
                    accounts.extend(region_accounts)

                    # Clean up temp file
                    try:
                        os.remove(temp_path)
                    except:
                        pass

            print(f"   Found {len(accounts)} accounts via line-by-line analysis")
            return accounts

        except Exception as e:
            print(f"   ❌ Line-by-line analysis error: {e}")
            return []

    def _extract_accounts_enhanced_preprocessing(self, dropdown_image: np.ndarray,
                                                 image_path: str, save_debug: bool) -> List[str]:
        """Method 3: Enhanced preprocessing for better OCR results."""
        try:
            print("🔍 Method 3: Enhanced preprocessing...")

            # Convert to grayscale
            gray = cv2.cvtColor(dropdown_image, cv2.COLOR_BGR2GRAY)

            # Resize for better OCR (OCR works better on larger text)
            scale_factor = 2.0
            new_width = int(gray.shape[1] * scale_factor)
            new_height = int(gray.shape[0] * scale_factor)
            resized = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

            # Enhanced contrast
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(resized)

            # Gaussian blur to smooth text
            blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)

            # Adaptive threshold for varying lighting
            adaptive_thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Morphological operations to clean text
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)

            # Save enhanced image
            if save_debug:
                debug_path = image_path.replace('.png', '_enhanced.png')
                cv2.imwrite(debug_path, cleaned)
                print(f"   Enhanced image saved: {debug_path}")

            # OCR on enhanced image
            temp_enhanced_path = image_path.replace('.png', '_temp_enhanced.png')
            cv2.imwrite(temp_enhanced_path, cleaned)

            accounts = self.ocr_utils.extract_account_names(temp_enhanced_path, debug_save=False)

            # Clean up
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
        """Remove duplicates and clean up account names."""
        print("🧹 Deduplicating and cleaning account names...")

        seen = set()
        unique_accounts = []

        for account in all_accounts:
            if not account or len(account.strip()) < 2:
                continue

            # Clean the account name
            cleaned = self._clean_account_name(account)

            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                unique_accounts.append(cleaned)

        # Sort for consistent ordering
        unique_accounts.sort()

        print(f"   Cleaned and deduplicated: {len(unique_accounts)} unique accounts")
        return unique_accounts

    def _clean_account_name(self, raw_name: str) -> Optional[str]:
        """Clean and validate an account name."""
        import re

        # Basic cleaning
        cleaned = raw_name.strip()

        # Remove common OCR artifacts
        cleaned = re.sub(r'[|\\\/]+', '', cleaned)
        cleaned = re.sub(r'[^\w@.-]', '', cleaned)  # Keep only safe characters
        cleaned = re.sub(r'^[^a-zA-Z0-9]+', '', cleaned)  # Remove leading junk

        # Validate length
        if len(cleaned) < 2 or len(cleaned) > 50:
            return None

        # Must contain some alphanumeric
        if not re.search(r'[a-zA-Z0-9]', cleaned):
            return None

        return cleaned

    def _close_dropdown(self):
        """Close the dropdown by clicking elsewhere."""
        try:
            # Click somewhere safe to close dropdown
            window_rect = self.tos_navigator._get_window_rect()
            if window_rect:
                # Click in the center-right area of the window
                center_x = window_rect[0] + (window_rect[2] - window_rect[0]) * 0.7
                center_y = window_rect[1] + (window_rect[3] - window_rect[1]) * 0.5

                pyautogui.click(center_x, center_y)
                time.sleep(0.5)
                print("🖱️ Clicked to close dropdown")
        except Exception as e:
            print(f"⚠️ Could not close dropdown: {e}")


# Integration class for easy use
class DropdownAccountDiscovery:
    def __init__(self):
        """Initialize dropdown-based account discovery."""
        from core.window_manager import WindowManager

        self.window_manager = WindowManager(
            target_exact_title="Main@thinkorswim [build 1985]",
            exclude_title_substring="DeltaMon"
        )
        self.tos_navigator = None
        self.dropdown_reader = None
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

            # Find ToS window
            update_status("📍 Locating ToS window...")
            tos_hwnd = self.window_manager.find_tos_window()
            if not tos_hwnd:
                update_status("❌ ToS window not found")
                return []

            # Focus window
            update_status("🎯 Focusing ToS window...")
            if not self.window_manager.focus_tos_window():
                update_status("⚠️ Warning: Could not focus ToS window")

            # Initialize components
            update_status("🔧 Initializing dropdown reader...")
            self.tos_navigator = TosNavigator(tos_hwnd)
            self.dropdown_reader = EnhancedDropdownReader(self.tos_navigator)

            # Read accounts from dropdown
            update_status("📖 Reading accounts from dropdown...")
            self.discovered_accounts = self.dropdown_reader.read_all_accounts_from_dropdown()

            if self.discovered_accounts:
                update_status(f"✅ Successfully discovered {len(self.discovered_accounts)} accounts!")
                for i, account in enumerate(self.discovered_accounts, 1):
                    update_status(f"   {i:2d}. {account}")
            else:
                update_status("❌ No accounts found in dropdown")

            return self.discovered_accounts

        except Exception as e:
            update_status(f"❌ Discovery error: {e}")
            return []

    def get_discovered_accounts(self) -> List[str]:
        """Get the list of discovered account names."""
        return self.discovered_accounts.copy()


# Test function
if __name__ == "__main__":
    print("Enhanced Dropdown Reader Test")
    print("=" * 40)

    discovery = DropdownAccountDiscovery()
    accounts = discovery.discover_all_accounts()

    if accounts:
        print(f"\n✅ SUCCESS! Found {len(accounts)} accounts:")
        for i, account in enumerate(accounts, 1):
            print(f"   {i:2d}. {account}")
    else:
        print("\n❌ No accounts found")