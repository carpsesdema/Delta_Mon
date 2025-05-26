# Delta_Mon/utils/ocr_utils.py

import cv2
import pytesseract
import numpy as np
from typing import List, Optional
import re
import os


class OCRUtils:
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize OCR utilities.

        Args:
            tesseract_path: Path to tesseract executable if not in PATH
        """
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # Common preprocessing configurations for different text types
        self.account_config = '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_@.-'
        self.delta_config = '--psm 7 -c tessedit_char_whitelist=0123456789.+-% '

    def preprocess_image_for_text(self, image_path: str, target_type: str = "account") -> Optional[np.ndarray]:
        """
        Preprocess image for better OCR results.

        Args:
            image_path: Path to the image file
            target_type: "account" for account names, "delta" for delta values

        Returns:
            Preprocessed image as numpy array or None if failed
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                print(f"Could not read image: {image_path}")
                return None

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            if target_type == "account":
                # For account names - enhance contrast and reduce noise
                # Apply gaussian blur to reduce noise
                blurred = cv2.GaussianBlur(gray, (3, 3), 0)

                # Apply adaptive threshold to handle varying lighting
                processed = cv2.adaptiveThreshold(
                    blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                )

                # Morphological operations to clean up text
                kernel = np.ones((2, 2), np.uint8)
                processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)

            elif target_type == "delta":
                # For delta values - more aggressive preprocessing for numbers
                # Increase contrast
                alpha = 1.5  # Contrast control
                beta = 20  # Brightness control
                enhanced = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

                # Apply threshold
                _, processed = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                # Dilate to make text thicker and easier to read
                kernel = np.ones((2, 2), np.uint8)
                processed = cv2.dilate(processed, kernel, iterations=1)

            else:
                # Default processing
                _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            return processed

        except Exception as e:
            print(f"Error preprocessing image {image_path}: {e}")
            return None

    def extract_account_names(self, dropdown_image_path: str, debug_save: bool = True) -> List[str]:
        """
        Extract account names from dropdown capture.

        Args:
            dropdown_image_path: Path to captured dropdown image
            debug_save: Whether to save preprocessed image for debugging

        Returns:
            List of detected account names
        """
        print(f"Extracting account names from: {dropdown_image_path}")

        # Preprocess image
        processed_image = self.preprocess_image_for_text(dropdown_image_path, "account")
        if processed_image is None:
            return []

        # Save preprocessed image for debugging if requested
        if debug_save:
            debug_path = dropdown_image_path.replace('.png', '_processed.png')
            cv2.imwrite(debug_path, processed_image)
            print(f"Preprocessed image saved to: {debug_path}")

        try:
            # Run OCR
            raw_text = pytesseract.image_to_string(processed_image, config=self.account_config)
            print(f"Raw OCR text:\n{raw_text}")

            # Parse account names
            account_names = self._parse_account_names(raw_text)
            print(f"Extracted account names: {account_names}")

            return account_names

        except Exception as e:
            print(f"Error during OCR: {e}")
            return []

    def _parse_account_names(self, raw_ocr_text: str) -> List[str]:
        """
        Parse account names from raw OCR text.

        Args:
            raw_ocr_text: Raw text from OCR

        Returns:
            List of cleaned account names
        """
        lines = raw_ocr_text.strip().split('\n')
        account_names = []

        for line in lines:
            cleaned_line = line.strip()
            if not cleaned_line:
                continue

            # Filter out obviously invalid lines
            if len(cleaned_line) < 3:  # Too short to be an account name
                continue
            if re.match(r'^[^a-zA-Z0-9]', cleaned_line):  # Starts with special char
                continue
            if '...' in cleaned_line:  # OCR artifacts
                continue

            # Clean up common OCR errors
            cleaned_line = re.sub(r'[|\\\/]', '', cleaned_line)  # Remove common OCR artifacts
            cleaned_line = re.sub(r'\s+', '_', cleaned_line)  # Replace spaces with underscores

            # Basic validation - account names should contain alphanumeric characters
            if re.search(r'[a-zA-Z0-9]', cleaned_line):
                account_names.append(cleaned_line)

        return account_names

    def extract_delta_value(self, delta_image_path: str, debug_save: bool = True) -> Optional[float]:
        """
        Extract delta percentage value from image.

        Args:
            delta_image_path: Path to image containing delta value
            debug_save: Whether to save preprocessed image for debugging

        Returns:
            Delta value as float or None if not found
        """
        print(f"Extracting delta value from: {delta_image_path}")

        # Preprocess image
        processed_image = self.preprocess_image_for_text(delta_image_path, "delta")
        if processed_image is None:
            return None

        # Save preprocessed image for debugging
        if debug_save:
            debug_path = delta_image_path.replace('.png', '_processed.png')
            cv2.imwrite(debug_path, processed_image)
            print(f"Preprocessed delta image saved to: {debug_path}")

        try:
            # Run OCR
            raw_text = pytesseract.image_to_string(processed_image, config=self.delta_config)
            print(f"Raw delta OCR text: '{raw_text}'")

            # Parse delta value
            delta_value = self._parse_delta_value(raw_text)
            if delta_value is not None:
                print(f"Extracted delta value: {delta_value}")
            else:
                print("Could not parse delta value from OCR text")

            return delta_value

        except Exception as e:
            print(f"Error during delta OCR: {e}")
            return None

    def _parse_delta_value(self, raw_ocr_text: str) -> Optional[float]:
        """
        Parse delta percentage value from raw OCR text.

        Args:
            raw_ocr_text: Raw text from OCR

        Returns:
            Delta value as float (e.g., 0.08 for 0.08%) or None if not found
        """
        # Look for percentage patterns
        # Common patterns: "+0.08%", "-0.15%", "0.08%", "+0.08", "-0.15"
        patterns = [
            r'([+-]?\d+\.?\d*)\s*%',  # With % sign
            r'([+-]?\d+\.?\d*)',  # Without % sign (fallback)
        ]

        for pattern in patterns:
            matches = re.findall(pattern, raw_ocr_text)
            for match in matches:
                try:
                    value = float(match)
                    # Convert to decimal if it looks like a percentage
                    if abs(value) > 1:  # Likely already in percentage form
                        value = value / 100.0
                    return value
                except ValueError:
                    continue

        return None


# Testing function
if __name__ == "__main__":
    ocr = OCRUtils()

    # Test with a sample image if available
    test_image = "assets/captures/debug_dropdown_capture.png"
    if os.path.exists(test_image):
        accounts = ocr.extract_account_names(test_image)
        print(f"Test extraction result: {accounts}")
    else:
        print(f"Test image not found: {test_image}")