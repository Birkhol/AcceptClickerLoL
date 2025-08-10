import tkinter as tk
from tkinter import messagebox
import threading
import time
import cv2
import pyautogui
import numpy as np
import sys
import os

class ImageClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Accept Clicker")
        self.root.geometry("360x250")
        self.root.configure(bg="#f4f4f4")
        self.root.resizable(False, False)
        self.scanning = False
        self.scan_thread = None

        self.build_ui()

    def build_ui(self):
        # Header
        self.title_label = tk.Label(
            self.root,
            text="Accept Clicker",
            font=("Segoe UI", 18, "bold"),
            bg="#f4f4f4",
            fg="#333"
        )
        self.title_label.pack(pady=(20, 10))

        # Description
        self.desc_label = tk.Label(
            self.root,
            text="Automatically scan the screen for an accept button\nand click when found.",
            font=("Segoe UI", 10),
            bg="#f4f4f4",
            fg="#666"
        )
        self.desc_label.pack(pady=(0, 10))

        # Buttons Frame
        button_frame = tk.Frame(self.root, bg="#f4f4f4")
        button_frame.pack(pady=10)

        self.start_button = tk.Button(
            button_frame,
            text="▶ Start Scan",
            command=self.start_scan,
            font=("Segoe UI", 10, "bold"),
            bg="#4CAF50",
            fg="white",
            activebackground="#45A049",
            padx=20,
            pady=10,
            bd=0,
            relief="flat",
            cursor="hand2"
        )
        self.start_button.grid(row=0, column=0, padx=10)

        self.stop_button = tk.Button(
            button_frame,
            text="■ Stop Scan",
            command=self.stop_scan,
            font=("Segoe UI", 10, "bold"),
            bg="#F44336",
            fg="white",
            activebackground="#D32F2F",
            padx=20,
            pady=10,
            bd=0,
            relief="flat",
            cursor="hand2",
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=1, padx=10)

        # Status Label
        self.status_label = tk.Label(
            self.root,
            text="Status: Idle",
            font=("Segoe UI", 10, "italic"),
            bg="#f4f4f4",
            fg="#444"
        )
        self.status_label.pack(pady=10)

    def start_scan(self):
        if not self.scanning:
            self.scanning = True
            self.status_label.config(text="Status: Scanning...", fg="#2E7D32")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.scan_thread = threading.Thread(target=self.scan_loop)
            self.scan_thread.daemon = True
            self.scan_thread.start()

    def stop_scan(self):
        self.scanning = False
        self.status_label.config(text="Status: Idle", fg="#444")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def check_champion_select(self, screenshot_bgr):
        image_paths_champselect = [
            resource_path("resources/ChampionSelect.png"),
            resource_path("resources/ChampionSelectARAMURF.png"),
            resource_path("resources/SelectChampionSpain2.png"),
            resource_path("resources/SelectChampionSpainARAM.png"),
            resource_path("resources/SelectChampionFrance.png"),
            resource_path("resources/SelectChampionFranceARAM.png"),
            resource_path("resources/SelectChampionKorea.png"),
            resource_path("resources/SelectChampionKoreaARAM.png")
        ]

        for image in image_paths_champselect:
            template = cv2.imread(image)
            if template is None:
                continue

            result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= 0.85)

            if len(locations[0]) > 0:
                return True

        return False

    def scan_loop(self):
        image_paths_accept = [
            resource_path("resources/AcceptButton.png"),
            resource_path("resources/AcceptButtonSpain.png"),
            resource_path("resources/AcceptButtonFrance.png"),
            resource_path("resources/AcceptButtonKorea.png")
        ]

        templates = []
        for image in image_paths_accept:
            template = cv2.imread(image)
            if template is None:
                messagebox.showerror("Error", f"Image not found: {image}")
                self.stop_scan()
                return
            templates.append(template)

        while self.scanning:
            try:
                screenshot = pyautogui.screenshot()
                screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

                # First check if we're in champ select
                if self.check_champion_select(screenshot_bgr):
                    self.status_label.config(text="Status: Champion Select detected", fg="#1976D2")
                    self.stop_scan()
                    return

                for template in templates:
                    result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
                    threshold = 0.8
                    locations = np.where(result >= threshold)

                    if len(locations[0]) > 0:
                        y, x = locations[0][0], locations[1][0]
                        h, w = template.shape[:2]
                        center_x, center_y = x + w // 2, y + h // 2
                        pyautogui.moveTo(center_x, center_y, duration=0.2)
                        pyautogui.click()
                        time.sleep(1)  # Prevent spamming clicks

                        # After accepting, wait a few seconds to check for Champ Select
                        for _ in range(70):  #21 seconds max
                            screenshot = pyautogui.screenshot()
                            screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                            if self.check_champion_select(screenshot_bgr):
                                self.status_label.config(text="Status: Champion Select detected", fg="#1976D2")
                                self.stop_scan()
                                self.root.quit()
                                sys.exit()
                            time.sleep(0.3)
                        break
                else:
                    time.sleep(0.3)

            except Exception as e:
                messagebox.showerror("Error during scanning", str(e))
                self.stop_scan()

# Run the app
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # temp folder when running as .exe
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap(resource_path("resources/accepticon2.ico"))
    app = ImageClickerApp(root)
    root.mainloop()
