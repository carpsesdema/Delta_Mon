# Delta_Mon/core/optimized_delta_extractor.py

import cv2
import numpy as np
import pyautogui
import os
import time
from typing import Optional, Tuple, List, Dict
from core.tos_navigator import TosNavigator
from utils.ocr_utils import OCRUtils
import re


class OptimizedDeltaExtractor:
    def __init__(self, tos_navigator: TosNavigator):
        """
        Delta extractor optimized for Pradeep's OptionDelta column layout.
        Based on the actual ToS screenshot showing the OptionDelta column.
        """
        self.tos_navigator = tos_navigator
        self.ocr_utils = OCRUtils()

        # Column detection settings based on the screenshot
        self.column_settings = {
            'header_text': 'OptionDelta',
            'expected_column_width': 80,  # Approximate width from screenshot
            'search_area': {
                'x_ratio': 0.3,  # OptionDelta column appears around 30% from left
                'y_ratio': 0.1,  # Start from top area
                'width_ratio': 0.4,  # Search middle portion of screen
                'height_ratio': 0.8,  # Most of the screen height
            }
        }

    def find_option_delta_column_location(self, save_debug: bool = True) -> Optional[Dict]:
        """
        Find the exact location of the OptionDelta column header and boundaries.

        Returns:
            Dictionary with column location info or None
        """
        print("🔍 Searching for OptionDelta column in portfolio view...")

        # Capture the main portfolio area
        portfolio_capture_path = self._capture_portfolio_area()
        if not portfolio_capture_path:
            return None

        # Method 1: Direct text search for "OptionDelta" header
        column_info = self._find_column_header_by_ocr(portfolio_capture_path, save_debug)

        if column_info:
            print(f"✅ Found OptionDelta column header: {column_info}")
            return column_info

        # Method 2: Template matching if available
        column_info = self._find_column_by_template_matching(save_debug)

        if column_info:
            print(f"✅ Found OptionDelta via template: {column_info}")
            return column_info

        print("❌ Could not locate OptionDelta column")
        return None

    def _capture_portfolio_area(self) -> Optional[str]:
        """Capture the portfolio/positions area where OptionDelta column is visible."""
        try:
            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect:
                return None

            left, top, right, bottom = window_rect
            window_width = right - left
            window_height = bottom - top

            # Based on screenshot: capture the main portfolio table area
            # Skip the very top (menus) and focus on the data table
            capture_x = left + int(window_width * 0.02)  # Small left margin
            capture_y = top + int(window_height * 0.15)  # Skip top menus/tabs
            capture_width = int(window_width * 0.96)  # Almost full width
            capture_height = int(window_height * 0.75)  # Main content area

            save_dir = os.path.join(self.tos_navigator.assets_path, 'captures', 'portfolio')
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, 'portfolio_area.png')

            screenshot = pyautogui.screenshot(region=(capture_x, capture_y, capture_width, capture_height))
            screenshot.save(save_path)

            print(f"📸 Portfolio area captured: {capture_width}x{capture_height}")
            return save_path

        except Exception as e:
            print(f"❌ Error capturing portfolio area: {e}")
            return None

    def _find_column_header_by_ocr(self, image_path: str, save_debug: bool) -> Optional[Dict]:
        """Find OptionDelta column header using OCR."""
        try:
            print("🔍 Searching for 'OptionDelta' column header...")

            # Load and preprocess image for header detection
            image = cv2.imread(image_path)
            if image is None:
                return None

            # Focus on the header area (top portion of the capture)
            header_height = min(100, image.shape[0] // 4)  # Top 25% or 100px max
            header_area = image[0:header_height, :]

            # Enhance for text detection
            gray = cv2.cvtColor(header_area, cv2.COLOR_BGR2GRAY)
            enhanced = self._enhance_for_header_detection(gray)

            if save_debug:
                debug_path = image_path.replace('.png', '_header_enhanced.png')
                cv2.imwrite(debug_path, enhanced)
                print(f"🐛 Header debug image: {debug_path}")

            # Run OCR to find column headers
            import pytesseract

            # Get detailed OCR data with bounding boxes
            config = '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            ocr_data = pytesseract.image_to_data(enhanced, config=config, output_type=pytesseract.Output.DICT)

            # Look for "OptionDelta" or close variations
            for i, text in enumerate(ocr_data['text']):
                text_clean = text.strip().lower()
                if 'optiondelta' in text_clean or ('option' in text_clean and 'delta' in text_clean):
                    confidence = ocr_data['conf'][i]
                    if confidence > 30:  # Reasonable confidence threshold
                        x = ocr_data['left'][i]
                        y = ocr_data['top'][i]
                        w = ocr_data['width'][i]
                        h = ocr_data['height'][i]

                        # Calculate column boundaries (extend down into data area)
                        column_info = {
                            'header_text': text.strip(),
                            'header_x': x,
                            'header_y': y,
                            'header_width': w,
                            'header_height': h,
                            'column_x': x,  # Column starts at header x
                            'column_width': max(w, self.column_settings['expected_column_width']),
                            'data_start_y': y + h + 5,  # Data starts below header
                            'confidence': confidence,
                            'method': 'ocr_header_detection'
                        }

                        if save_debug:
                            self._save_column_debug(image, column_info, image_path)

                        return column_info

            # Try looking for just "Delta" as fallback
            for i, text in enumerate(ocr_data['text']):
                text_clean = text.strip().lower()
                if text_clean == 'delta':
                    confidence = ocr_data['conf'][i]
                    if confidence > 40:
                        x = ocr_data['left'][i]
                        y = ocr_data['top'][i]
                        w = ocr_data['width'][i]
                        h = ocr_data['height'][i]

                        column_info = {
                            'header_text': text.strip(),
                            'header_x': x,
                            'header_y': y,
                            'header_width': w,
                            'header_height': h,
                            'column_x': x,
                            'column_width': max(w, self.column_settings['expected_column_width']),
                            'data_start_y': y + h + 5,
                            'confidence': confidence,
                            'method': 'delta_only_detection'
                        }
                        return column_info

            return None

        except Exception as e:
            print(f"❌ OCR header detection error: {e}")
            return None

    def _enhance_for_header_detection(self, gray_image: np.ndarray) -> np.ndarray:
        """Enhance image specifically for detecting column headers."""
        try:
            # Scale up for better OCR
            scale_factor = 2.0
            height, width = gray_image.shape
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            resized = cv2.resize(gray_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

            # Enhance contrast for header text
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(resized)

            # Light blur to smooth text
            blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)

            # Adaptive threshold to handle varying backgrounds
            adaptive_thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Invert for OCR (black text on white background)
            inverted = cv2.bitwise_not(adaptive_thresh)

            return inverted

        except Exception as e:
            print(f"Header enhancement error: {e}")
            return gray_image

    def extract_all_delta_values_from_column(self, column_info: Dict = None) -> List[Dict]:
        """
        Extract all delta values from the OptionDelta column.

        Returns:
            List of dictionaries with row info and delta values
        """
        print("📊 Extracting all delta values from OptionDelta column...")

        if not column_info:
            column_info = self.find_option_delta_column_location()
            if not column_info:
                print("❌ Cannot extract delta values - column not found")
                return []

        # Capture current portfolio state
        portfolio_capture_path = self._capture_portfolio_area()
        if not portfolio_capture_path:
            return []

        # Extract delta values from the column
        delta_values = self._extract_delta_values_from_column_area(
            portfolio_capture_path, column_info
        )

        print(f"✅ Extracted {len(delta_values)} delta values from column")
        return delta_values

    def _extract_delta_values_from_column_area(self, image_path: str, column_info: Dict) -> List[Dict]:
        """Extract all delta values from the specific column area."""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return []

            # Define the column data area
            col_x = column_info['column_x']
            col_width = column_info['column_width']
            data_start_y = column_info.get('data_start_y', column_info['header_y'] + column_info['header_height'] + 5)

            # Extract the column data area (below the header)
            image_height = image.shape[0]
            data_height = image_height - data_start_y - 20  # Leave some bottom margin

            if data_height <= 0:
                print("⚠️ No data area available below header")
                return []

            # Extract column data region
            column_data = image[data_start_y:data_start_y + data_height, col_x:col_x + col_width]

            # Save debug image of column data
            debug_dir = os.path.join(os.path.dirname(image_path), 'column_data')
            os.makedirs(debug_dir, exist_ok=True)
            column_debug_path = os.path.join(debug_dir, 'option_delta_column.png')
            cv2.imwrite(column_debug_path, column_data)
            print(f"🐛 Column data saved: {column_debug_path}")

            # Find individual delta values in the column
            delta_values = self._parse_individual_delta_values(column_debug_path, col_x, data_start_y)

            return delta_values

        except Exception as e:
            print(f"❌ Error extracting column delta values: {e}")
            return []

    def _parse_individual_delta_values(self, column_image_path: str, base_x: int, base_y: int) -> List[Dict]:
        """Parse individual delta values from the column image."""
        try:
            # Load column image
            column_image = cv2.imread(column_image_path, cv2.IMREAD_GRAYSCALE)
            if column_image is None:
                return []

            # Enhance for number recognition
            enhanced = self._enhance_for_number_detection(column_image)

            # Find text regions (potential delta values)
            text_regions = self._find_text_regions_in_column(enhanced)

            delta_results = []

            for i, (region_y, region_height) in enumerate(text_regions):
                # Extract the specific region
                region_image = enhanced[region_y:region_y + region_height, :]

                # Save individual region for debugging
                region_debug_path = column_image_path.replace('.png', f'_region_{i:02d}.png')
                cv2.imwrite(region_debug_path, region_image)

                # OCR the region to get delta value
                delta_value = self._ocr_single_delta_value(region_debug_path)

                if delta_value is not None:
                    delta_result = {
                        'delta_value': delta_value,
                        'region_index': i,
                        'screen_x': base_x,
                        'screen_y': base_y + region_y,
                        'region_height': region_height,
                        'formatted_value': f"{delta_value:+.3f}",
                        'percentage': f"{delta_value * 100:+.1f}%"
                    }
                    delta_results.append(delta_result)
                    print(f"  📍 Region {i}: {delta_value:+.3f} at y={base_y + region_y}")

            return delta_results

        except Exception as e:
            print(f"❌ Error parsing delta values: {e}")
            return []

    def _find_text_regions_in_column(self, enhanced_image: np.ndarray) -> List[Tuple[int, int]]:
        """Find potential text regions (rows) in the column image."""
        try:
            # Use horizontal projection to find text rows
            height, width = enhanced_image.shape

            # Sum pixels horizontally to find text rows
            horizontal_projection = np.sum(enhanced_image, axis=1)

            # Smooth the projection
            from scipy import ndimage
            smoothed = ndimage.gaussian_filter1d(horizontal_projection, sigma=1)

            # Find regions with significant content (text)
            threshold = np.mean(smoothed) * 1.2  # Above average activity

            # Find contiguous regions above threshold
            regions = []
            in_region = False
            region_start = 0

            for i in range(len(smoothed)):
                if smoothed[i] > threshold and not in_region:
                    # Start of new region
                    in_region = True
                    region_start = i
                elif smoothed[i] <= threshold and in_region:
                    # End of region
                    region_height = i - region_start
                    if region_height >= 8:  # Minimum height for text
                        regions.append((region_start, region_height))
                    in_region = False

            # Handle case where region extends to end
            if in_region:
                region_height = len(smoothed) - region_start
                if region_height >= 8:
                    regions.append((region_start, region_height))

            print(f"🔍 Found {len(regions)} potential text regions in column")
            return regions

        except Exception as e:
            print(f"❌ Error finding text regions: {e}")
            return []

    def _enhance_for_number_detection(self, gray_image: np.ndarray) -> np.ndarray:
        """Enhance image specifically for detecting delta numbers."""
        try:
            # Scale up significantly for better OCR on small numbers
            scale_factor = 3.0
            height, width = gray_image.shape
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            resized = cv2.resize(gray_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

            # Strong contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
            enhanced = clahe.apply(resized)

            # Binary threshold
            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Invert for OCR
            inverted = cv2.bitwise_not(thresh)

            # Morphological operations to clean up numbers
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(inverted, cv2.MORPH_CLOSE, kernel)

            return cleaned

        except Exception as e:
            print(f"Number detection enhancement error: {e}")
            return gray_image

    def _ocr_single_delta_value(self, region_image_path: str) -> Optional[float]:
        """Extract a single delta value from a region image using OCR."""
        try:
            import pytesseract

            # Load region image
            region_image = cv2.imread(region_image_path, cv2.IMREAD_GRAYSCALE)
            if region_image is None:
                return None

            # OCR configuration optimized for decimal numbers
            config = '--psm 8 -c tessedit_char_whitelist=0123456789.-+'

            ocr_text = pytesseract.image_to_string(region_image, config=config).strip()

            if not ocr_text:
                return None

            # Parse the delta value
            delta_value = self._parse_delta_number(ocr_text)
            return delta_value

        except Exception as e:
            print(f"❌ OCR single delta error: {e}")
            return None

    def _parse_delta_number(self, ocr_text: str) -> Optional[float]:
        """Parse a delta number from OCR text."""
        try:
            # Clean the text
            cleaned = ocr_text.strip().replace(' ', '').replace('\n', '')

            # Patterns for delta values based on the screenshot
            patterns = [
                r'^([+-]?\d*\.?\d+)$',  # Simple decimal like -0.05, 1.0
                r'([+-]?\d*\.?\d+)',  # Decimal anywhere in string
            ]

            for pattern in patterns:
                match = re.search(pattern, cleaned)
                if match:
                    try:
                        value = float(match.group(1))

                        # Validate range - delta values should be reasonable
                        if -2.0 <= value <= 2.0:  # Extended range based on screenshot
                            return value
                    except ValueError:
                        continue

            return None

        except Exception as e:
            print(f"❌ Delta number parsing error: {e}")
            return None

    def _save_column_debug(self, image: np.ndarray, column_info: Dict, original_path: str):
        """Save debug image showing found column location."""
        try:
            debug_image = image.copy()

            # Draw rectangle around column area
            x = column_info['column_x']
            y = column_info['header_y']
            w = column_info['column_width']
            h = column_info.get('header_height', 30)

            cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(debug_image, 'OptionDelta', (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            debug_path = original_path.replace('.png', '_column_found.png')
            cv2.imwrite(debug_path, debug_image)
            print(f"🐛 Column debug saved: {debug_path}")

        except Exception as e:
            print(f"Debug save error: {e}")

    def check_delta_thresholds(self, delta_values: List[Dict],
                               positive_threshold: float = 0.08,
                               negative_threshold: float = -0.05) -> List[Dict]:
        """
        Check which delta values exceed the specified thresholds.

        Args:
            delta_values: List of delta value dictionaries
            positive_threshold: Alert when delta > this value
            negative_threshold: Alert when delta < this value

        Returns:
            List of delta values that exceed thresholds
        """
        alerts = []

        for delta_info in delta_values:
            delta_value = delta_info['delta_value']

            alert_triggered = False
            alert_type = None

            if delta_value > positive_threshold:
                alert_triggered = True
                alert_type = "HIGH_DELTA"
            elif delta_value < negative_threshold:
                alert_triggered = True
                alert_type = "LOW_DELTA"

            if alert_triggered:
                alert_info = delta_info.copy()
                alert_info.update({
                    'alert_type': alert_type,
                    'threshold_exceeded': positive_threshold if alert_type == "HIGH_DELTA" else negative_threshold,
                    'excess_amount': delta_value - positive_threshold if alert_type == "HIGH_DELTA" else delta_value - negative_threshold
                })
                alerts.append(alert_info)

        return alerts


# Test function for the optimized extractor
if __name__ == "__main__":
    print("Optimized OptionDelta Extractor Test")
    print("=" * 50)

    from core.window_manager import WindowManager

    wm = WindowManager(target_exact_title="Main@thinkorswim [build 1985]")
    tos_hwnd = wm.find_tos_window()

    if tos_hwnd:
        navigator = TosNavigator(tos_hwnd)
        extractor = OptimizedDeltaExtractor(navigator)

        # Test finding the OptionDelta column
        column_info = extractor.find_option_delta_column_location()

        if column_info:
            print(f"✅ Found OptionDelta column: {column_info}")

            # Extract all delta values
            all_delta_values = extractor.extract_all_delta_values_from_column(column_info)

            if all_delta_values:
                print(f"\n📊 Extracted {len(all_delta_values)} delta values:")
                for i, delta_info in enumerate(all_delta_values):
                    print(f"  {i + 1}. {delta_info['formatted_value']} ({delta_info['percentage']})")

                # Check thresholds
                alerts = extractor.check_delta_thresholds(all_delta_values, 0.08, -0.05)

                if alerts:
                    print(f"\n🚨 {len(alerts)} values exceed thresholds:")
                    for alert in alerts:
                        print(f"  ⚠️ {alert['formatted_value']} - {alert['alert_type']}")
                else:
                    print("\n✅ All delta values within thresholds")
            else:
                print("❌ No delta values extracted")
        else:
            print("❌ Could not find OptionDelta column")
    else:
        print("❌ ToS window not found")