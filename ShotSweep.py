r"""
ShotSweep- auto-expiring screenshot tool for Windows.

Press a hotkey to take a screenshot. It's saved with an expiry date baked
into the filename and copied to your clipboard for instant pasting/sharing.
A background thread deletes screenshots once they pass their expiry date.

SETUP
------
1. Install dependencies (one time):
   pip install keyboard pillow pywin32

2. Run it:
   python ShotSweep.py

3. (Optional) Make it start automatically with Windows:
   - Win+R -> shell:startup -> create a shortcut to a .bat file containing:
       pythonw C:\path\to\ShotSweep.py
     (pythonw avoids a console window popping up)

USAGE
-----
- Ctrl+Shift+S  -> full-screen screenshot, expires in EXPIRY_DAYS (default 7)
- Ctrl+Shift+K  -> full-screen "keeper" screenshot, never auto-deletes
- Ctrl+Shift+A  -> drag-select an area, expires in EXPIRY_DAYS
- Ctrl+Shift+D  -> drag-select an area, "keeper", never auto-deletes
- Ctrl+Shift+Q  -> quit the program

While selecting an area, press Esc to cancel.
"""

import io
import os
import re
import time
import queue
import threading
from datetime import datetime, timedelta

import keyboard
import tkinter as tk
from PIL import ImageGrab
import win32clipboard

# ---------------- CONFIG ----------------
EXPIRY_MINUTES = 7 * 24 * 60   # 7 days
SAVE_DIR = os.path.join(os.path.expanduser("~"), "Pictures", "QuickShots")
CLEANUP_CHECK_INTERVAL_SECONDS = 60 * 60   # 1 hour
# -----------------------------------------

os.makedirs(SAVE_DIR, exist_ok=True)

FILENAME_PATTERN = re.compile(
    r"shot_(?P<taken>\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_exp(?P<expiry>\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}|never)\.png"
)


def copy_image_to_clipboard(img):
    output = io.BytesIO()
    img.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]  # strip BMP file header, DIB needs raw data
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()


def select_area():
    """Show a fullscreen overlay, let the user drag a rectangle, and return
    the (left, top, right, bottom) box they selected, or None if cancelled
    (e.g. by pressing Esc or clicking without dragging)."""
    result = {}

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.3)
    root.attributes("-topmost", True)
    root.configure(bg="black")
    root.config(cursor="cross")

    canvas = tk.Canvas(root, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    start = {}
    rect_id = None

    def on_press(event):
        start["x"], start["y"] = event.x, event.y

    def on_drag(event):
        nonlocal rect_id
        if rect_id:
            canvas.delete(rect_id)
        rect_id = canvas.create_rectangle(
            start["x"], start["y"], event.x, event.y,
            outline="red", width=2
        )

    def on_release(event):
        x0, y0 = start.get("x"), start.get("y")
        x1, y1 = event.x, event.y
        if x0 is not None and (abs(x1 - x0) > 5 and abs(y1 - y0) > 5):
            result["box"] = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        root.destroy()

    def on_escape(event):
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", on_escape)

    root.update_idletasks()
    root.deiconify()
    root.lift()
    root.focus_force()
    canvas.focus_set()

    root.mainloop()
    return result.get("box")


def take_screenshot(expiry_minutes=None, area=False):
    if area:
        box = select_area()
        if box is None:
            print("[Quick Shot] Selection cancelled.")
            return
        img = ImageGrab.grab(bbox=box)
    else:
        img = ImageGrab.grab()
    now = datetime.now()
    taken_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    if expiry_minutes is None:
        expiry_str = "never"
    else:
        expiry_str = (now + timedelta(minutes=expiry_minutes)).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"shot_{taken_str}_exp{expiry_str}.png"
    path = os.path.join(SAVE_DIR, filename)
    img.save(path, "PNG")
    copy_image_to_clipboard(img)
    label = "keeper (never expires)" if expiry_minutes is None else f"expires {expiry_str}"
    print(f"[Quick Shot] Saved {filename} ({label}) — copied to clipboard.")


def cleanup_loop():
    while True:
        now = datetime.now()
        for fname in os.listdir(SAVE_DIR):
            match = FILENAME_PATTERN.match(fname)
            if not match:
                continue
            expiry = match.group("expiry")
            if expiry == "never":
                continue
            expiry_dt = datetime.strptime(expiry, "%Y-%m-%d_%H-%M-%S")
            if now >= expiry_dt:
                try:
                    os.remove(os.path.join(SAVE_DIR, fname))
                    print(f"[Quick Shot] Deleted expired screenshot: {fname}")
                except OSError as e:
                    print(f"[Quick Shot] Couldn't delete {fname}: {e}")
        time.sleep(CLEANUP_CHECK_INTERVAL_SECONDS)


def main():
    print(f"[Quick Shot] Watching folder: {SAVE_DIR}")
    print(f"[Quick Shot] Default expiry: {EXPIRY_MINUTES} minutes")
    print("[Quick Shot] Ctrl+Shift+S = full screen (expires) | Ctrl+Shift+K = full screen (keeper)")
    print("[Quick Shot] Ctrl+Shift+A = select area (expires) | Ctrl+Shift+D = select area (keeper)")
    print("[Quick Shot] Ctrl+Shift+Q = quit")

    threading.Thread(target=cleanup_loop, daemon=True).start()

    action_queue = queue.Queue()

    # Hotkey callbacks run on keyboard's own background thread. tkinter is not
    # thread-safe, so instead of taking the screenshot right here, we just
    # drop a request on the queue and let the main thread do the actual work.
    keyboard.add_hotkey("ctrl+shift+s", lambda: action_queue.put((EXPIRY_MINUTES, False)))
    keyboard.add_hotkey("ctrl+shift+k", lambda: action_queue.put((None, False)))
    keyboard.add_hotkey("ctrl+shift+a", lambda: action_queue.put((EXPIRY_MINUTES, True)))
    keyboard.add_hotkey("ctrl+shift+d", lambda: action_queue.put((None, True)))
    keyboard.add_hotkey("ctrl+shift+q", lambda: action_queue.put("quit"))

    # Main thread loop: wait for hotkey requests and handle them here, so any
    # tkinter windows (used for area selection) are always created on the
    # main thread.
    while True:
        request = action_queue.get()  # blocks until a hotkey is pressed
        if request == "quit":
            print("[Quick Shot] Quitting.")
            os._exit(0)
        expiry_minutes, area = request
        take_screenshot(expiry_minutes, area=area)


if __name__ == "__main__":
    main()
