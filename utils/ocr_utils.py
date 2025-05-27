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
        Initialize OCR utilities optimized for OptionDelta column values.

        Args:
            tesseract_path: Path to tesseract executable if not in PATH
        """
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # Optimized OCR configurations for OptionDelta values
        self.account_config = '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_@.-'
        self.delta_config = '--psm 8 -c tessedit_char_whitelist=0123456789.+-'  # Simplified for delta values
        self.header_config = '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    def preprocess_image_for_text(self, image_path: str, target_type: str = "account") -> Optional[np.ndarray]:
        """
        Preprocess image for better OCR results.

        Args:
            image_path: Path to the image file
            target_type: "account", "delta", or "header"

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
                blurred = cv2.GaussianBlur(gray, (3, 3), 0)
                processed = cv2.adaptiveThreshold(
                    blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                )
                kernel = np.ones((2, 2), np.uint8)
                processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)

            elif target_type == "delta":
                # Optimized for OptionDelta values like -0.05, 1.0, -0.19
                # Scale up significantly for small numbers
                scale_factor = 4.0
                height, width = gray.shape
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                resized = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

                # Strong contrast enhancement
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
                enhanced = clahe.apply(resized)

                # Apply adaptive threshold
                processed = cv2.adaptiveThreshold(
                    enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                )

                # Invert if needed (OCR works better with black text on white)
                if np.mean(processed) < 127:  # If image is mostly dark
                    processed = cv2.bitwise_not(processed)

                # Clean up with morphological operations
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
                processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)

            elif target_type == "header":
                # For column headers like "OptionDelta"
                # Scale up for better recognition
                scale_factor = 2.5
                height, width = gray.shape
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                resized = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

                # Enhance contrast
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(resized)

                # Threshold
                _, processed = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                # Invert for OCR
                processed = cv2.bitwise_not(processed)

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

    def extract_delta_value(self, delta_image_path: str, debug_save: bool = True) -> Optional[float]:
        """
        Extract delta percentage value from image.
        Optimized for OptionDelta column values like -0.05, 1.0, -0.19

        Args:
            delta_image_path: Path to image containing delta value
            debug_save: Whether to save preprocessed image for debugging

        Returns:
            Delta value as float or None if not found
        """
        print(f"Extracting delta value from: {delta_image_path}")

        # Preprocess image specifically for delta values
        processed_image = self.preprocess_image_for_text(delta_image_path, "delta")
        if processed_image is None:
            return None

        # Save preprocessed image for debugging
        if debug_save:
            debug_path = delta_image_path.replace('.png', '_processed.png')
            cv2.imwrite(debug_path, processed_image)
            print(f"Preprocessed delta image saved to: {debug_path}")

        try:
            # Run OCR with delta-optimized config
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

    def extract_column_header(self, header_image_path: str, debug_save: bool = True) -> Optional[str]:
        """
        Extract column header text (like "OptionDelta").

        Args:
            header_image_path: Path to image containing header text
            debug_save: Whether to save preprocessed image

        Returns:
            Header text or None if not found
        """
        print(f"Extracting column header from: {header_image_path}")

        processed_image = self.preprocess_image_for_text(header_image_path, "header")
        if processed_image is None:
            return None

        if debug_save:
            debug_path = header_image_path.replace('.png', '_header_processed.png')
            cv2.imwrite(debug_path, processed_image)

        try:
            raw_text = pytesseract.image_to_string(processed_image, config=self.header_config)
            cleaned_text = raw_text.strip()

            print(f"Raw header OCR text: '{cleaned_text}'")

            # Look for "OptionDelta" or similar
            if 'option' in cleaned_text.lower() and 'delta' in cleaned_text.lower():
                return cleaned_text
            elif 'delta' in cleaned_text.lower():
                return cleaned_text

            return cleaned_text if cleaned_text else None

        except Exception as e:
            print(f"Error during header OCR: {e}")
            return None

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

    def _parse_delta_value(self, raw_ocr_text: str) -> Optional[float]:
        """
        Parse delta value from raw OCR text.
        Optimized for OptionDelta values from the screenshot.

        Args:
            raw_ocr_text: Raw text from OCR

        Returns:
            Delta value as float or None if not found
        """
        try:
            if not raw_ocr_text:
                return None

            # Clean the text
            cleaned = raw_ocr_text.strip().replace(' ', '').replace('\n', '')

            # Patterns specifically for OptionDelta values
            # Based on screenshot: values like 1.0, -0.05, -0.1, -0.03, -0.08, etc.
            patterns = [
                r'^([+-]?\d+\.?\d*)$',  # Simple: 1.0, -0.05, -0.1
                r'^([+-]?\d*\.?\d+)$',  # Alternative: .05, -.1
                r'([+-]?\d+\.?\d*)',  # Within text
                r'([+-]?\d*\.?\d+)',  # Alternative within text
            ]

            for pattern in patterns:
                match = re.search(pattern, cleaned)
                if match:
                    try:
                        value = float(match.group(1))

                        # Validate range - OptionDelta values should be reasonable
                        # From screenshot, values range from -0.19 to 1.0
                        if -2.0 <= value <= 2.0:
                            return value

                    except ValueError:
                        continue

            # Special handling for common OCR errors
            # Sometimes "1.0" gets read as "10" or similar
            if cleaned.isdigit():
                num_val = int(cleaned)
                if 10 <= num_val <= 19:  # Likely "1.0" read as "10"
                    return 1.0
                elif 1 <= num_val <= 9:  # Single digit
                    return float(num_val) / 10.0  # Convert to decimal

            print(f"⚠️ Could not parse delta value from: '{cleaned}'")
            return None

        except Exception as e:
            print(f"❌ Delta parsing error: {e}")
            return None

    def extract_multiple_delta_values(self, column_image_path: str, debug_save: bool = True) -> List[float]:
        """
        Extract multiple delta values from a column image.

        Args:
            column_image_path: Path to column image with multiple delta values
            debug_save: Whether to save debug images

        Returns:
            List of delta values found
        """
        print(f"Extracting multiple delta values from: {column_image_path}")

        processed_image = self.preprocess_image_for_text(column_image_path, "delta")
        if processed_image is None:
            return []

        if debug_save:
            debug_path = column_image_path.replace('.png', '_multi_processed.png')
            cv2.imwrite(debug_path, processed_image)

        try:
            # Use different PSM mode for multiple text lines
            multi_config = '--psm 6 -c tessedit_char_whitelist=0123456789.+-'
            raw_text = pytesseract.image_to_string(processed_image, config=multi_config)

            print(f"Raw multi-delta OCR text:\n{raw_text}")

            # Parse each line as a potential delta value
            lines = raw_text.strip().split('\n')
            delta_values = []

            for line in lines:
                line = line.strip()
                if line:
                    delta_val = self._parse_delta_value(line)
                    if delta_val is not None:
                        delta_values.append(delta_val)

            print(f"Extracted {len(delta_values)} delta values: {delta_values}")
            return delta_values

        except Exception as e:
            print(f"Error extracting multiple delta values: {e}")
            return []


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

    # Test delta value extraction
    delta_test_image = "assets/captures/delta_values/test_delta.png"
    if os.path.exists(delta_test_image):
        delta_val = ocr.extract_delta_value(delta_test_image)
        print(f"Test delta extraction: {delta_val}")