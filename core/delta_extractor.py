# Delta_Mon/core/delta_extractor.py

import cv2
import numpy as np
import pyautogui
import os
import time
from typing import Optional, Tuple
from core.tos_navigator import TosNavigator
from utils.ocr_utils import OCRUtils


class DeltaExtractor:
    def __init__(self, tos_navigator: TosNavigator):
        """
        Initialize delta extractor.

        Args:
            tos_navigator: TosNavigator instance for window operations
        """
        self.tos_navigator = tos_navigator
        self.ocr_utils = OCRUtils()

        # Delta indicator search areas (will be refined based on actual layout)
        self.search_areas = [
            {'name': 'top_right', 'x_ratio': 0.7, 'y_ratio': 0.1, 'width_ratio': 0.25, 'height_ratio': 0.3},
            {'name': 'bottom_right', 'x_ratio': 0.7, 'y_ratio': 0.6, 'width_ratio': 0.25, 'height_ratio': 0.3},
            {'name': 'center_right', 'x_ratio': 0.6, 'y_ratio': 0.3, 'width_ratio': 0.35, 'height_ratio': 0.4},
        ]

    def find_delta_indicator(self, account_name: str = "current") -> Optional[Tuple[int, int, int, int]]:
        """
        Find the delta indicator in the current account tab.

        Args:
            account_name: Name of current account (for logging)

        Returns:
            Tuple of (x, y, width, height) relative to window, or None
        """
        print(f"Searching for delta indicator in account: {account_name}")

        # Method 1: Try template matching if we have a delta indicator template
        delta_template_path = os.path.join(self.tos_navigator.assets_path, 'templates', 'delta_indicator_template.png')
        if os.path.exists(delta_template_path):
            result = self.tos_navigator.find_element_on_screen("delta_indicator_template.png", confidence=0.7)
            if result:
                print(f"Found delta indicator using template matching: {result}")
                return result

        # Method 2: Search in common areas where delta indicators typically appear
        for area in self.search_areas:
            result = self._search_in_area(area, account_name)
            if result:
                return result

        print(f"Could not locate delta indicator for account: {account_name}")
        return None

    def _search_in_area(self, search_area: dict, account_name: str) -> Optional[Tuple[int, int, int, int]]:
        """
        Search for delta indicator in a specific area of the window.

        Args:
            search_area: Dictionary defining the search area
            account_name: Account name for logging

        Returns:
            Delta indicator coordinates or None
        """
        try:
            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect:
                return None

            left, top, right, bottom = window_rect
            window_width = right - left
            window_height = bottom - top

            # Calculate search area coordinates
            area_x = int(window_width * search_area['x_ratio'])
            area_y = int(window_height * search_area['y_ratio'])
            area_width = int(window_width * search_area['width_ratio'])
            area_height = int(window_height * search_area['height_ratio'])

            # Capture the search area
            capture_path = self._capture_search_area(
                area_x, area_y, area_width, area_height,
                f"{account_name}_{search_area['name']}_search.png"
            )

            if not capture_path:
                return None

            # Look for delta-like patterns in the captured area
            delta_coords = self._find_delta_pattern(capture_path, area_x, area_y)
            if delta_coords:
                print(f"Found potential delta indicator in {search_area['name']} area: {delta_coords}")
                return delta_coords

        except Exception as e:
            print(f"Error searching area {search_area['name']}: {e}")

        return None

    def _capture_search_area(self, rel_x: int, rel_y: int, width: int, height: int, filename: str) -> Optional[str]:
        """
        Capture a specific search area of the window.

        Args:
            rel_x, rel_y: Position relative to window
            width, height: Dimensions of area to capture
            filename: Name for saved image

        Returns:
            Path to captured image or None
        """
        try:
            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect:
                return None

            win_left, win_top = window_rect[0], window_rect[1]

            # Convert to absolute screen coordinates
            abs_x = win_left + rel_x
            abs_y = win_top + rel_y

            # Capture the area
            save_dir = os.path.join(self.tos_navigator.assets_path, 'captures', 'delta_search')
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, filename)

            screenshot = pyautogui.screenshot(region=(abs_x, abs_y, width, height))
            screenshot.save(save_path)

            return save_path

        except Exception as e:
            print(f"Error capturing search area: {e}")
            return None

    def _find_delta_pattern(self, image_path: str, area_x: int, area_y: int) -> Optional[Tuple[int, int, int, int]]:
        """
        Find delta pattern in captured search area.

        Args:
            image_path: Path to captured search area image
            area_x, area_y: Original area position for coordinate conversion

        Returns:
            Delta indicator coordinates relative to window or None
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return None

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Look for text patterns that might indicate delta values
            # This could include: percentage signs, +/- signs, decimal numbers

            # Method 1: Use OCR to find percentage-like text
            text_regions = self._find_text_regions(gray)

            for region in text_regions:
                # Extract small area around potential text
                x, y, w, h = region
                text_crop_path = image_path.replace('.png', f'_text_{x}_{y}.png')
                text_crop = image[y:y + h, x:x + w]
                cv2.imwrite(text_crop_path, text_crop)

                # Try to extract delta value
                delta_value = self.ocr_utils.extract_delta_value(text_crop_path, debug_save=True)
                if delta_value is not None:
                    # Found a valid delta value, return the region coordinates
                    delta_x = area_x + x
                    delta_y = area_y + y
                    return (delta_x, delta_y, w, h)

            return None

        except Exception as e:
            print(f"Error finding delta pattern: {e}")
            return None

    def _find_text_regions(self, gray_image: np.ndarray) -> list:
        """
        Find potential text regions in the image.

        Args:
            gray_image: Grayscale image

        Returns:
            List of (x, y, width, height) tuples for potential text areas
        """
        try:
            # Apply morphological operations to find text regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

            # Gradient
            gradient = cv2.morphologyEx(gray_image, cv2.MORPH_GRADIENT, kernel)

            # Threshold
            _, thresh = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Morphological operations to connect text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
            connected = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            text_regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Filter by size - text regions should be reasonable size
                if 10 <= w <= 150 and 8 <= h <= 50:
                    # Add some padding
                    x = max(0, x - 5)
                    y = max(0, y - 5)
                    w = min(gray_image.shape[1] - x, w + 10)
                    h = min(gray_image.shape[0] - y, h + 10)

                    text_regions.append((x, y, w, h))

            return text_regions

        except Exception as e:
            print(f"Error finding text regions: {e}")
            return []

    def extract_delta_value(self, account_name: str) -> Optional[float]:
        """
        Extract the delta value for the current account.

        Args:
            account_name: Name of the account being processed

        Returns:
            Delta value as float or None if not found
        """
        print(f"Extracting delta value for account: {account_name}")

        # Find the delta indicator
        delta_coords = self.find_delta_indicator(account_name)
        if not delta_coords:
            print(f"Could not find delta indicator for {account_name}")
            return None

        # Capture the delta indicator area
        delta_image_path = self._capture_delta_area(delta_coords, account_name)
        if not delta_image_path:
            print(f"Could not capture delta area for {account_name}")
            return None

        # Extract the value using OCR
        delta_value = self.ocr_utils.extract_delta_value(delta_image_path, debug_save=True)

        if delta_value is not None:
            print(f"Successfully extracted delta value for {account_name}: {delta_value}")
        else:
            print(f"Failed to extract delta value for {account_name}")

        return delta_value

    def _capture_delta_area(self, delta_coords: Tuple[int, int, int, int], account_name: str) -> Optional[str]:
        """
        Capture the specific delta indicator area.

        Args:
            delta_coords: (x, y, width, height) relative to window
            account_name: Account name for filename

        Returns:
            Path to captured delta image or None
        """
        try:
            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect:
                return None

            win_left, win_top = window_rect[0], window_rect[1]
            rel_x, rel_y, width, height = delta_coords

            # Convert to absolute coordinates
            abs_x = win_left + rel_x
            abs_y = win_top + rel_y

            # Add some padding to ensure we capture the full value
            padding = 10
            abs_x = max(0, abs_x - padding)
            abs_y = max(0, abs_y - padding)
            width += 2 * padding
            height += 2 * padding

            # Capture the delta area
            save_dir = os.path.join(self.tos_navigator.assets_path, 'captures', 'delta_values')
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f'delta_{account_name}_{int(time.time())}.png')

            screenshot = pyautogui.screenshot(region=(abs_x, abs_y, width, height))
            screenshot.save(save_path)

            print(f"Delta area captured: {save_path}")
            return save_path

        except Exception as e:
            print(f"Error capturing delta area: {e}")
            return None