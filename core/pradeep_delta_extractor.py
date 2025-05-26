# Delta_Mon/core/pradeep_delta_extractor.py

import cv2
import numpy as np
import pyautogui
import os
import time
from typing import Optional, Tuple, List, Dict
from core.tos_navigator import TosNavigator
from utils.ocr_utils import OCRUtils
import re


class PradeepDeltaExtractor:
    def __init__(self, tos_navigator: TosNavigator):
        """
        Delta extractor specifically designed for Pradeep's OptionDelta column setup.

        Args:
            tos_navigator: TosNavigator instance for window operations
        """
        self.tos_navigator = tos_navigator
        self.ocr_utils = OCRUtils()

        # Settings based on Pradeep's actual setup
        self.column_settings = {
            'header_text': 'OptionDelta',
            'search_area': {
                'x_ratio': 0.1,  # Start searching from 10% from left
                'y_ratio': 0.1,  # Start from 10% from top
                'width_ratio': 0.8,  # Search most of the window width
                'height_ratio': 0.8,  # Search most of the window height
            },
            'value_format': {
                'decimal_places': 3,
                'expected_range': (-1.0, 1.0),  # Typical delta range
                'pattern': r'[+-]?\d*\.?\d+',  # Regex for decimal numbers
            }
        }

    def find_option_delta_column(self, save_debug: bool = True) -> Optional[Dict]:
        """
        Find the OptionDelta column header in Pradeep's ToS interface.

        Args:
            save_debug: Whether to save debug images

        Returns:
            Dictionary with column position info or None
        """
        print("🔍 Searching for OptionDelta column...")

        # Capture the main ToS window area
        window_capture_path = self._capture_window_area()
        if not window_capture_path:
            return None

        # Method 1: Look for "OptionDelta" text using OCR
        column_info = self._find_column_by_text_search(window_capture_path, save_debug)

        if column_info:
            print(f"✅ Found OptionDelta column at position: {column_info}")
            return column_info

        # Method 2: Template matching if we have a template
        column_info = self._find_column_by_template(window_capture_path, save_debug)

        if column_info:
            print(f"✅ Found OptionDelta column via template: {column_info}")
            return column_info

        print("❌ Could not locate OptionDelta column")
        return None

    def _capture_window_area(self) -> Optional[str]:
        """Capture the main ToS window area for analysis."""
        try:
            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect:
                return None

            left, top, right, bottom = window_rect
            window_width = right - left
            window_height = bottom - top

            # Capture the main content area (skip title bar)
            capture_x = left + int(window_width * 0.02)
            capture_y = top + int(window_height * 0.08)  # Skip title bar
            capture_width = int(window_width * 0.96)
            capture_height = int(window_height * 0.85)

            # Save capture
            save_dir = os.path.join(self.tos_navigator.assets_path, 'captures', 'delta_extraction')
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, 'window_capture.png')

            screenshot = pyautogui.screenshot(region=(capture_x, capture_y, capture_width, capture_height))
            screenshot.save(save_path)

            print(f"📸 Window captured: {capture_width}x{capture_height}")
            return save_path

        except Exception as e:
            print(f"❌ Error capturing window: {e}")
            return None

    def _find_column_by_text_search(self, image_path: str, save_debug: bool) -> Optional[Dict]:
        """Find OptionDelta column by searching for the text."""
        try:
            print("🔍 Searching for 'OptionDelta' text...")

            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return None

            # Convert to grayscale and enhance for text detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Create enhanced version for better OCR
            enhanced = self._enhance_for_text_detection(gray)

            if save_debug:
                debug_path = image_path.replace('.png', '_enhanced.png')
                cv2.imwrite(debug_path, enhanced)

            # Use OCR to find all text in the image
            import pytesseract

            # Get detailed OCR data with bounding boxes
            ocr_data = pytesseract.image_to_data(enhanced, output_type=pytesseract.Output.DICT)

            # Look for "OptionDelta" text
            for i, text in enumerate(ocr_data['text']):
                if 'option' in text.lower() and 'delta' in text.lower():
                    # Found potential match
                    confidence = ocr_data['conf'][i]
                    if confidence > 30:  # Reasonable confidence
                        x = ocr_data['left'][i]
                        y = ocr_data['top'][i]
                        w = ocr_data['width'][i]
                        h = ocr_data['height'][i]

                        column_info = {
                            'header_text': text,
                            'x': x, 'y': y, 'width': w, 'height': h,
                            'confidence': confidence,
                            'method': 'text_search'
                        }

                        if save_debug:
                            self._save_column_debug(image, column_info, image_path)

                        return column_info

            # Also try looking for just "Delta" in case OCR splits the text
            for i, text in enumerate(ocr_data['text']):
                if text.lower().strip() == 'delta':
                    confidence = ocr_data['conf'][i]
                    if confidence > 40:
                        x = ocr_data['left'][i]
                        y = ocr_data['top'][i]
                        w = ocr_data['width'][i]
                        h = ocr_data['height'][i]

                        column_info = {
                            'header_text': text,
                            'x': x, 'y': y, 'width': w, 'height': h,
                            'confidence': confidence,
                            'method': 'text_search_delta_only'
                        }
                        return column_info

            return None

        except Exception as e:
            print(f"❌ Text search error: {e}")
            return None

    def _enhance_for_text_detection(self, gray_image: np.ndarray) -> np.ndarray:
        """Enhance image specifically for detecting column header text."""
        try:
            # Resize for better OCR (text detection works better on larger images)
            scale_factor = 2.0
            height, width = gray_image.shape
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            resized = cv2.resize(gray_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

            # Enhance contrast for dark ToS theme
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(resized)

            # Slight blur to smooth text
            blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)

            # Threshold to get white text on black background (invert for OCR)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # OCR works better with black text on white background, so invert
            inverted = cv2.bitwise_not(thresh)

            return inverted

        except Exception as e:
            print(f"Enhancement error: {e}")
            return gray_image

    def _find_column_by_template(self, image_path: str, save_debug: bool) -> Optional[Dict]:
        """Find column using template matching (if template exists)."""
        try:
            template_path = os.path.join(self.tos_navigator.assets_path, 'templates', 'option_delta_header.png')
            if not os.path.exists(template_path):
                print("📝 No OptionDelta template found (this is normal for first run)")
                return None

            print("🎯 Using template matching for OptionDelta header...")

            # Standard template matching
            result = self.tos_navigator.find_element_on_screen("option_delta_header.png", confidence=0.7)

            if result:
                x, y, w, h = result
                return {
                    'header_text': 'OptionDelta',
                    'x': x, 'y': y, 'width': w, 'height': h,
                    'confidence': 0.8,
                    'method': 'template_match'
                }

            return None

        except Exception as e:
            print(f"Template matching error: {e}")
            return None

    def extract_delta_value_for_account(self, account_name: str,
                                        column_info: Dict = None) -> Optional[float]:
        """
        Extract the delta value for a specific account from the OptionDelta column.

        Args:
            account_name: Name of the account to extract delta for
            column_info: Column position info (will search if not provided)

        Returns:
            Delta value as float or None if not found
        """
        print(f"🎯 Extracting delta value for account: {account_name}")

        # Find column if not provided
        if not column_info:
            column_info = self.find_option_delta_column()
            if not column_info:
                print("❌ Could not locate OptionDelta column")
                return None

        # Capture the current window state
        window_capture_path = self._capture_window_area()
        if not window_capture_path:
            return None

        # Find the account row and extract delta value
        delta_value = self._extract_delta_from_account_row(
            window_capture_path, account_name, column_info
        )

        if delta_value is not None:
            print(f"✅ Found delta for {account_name}: {delta_value}")
        else:
            print(f"❌ Could not extract delta for {account_name}")

        return delta_value

    def _extract_delta_from_account_row(self, image_path: str, account_name: str,
                                        column_info: Dict) -> Optional[float]:
        """Extract delta value from the account's row in the OptionDelta column."""
        try:
            # Load the window capture
            image = cv2.imread(image_path)
            if image is None:
                return None

            # Step 1: Find the row containing the account name
            account_row_y = self._find_account_row(image, account_name)
            if account_row_y is None:
                print(f"❌ Could not find row for account: {account_name}")
                return None

            # Step 2: Extract the delta value from the OptionDelta column at that row
            column_x = column_info['x']
            column_width = column_info.get('width', 80)  # Default width

            # Define extraction area (account row + column area)
            extract_x = column_x
            extract_y = account_row_y - 5  # Small buffer above
            extract_width = column_width
            extract_height = 25  # Typical row height

            # Ensure we don't go out of bounds
            extract_x = max(0, extract_x)
            extract_y = max(0, extract_y)
            extract_width = min(image.shape[1] - extract_x, extract_width)
            extract_height = min(image.shape[0] - extract_y, extract_height)

            # Extract the delta value area
            delta_area = image[extract_y:extract_y + extract_height, extract_x:extract_x + extract_width]

            # Save debug image
            debug_dir = os.path.join(os.path.dirname(image_path), 'delta_values')
            os.makedirs(debug_dir, exist_ok=True)
            debug_path = os.path.join(debug_dir, f'delta_{account_name}.png')
            cv2.imwrite(debug_path, delta_area)

            # Use OCR to extract the delta value
            delta_value = self._ocr_delta_value(debug_path)

            return delta_value

        except Exception as e:
            print(f"❌ Error extracting delta from row: {e}")
            return None

    def _find_account_row(self, image: np.ndarray, account_name: str) -> Optional[int]:
        """Find the Y coordinate of the row containing the account name."""
        try:
            # Convert to grayscale and enhance
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            enhanced = self._enhance_for_text_detection(gray)

            # Save temp image for OCR
            temp_path = os.path.join(os.path.dirname(self.tos_navigator.assets_path), 'temp_account_search.png')
            cv2.imwrite(temp_path, enhanced)

            # Use OCR to find all text with positions
            import pytesseract
            ocr_data = pytesseract.image_to_data(enhanced, output_type=pytesseract.Output.DICT)

            # Look for the account name
            for i, text in enumerate(ocr_data['text']):
                if account_name.lower() in text.lower() or text.lower() in account_name.lower():
                    confidence = ocr_data['conf'][i]
                    if confidence > 30:
                        # Found the account, return the Y coordinate
                        y = ocr_data['top'][i]
                        print(f"📍 Found account '{account_name}' at Y position: {y}")

                        # Clean up temp file
                        try:
                            os.remove(temp_path)
                        except:
                            pass

                        return y

            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass

            return None

        except Exception as e:
            print(f"❌ Error finding account row: {e}")
            return None

    def _ocr_delta_value(self, delta_image_path: str) -> Optional[float]:
        """Extract numeric delta value from image using OCR."""
        try:
            # Load and preprocess the delta area image
            image = cv2.imread(delta_image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                return None

            # Enhance for number recognition
            enhanced = self._enhance_for_number_ocr(image)

            # Save enhanced version for debugging
            enhanced_path = delta_image_path.replace('.png', '_enhanced.png')
            cv2.imwrite(enhanced_path, enhanced)

            # Use OCR to extract text
            import pytesseract

            # OCR config optimized for numbers
            config = '--psm 8 -c tessedit_char_whitelist=0123456789.-+'

            ocr_text = pytesseract.image_to_string(enhanced, config=config).strip()
            print(f"🔍 OCR raw text: '{ocr_text}'")

            # Parse the delta value
            delta_value = self._parse_delta_value(ocr_text)

            return delta_value

        except Exception as e:
            print(f"❌ OCR delta value error: {e}")
            return None

    def _enhance_for_number_ocr(self, gray_image: np.ndarray) -> np.ndarray:
        """Enhance image specifically for reading numeric delta values."""
        try:
            # Scale up for better OCR
            scale_factor = 3.0
            height, width = gray_image.shape
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            resized = cv2.resize(gray_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

            # Strong contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
            enhanced = clahe.apply(resized)

            # Threshold to get clean black/white
            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Invert for OCR (black text on white background)
            inverted = cv2.bitwise_not(thresh)

            # Morphological operations to clean up numbers
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(inverted, cv2.MORPH_CLOSE, kernel)

            return cleaned

        except Exception as e:
            print(f"Number OCR enhancement error: {e}")
            return gray_image

    def _parse_delta_value(self, ocr_text: str) -> Optional[float]:
        """Parse delta value from OCR text."""
        try:
            if not ocr_text:
                return None

            # Clean the text
            cleaned = ocr_text.strip().replace(' ', '')

            # Look for decimal number patterns
            patterns = [
                r'^([+-]?\d*\.?\d+)$',  # Simple decimal
                r'([+-]?\d*\.?\d+)',  # Decimal anywhere in string
                r'^([+-]?\d+\.?\d*)$',  # Alternative format
            ]

            for pattern in patterns:
                match = re.search(pattern, cleaned)
                if match:
                    try:
                        value = float(match.group(1))

                        # Validate range (delta values should be between -1 and 1 typically)
                        if -1.5 <= value <= 1.5:
                            return value

                    except ValueError:
                        continue

            print(f"⚠️ Could not parse delta value from: '{ocr_text}'")
            return None

        except Exception as e:
            print(f"❌ Delta parsing error: {e}")
            return None

    def _save_column_debug(self, image: np.ndarray, column_info: Dict, original_path: str):
        """Save debug image showing found column location."""
        try:
            debug_image = image.copy()

            x, y, w, h = column_info['x'], column_info['y'], column_info['width'], column_info['height']

            # Draw rectangle around found column
            cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Add text label
            cv2.putText(debug_image, f"OptionDelta ({column_info['confidence']:.1f})",
                        (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            debug_path = original_path.replace('.png', '_column_debug.png')
            cv2.imwrite(debug_path, debug_image)

            print(f"🐛 Column debug saved: {debug_path}")

        except Exception as e:
            print(f"Debug save error: {e}")

    def create_option_delta_template(self, column_info: Dict) -> bool:
        """Create a template from the found OptionDelta column for future use."""
        try:
            # Capture current window
            window_capture_path = self._capture_window_area()
            if not window_capture_path:
                return False

            # Load image and extract column header area
            image = cv2.imread(window_capture_path)
            if image is None:
                return False

            x, y, w, h = column_info['x'], column_info['y'], column_info['width'], column_info['height']

            # Add some padding
            padding = 5
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(image.shape[1] - x, w + 2 * padding)
            h = min(image.shape[0] - y, h + 2 * padding)

            # Extract template
            template = image[y:y + h, x:x + w]

            # Save template
            templates_dir = os.path.join(self.tos_navigator.assets_path, 'templates')
            os.makedirs(templates_dir, exist_ok=True)
            template_path = os.path.join(templates_dir, 'option_delta_header.png')

            cv2.imwrite(template_path, template)

            print(f"✅ OptionDelta template created: {template_path}")
            return True

        except Exception as e:
            print(f"❌ Template creation error: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    print("Pradeep's OptionDelta Extractor Test")
    print("=" * 40)

    # This would be used with actual ToS window
    from core.window_manager import WindowManager

    wm = WindowManager(target_exact_title="Main@thinkorswim [build 1985]")
    tos_hwnd = wm.find_tos_window()

    if tos_hwnd:
        navigator = TosNavigator(tos_hwnd)
        extractor = PradeepDeltaExtractor(navigator)

        # Test finding the column
        column_info = extractor.find_option_delta_column()

        if column_info:
            print(f"✅ Found OptionDelta column: {column_info}")

            # Create template for future use
            extractor.create_option_delta_template(column_info)

            # Test extracting a delta value (you'd replace with actual account name)
            test_account = "TEST_ACCOUNT"  # Replace with real account name
            delta_value = extractor.extract_delta_value_for_account(test_account, column_info)

            if delta_value is not None:
                print(f"✅ Extracted delta: {delta_value}")
            else:
                print("❌ Could not extract delta value")
        else:
            print("❌ Could not find OptionDelta column")
    else:
        print("❌ ToS window not found")