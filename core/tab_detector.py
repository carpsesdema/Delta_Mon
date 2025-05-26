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
        """
        Initialize tab detector with TOS navigator.

        Args:
            tos_navigator: TosNavigator instance for window operations
        """
        self.tos_navigator = tos_navigator
        self.current_tab_index = 0
        self.total_tabs = 0

        # Tab navigation coordinates (will be detected)
        self.tab_area_coords = None
        self.tab_positions = []

    def detect_account_tabs(self) -> List[dict]:
        """
        Detect all available account tabs in ToS.

        Returns:
            List of tab info dictionaries with positions and potentially names
        """
        print("Detecting account tabs...")

        # First, try to find the tab area using template matching
        tab_area = self._find_tab_area()
        if not tab_area:
            print("Could not locate tab area in ToS window")
            return []

        # Capture the tab area
        tab_image_path = self._capture_tab_area(tab_area)
        if not tab_image_path:
            print("Could not capture tab area")
            return []

        # Analyze the captured tab area to find individual tabs
        tabs = self._analyze_tab_positions(tab_image_path, tab_area)

        print(f"Detected {len(tabs)} account tabs")
        return tabs

    def _find_tab_area(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Find the area where account tabs are located.

        Returns:
            Tuple of (x, y, width, height) relative to window, or None
        """
        # Try to find tab area using template matching
        # Look for common tab area indicators or use a general approach

        # Method 1: Look for a tab template if available
        tab_template_path = os.path.join(self.tos_navigator.assets_path, 'templates', 'tab_area_template.png')
        if os.path.exists(tab_template_path):
            result = self.tos_navigator.find_element_on_screen("tab_area_template.png", confidence=0.6)
            if result:
                return result

        # Method 2: Use window analysis to find likely tab area
        window_rect = self.tos_navigator._get_window_rect()
        if not window_rect:
            return None

        left, top, right, bottom = window_rect
        window_width = right - left
        window_height = bottom - top

        # Tabs are typically in the upper portion of the window
        # Estimate tab area (adjust these values based on your ToS layout)
        estimated_tab_x = 50  # Offset from left edge
        estimated_tab_y = 80  # Offset from top edge
        estimated_tab_width = window_width - 100  # Most of window width
        estimated_tab_height = 40  # Typical tab height

        return (estimated_tab_x, estimated_tab_y, estimated_tab_width, estimated_tab_height)

    def _capture_tab_area(self, tab_area: Tuple[int, int, int, int]) -> Optional[str]:
        """
        Capture the tab area for analysis.

        Args:
            tab_area: (x, y, width, height) relative to window

        Returns:
            Path to captured image or None
        """
        try:
            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect:
                return None

            win_left, win_top = window_rect[0], window_rect[1]
            tab_x, tab_y, tab_width, tab_height = tab_area

            # Convert to absolute screen coordinates
            abs_x = win_left + tab_x
            abs_y = win_top + tab_y

            # Capture the tab area
            save_dir = os.path.join(self.tos_navigator.assets_path, 'captures')
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, 'tab_area_capture.png')

            screenshot = pyautogui.screenshot(region=(abs_x, abs_y, tab_width, tab_height))
            screenshot.save(save_path)

            print(f"Tab area captured: {save_path}")
            return save_path

        except Exception as e:
            print(f"Error capturing tab area: {e}")
            return None

    def _analyze_tab_positions(self, tab_image_path: str, tab_area: Tuple[int, int, int, int]) -> List[dict]:
        """
        Analyze captured tab image to find individual tab positions.

        Args:
            tab_image_path: Path to captured tab area image
            tab_area: Original tab area coordinates

        Returns:
            List of tab dictionaries with position info
        """
        try:
            # Read the captured tab image
            tab_image = cv2.imread(tab_image_path)
            if tab_image is None:
                print(f"Could not read tab image: {tab_image_path}")
                return []

            # Convert to grayscale for analysis
            gray = cv2.cvtColor(tab_image, cv2.COLOR_BGR2GRAY)

            # Find tab boundaries using edge detection and contours
            # This is a simplified approach - may need refinement based on actual ToS tab appearance

            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)

            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            tabs = []
            tab_x_base, tab_y_base = tab_area[0], tab_area[1]

            # Alternative approach: detect vertical lines that might separate tabs
            # For now, let's use a simpler approach assuming tabs are roughly evenly spaced

            tab_width = tab_image.shape[1]
            tab_height = tab_image.shape[0]

            # Estimate number of tabs based on common layouts (adjust as needed)
            estimated_tab_count = max(1, min(8, tab_width // 120))  # Assume ~120px per tab minimum

            for i in range(estimated_tab_count):
                tab_start_x = (tab_width // estimated_tab_count) * i
                tab_end_x = (tab_width // estimated_tab_count) * (i + 1)

                # Create tab info
                tab_info = {
                    'index': i,
                    'relative_x': tab_x_base + tab_start_x,
                    'relative_y': tab_y_base,
                    'width': tab_end_x - tab_start_x,
                    'height': tab_height,
                    'center_x': tab_x_base + (tab_start_x + tab_end_x) // 2,
                    'center_y': tab_y_base + tab_height // 2,
                    'name': f"Tab_{i + 1}"  # Will be updated when we get actual names
                }
                tabs.append(tab_info)

            # Save debug image with detected tab boundaries
            debug_image = tab_image.copy()
            for tab in tabs:
                start_x = tab['relative_x'] - tab_x_base
                end_x = start_x + tab['width']
                cv2.rectangle(debug_image, (start_x, 0), (end_x, tab_height), (0, 255, 0), 2)
                cv2.putText(debug_image, tab['name'], (start_x + 5, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            debug_path = tab_image_path.replace('.png', '_analyzed.png')
            cv2.imwrite(debug_path, debug_image)
            print(f"Tab analysis debug image saved: {debug_path}")

            return tabs

        except Exception as e:
            print(f"Error analyzing tab positions: {e}")
            return []

    def switch_to_tab(self, tab_info: dict) -> bool:
        """
        Switch to a specific account tab.

        Args:
            tab_info: Tab information dictionary from detect_account_tabs()

        Returns:
            True if successful, False otherwise
        """
        try:
            window_rect = self.tos_navigator._get_window_rect()
            if not window_rect:
                print("Cannot switch tab: window rect not found")
                return False

            win_left, win_top = window_rect[0], window_rect[1]

            # Calculate absolute click coordinates
            click_x = win_left + tab_info['center_x']
            click_y = win_top + tab_info['center_y']

            print(f"Switching to tab '{tab_info['name']}' at ({click_x}, {click_y})")

            # Click the tab
            pyautogui.click(click_x, click_y)

            # Wait for tab to load
            time.sleep(1.0)

            self.current_tab_index = tab_info['index']
            return True

        except Exception as e:
            print(f"Error switching to tab: {e}")
            return False

    def get_current_tab_index(self) -> int:
        """Get the index of the currently active tab."""
        return self.current_tab_index

    def update_tab_names(self, tabs: List[dict], account_names: List[str]):
        """
        Update tab information with actual account names.

        Args:
            tabs: List of tab dictionaries
            account_names: List of account names from dropdown discovery
        """
        for i, tab in enumerate(tabs):
            if i < len(account_names):
                tab['name'] = account_names[i]
                tab['account_name'] = account_names[i]
            else:
                tab['account_name'] = f"Unknown_Account_{i + 1}"