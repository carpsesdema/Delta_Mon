# Delta_Mon/utils/ocr_utils.py

import cv2
import pytesseract
import numpy as np
from typing import List, Optional
import re
import os
import sys


class OCRUtils:
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize OCR utilities with bundled Tesseract (no client install needed!)
        """
        # Try bundled Tesseract first
        if not tesseract_path:
            tesseract_path = self._find_bundled_tesseract()

        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            print(f"✅ Using bundled Tesseract at: {tesseract_path}")
        else:
            print("❌ Bundled Tesseract not found!")
            print("🔧 To bundle Tesseract:")
            print("   1. Copy C:\\Program Files\\Tesseract-OCR\\ to your project as 'tesseract\\'")
            print("   2. Include the 'tesseract\\' folder when distributing your app")
            raise RuntimeError("Tesseract not found. Please bundle Tesseract with your application.")

        # Test if tesseract works
        try:
            pytesseract.get_tesseract_version()
            print("✅ Tesseract is working correctly")
        except Exception as e:
            print(f"❌ Tesseract test failed: {e}")
            raise

        # Optimized OCR configurations
        self.account_config = '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_@.-'
        self.delta_config = '--psm 8 -c tessedit_char_whitelist=0123456789.+-'
        self.header_config = '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    def _find_bundled_tesseract(self) -> Optional[str]:
        """Find bundled Tesseract executable"""
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Look for bundled tesseract
        bundled_paths = [
            os.path.join(script_dir, 'tesseract', 'tesseract.exe'),  # Bundled with app
            os.path.join(script_dir, 'tesseract-ocr', 'tesseract.exe'),  # Alternative name
            os.path.join(script_dir, 'bin', 'tesseract.exe'),  # In bin folder
        ]

        for path in bundled_paths:
            if os.path.exists(path):
                print(f"Found bundled Tesseract: {path}")
                return path

        # If no bundled version, try system paths as fallback
        system_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]

        for path in system_paths:
            if os.path.exists(path):
                print(f"Found system Tesseract: {path}")
                return path

        return None

    def preprocess_image_for_text(self, image_path: str, target_type: str = "account") -> Optional[np.ndarray]:
        """
        Preprocess image for better OCR results.
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                print(f"Could not read image: {image_path}")
                return None

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            if target_type == "account":
                blurred = cv2.GaussianBlur(gray, (3, 3), 0)
                processed = cv2.adaptiveThreshold(
                    blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                )
                kernel = np.ones((2, 2), np.uint8)
                processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)

            elif target_type == "delta":
                scale_factor = 4.0
                height, width = gray.shape
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                resized = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
                enhanced = clahe.apply(resized)

                processed = cv2.adaptiveThreshold(
                    enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                )

                if np.mean(processed) < 127:
                    processed = cv2.bitwise_not(processed)

                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
                processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)

            elif target_type == "header":
                scale_factor = 2.5
                height, width = gray.shape
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                resized = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(resized)

                _, processed = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                processed = cv2.bitwise_not(processed)

            else:
                _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            return processed

        except Exception as e:
            print(f"Error preprocessing image {image_path}: {e}")
            return None

    def extract_account_names(self, dropdown_image_path: str, debug_save: bool = True) -> List[str]:
        """Extract account names from dropdown capture."""
        print(f"Extracting account names from: {dropdown_image_path}")

        processed_image = self.preprocess_image_for_text(dropdown_image_path, "account")
        if processed_image is None:
            return []

        if debug_save:
            debug_path = dropdown_image_path.replace('.png', '_processed.png')
            cv2.imwrite(debug_path, processed_image)
            print(f"Preprocessed image saved to: {debug_path}")

        try:
            raw_text = pytesseract.image_to_string(processed_image, config=self.account_config)
            print(f"Raw OCR text:\n{raw_text}")

            account_names = self._parse_account_names(raw_text)
            print(f"Extracted account names: {account_names}")

            return account_names

        except Exception as e:
            print(f"Error during OCR: {e}")
            return []

    def extract_delta_value(self, delta_image_path: str, debug_save: bool = True) -> Optional[float]:
        """Extract delta percentage value from image."""
        print(f"Extracting delta value from: {delta_image_path}")

        processed_image = self.preprocess_image_for_text(delta_image_path, "delta")
        if processed_image is None:
            return None

        if debug_save:
            debug_path = delta_image_path.replace('.png', '_processed.png')
            cv2.imwrite(debug_path, processed_image)
            print(f"Preprocessed delta image saved to: {debug_path}")

        try:
            raw_text = pytesseract.image_to_string(processed_image, config=self.delta_config)
            print(f"Raw delta OCR text: '{raw_text}'")

            delta_value = self._parse_delta_value(raw_text)
            if delta_value is not None:
                print(f"Successfully extracted delta value: {delta_value}")
            else:
                print("Could not parse delta value from OCR text")

            return delta_value

        except Exception as e:
            print(f"Error during delta OCR: {e}")
            return None

    def _parse_account_names(self, raw_ocr_text: str) -> List[str]:
        """Parse account names from raw OCR text."""
        lines = raw_ocr_text.strip().split('\n')
        account_names = []

        for line in lines:
            cleaned_line = line.strip()
            if not cleaned_line:
                continue

            if len(cleaned_line) < 3:
                continue
            if re.match(r'^[^a-zA-Z0-9]', cleaned_line):
                continue
            if '...' in cleaned_line:
                continue

            cleaned_line = re.sub(r'[|\\\/]', '', cleaned_line)
            cleaned_line = re.sub(r'\s+', '_', cleaned_line)

            if re.search(r'[a-zA-Z0-9]', cleaned_line):
                account_names.append(cleaned_line)

        return account_names

    def _parse_delta_value(self, raw_ocr_text: str) -> Optional[float]:
        """Parse delta value from raw OCR text."""
        try:
            if not raw_ocr_text:
                return None

            cleaned = raw_ocr_text.strip().replace(' ', '').replace('\n', '')

            patterns = [
                r'^([+-]?\d+\.?\d*)$',
                r'^([+-]?\d*\.?\d+)$',
                r'([+-]?\d+\.?\d*)',
                r'([+-]?\d*\.?\d+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, cleaned)
                if match:
                    try:
                        value = float(match.group(1))
                        if -2.0 <= value <= 2.0:
                            return value
                    except ValueError:
                        continue

            if cleaned.isdigit():
                num_val = int(cleaned)
                if 10 <= num_val <= 19:
                    return 1.0
                elif 1 <= num_val <= 9:
                    return float(num_val) / 10.0

            print(f"⚠️ Could not parse delta value from: '{cleaned}'")
            return None

        except Exception as e:
            print(f"❌ Delta parsing error: {e}")
            return None


# Instructions for bundling Tesseract
def create_bundle_instructions():
    instructions = """
    🔧 TO BUNDLE TESSERACT WITH YOUR APP:

    1. Copy Tesseract folder:
       Copy: C:\\Program Files\\Tesseract-OCR\\
       To: your_project\\tesseract\\

    2. Your project structure should look like:
       Delta_Mon/
       ├── tesseract/
       │   ├── tesseract.exe
       │   ├── tessdata/
       │   └── (other tesseract files)
       ├── core/
       ├── utils/
       └── main.py

    3. When distributing, include the tesseract/ folder

    4. The OCRUtils will automatically find and use the bundled version!
    """
    print(instructions)


if __name__ == "__main__":
    try:
        ocr = OCRUtils()
        print("✅ OCR initialized successfully")
    except Exception as e:
        print(f"❌ OCR initialization failed: {e}")
        create_bundle_instructions()