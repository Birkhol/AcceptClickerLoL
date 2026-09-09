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
    SCAN_INTERVAL_SECONDS = 0.1
    ACCEPT_THRESHOLD = 0.8
    CHAMPION_SELECT_THRESHOLD = 0.85

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

    def load_templates(self, image_paths, required):
        templates = []
        for image_path in image_paths:
            template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                if required:
                    raise FileNotFoundError(f"Image not found: {image_path}")
                continue
            templates.append(template)
        return templates

    def find_template(self, screenshot_gray, templates, threshold):
        screenshot_height, screenshot_width = screenshot_gray.shape[:2]

        for template in templates:
            template_height, template_width = template.shape[:2]
            if template_height > screenshot_height or template_width > screenshot_width:
                continue

            result = cv2.matchTemplate(
                screenshot_gray,
                template,
                cv2.TM_CCOEFF_NORMED
            )
            _, best_score, _, best_location = cv2.minMaxLoc(result)

            if best_score >= threshold:
                return best_location, template.shape[:2]

        return None

    def scan_loop(self):
        image_paths_accept = [
            resource_path("resources/AcceptButton.png"),
            resource_path("resources/AcceptButtonSpain.png"),
            resource_path("resources/AcceptButtonFrance.png"),
            resource_path("resources/AcceptButtonKorea.png"),
            resource_path("resources/AcceptButtonPortuguese.png"),
            resource_path("resources/AcceptButtonGermany.png"),
            resource_path("resources/AcceptButtonRussia.png")
        ]
        image_paths_champselect = [
            resource_path("resources/ChampionSelect.png"),
            resource_path("resources/SelectChampionClassic.png"),
            resource_path("resources/ChampionSelectARAMURF.png"),
            resource_path("resources/SelectChampionSpain2.png"),
            resource_path("resources/SelectChampionSpainARAM.png"),
            resource_path("resources/SelectChampionFrance.png"),
            resource_path("resources/SelectChampionFranceARAM.png"),
            resource_path("resources/SelectChampionKorea.png"),
            resource_path("resources/SelectChampionKoreaARAM.png"),
            resource_path("resources/SelectChampionPortuguese.png"),
            resource_path("resources/SelectChampionPortugueseARAM.png"),
            resource_path("resources/SelectChampionGermany.png"),
            resource_path("resources/SelectChampionGermanyARAM.png"),
            resource_path("resources/SelectChampionRussia.png"),
            resource_path("resources/SelectChampionRussiaARAM.png")
        ]

        try:
            accept_templates = self.load_templates(image_paths_accept, required=True)
            champion_select_templates = self.load_templates(
                image_paths_champselect,
                required=False
            )
        except FileNotFoundError as error:
            messagebox.showerror("Error", str(error))
            self.stop_scan()
            return

        waiting_for_champion_select = False

        while self.scanning:
            try:
                scan_started = time.perf_counter()
                screenshot = pyautogui.screenshot()
                screenshot_gray = cv2.cvtColor(
                    np.array(screenshot),
                    cv2.COLOR_RGB2GRAY
                )

                if waiting_for_champion_select:
                    champion_select_match = self.find_template(
                        screenshot_gray,
                        champion_select_templates,
                        self.CHAMPION_SELECT_THRESHOLD
                    )
                    if champion_select_match is not None:
                        self.status_label.config(
                            text="Status: Champion Select detected",
                            fg="#1976D2"
                        )
                        self.stop_scan()
                        return

                accept_match = self.find_template(
                    screenshot_gray,
                    accept_templates,
                    self.ACCEPT_THRESHOLD
                )
                if accept_match is not None:
                    (x, y), (height, width) = accept_match
                    pyautogui.click(x + width // 2, y + height // 2)
                    self.status_label.config(
                        text="Status: Match accepted; waiting for Champion Select...",
                        fg="#2E7D32"
                    )
                    waiting_for_champion_select = True

                elapsed = time.perf_counter() - scan_started
                time.sleep(max(0, self.SCAN_INTERVAL_SECONDS - elapsed))

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
