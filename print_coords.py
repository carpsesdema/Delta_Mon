import pyautogui
import time


def print_mouse_coordinates():
    print("Press Ctrl+C to stop.")
    try:
        while True:
            x, y = pyautogui.position()
            print(f"Mouse coordinates: ({x}, {y})")
            time.sleep(1)  # Adjust the sleep time as needed
    except KeyboardInterrupt:
        print("\nStopped printing mouse coordinates.")


while 1:
    print_mouse_coordinates()
    time.sleep(1)  # Wait before restarting the function