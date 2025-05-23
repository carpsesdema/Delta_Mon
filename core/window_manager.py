# Delta_Mon/core/window_manager.py

import win32gui
import win32con
import win32api  # For GetSystemMetrics if needed for primary screen, though GetWindowRect is usually sufficient


class WindowManager:
    def __init__(self, target_exact_title="Main@thinkorswim [build 1985]",
                 target_title_substring=None,  # Can be used as a fallback or alternative
                 exclude_title_substring="DeltaMon"):  # To avoid finding our own app

        self.target_exact_title = target_exact_title.lower() if target_exact_title else None
        self.target_title_substring = target_title_substring.lower() if target_title_substring else None
        self.exclude_title_substring = exclude_title_substring.lower() if exclude_title_substring else None
        self.hwnd = None  # Will store the handle (HWND) of the found window

    def _enum_windows_callback(self, hwnd, found_hwnds_list):
        """Callback function for EnumWindows"""
        if not win32gui.IsWindowVisible(hwnd):
            return True  # Continue enumeration

        window_title = win32gui.GetWindowText(hwnd)
        title_lower = window_title.lower()

        # Skip if it matches the exclusion string
        if self.exclude_title_substring and self.exclude_title_substring in title_lower:
            return True  # Continue enumeration

        # Check for exact title match first
        if self.target_exact_title and self.target_exact_title == title_lower:
            found_hwnds_list.append(hwnd)
            return False  # Stop enumeration, exact match found

        # If no exact title provided or not matched, check for substring
        if self.target_title_substring and self.target_title_substring in title_lower:
            found_hwnds_list.append(hwnd)
            # We could stop here if substring is enough, or collect all and pick one.
            # For ToS, usually one main window, so first substring match is often okay.
            # return False # Optional: stop on first substring match

        return True  # Continue enumeration

    def find_tos_window(self) -> int | None:
        """
        Finds the Thinkorswim window by title.
        Returns the window handle (HWND) or None if not found.
        """
        found_hwnds = []
        try:
            win32gui.EnumWindows(self._enum_windows_callback, found_hwnds)
        except Exception as e:
            print(f"Error during EnumWindows: {e}")
            self.hwnd = None
            return None

        if found_hwnds:
            # If multiple matches (e.g., from substring), prioritize or just take the first.
            # For an exact match, there should ideally be only one.
            self.hwnd = found_hwnds[0]
            window_title = win32gui.GetWindowText(self.hwnd)
            print(f"Found ToS window: '{window_title}' (HWND: {self.hwnd})")
            return self.hwnd
        else:
            print(
                f"ToS window not found (Exact: '{self.target_exact_title}', Substring: '{self.target_title_substring}')")
            self.hwnd = None
            return None

    def get_window_rect(self) -> tuple[int, int, int, int] | None:
        """
        Gets the bounding rectangle of the found ToS window.
        Returns (left, top, right, bottom) screen coordinates or None.
        """
        if not self.hwnd:
            print("Window handle (HWND) not found. Cannot get window rect.")
            # Optionally, try to find it again if not found
            # if not self.find_tos_window():
            #     return None
            return None

        try:
            return win32gui.GetWindowRect(self.hwnd)
        except Exception as e:
            print(f"Error getting window rect for HWND {self.hwnd}: {e}")
            return None

    def focus_tos_window(self) -> bool:
        """
        Activates (brings to front and gives focus to) the ToS window.
        Returns True if successful, False otherwise.
        """
        if not self.hwnd:
            print("Window handle (HWND) not found. Cannot focus window.")
            # Optionally, try to find it again
            if not self.find_tos_window():  # Attempt to find it if not already set
                print("Focus failed: ToS window not found.")
                return False

        if self.hwnd:  # Re-check self.hwnd after the potential find_tos_window call
            try:
                # Restore if minimized
                if win32gui.IsIconic(self.hwnd):
                    win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)

                # Bring to foreground
                win32gui.SetForegroundWindow(self.hwnd)
                # Some applications might need a slight pause or further interaction
                # to fully gain focus for subsequent SendInput/PyAutoGUI actions.
                # For now, SetForegroundWindow should be sufficient.
                print(f"Focused ToS window (HWND: {self.hwnd})")
                return True
            except Exception as e:
                # pywintypes.error: (0, 'SetForegroundWindow', 'No error message is available') can occur
                # if another app is admin and this script isn't, or other focus-stealing issues.
                print(f"Error focusing ToS window (HWND {self.hwnd}): {e}")
                return False
        return False


# Example Usage (for testing this module directly):
if __name__ == "__main__":
    # Using the exact title provided by the user
    wm = WindowManager(target_exact_title="Main@thinkorswim [build 1985]")
    # Alternatively, for a substring test if exact title might vary slightly (e.g. build number)
    # wm = WindowManager(target_title_substring="main@thinkorswim", exclude_title_substring="DeltaMon")

    tos_hwnd = wm.find_tos_window()

    if tos_hwnd:
        print(f"ToS HWND: {tos_hwnd}")
        rect = wm.get_window_rect()
        if rect:
            print(f"ToS Window Rect: {rect} (L: {rect[0]}, T: {rect[1]}, R: {rect[2]}, B: {rect[3]})")
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            print(f"Dimensions: Width={width}, Height={height}")

        # Test focus (be careful, this will bring the window to the front)
        # import time
        # print("Attempting to focus in 3 seconds...")
        # time.sleep(3)
        # if wm.focus_tos_window():
        # print("Focus successful.")
        # else:
        # print("Focus failed.")
    else:
        print("ToS window was not found.")