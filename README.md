# ShotSweep

A lightweight Windows tool for people who take a *lot* of screenshots just to share something once, then never clean them up. ShotSweep lets you take a screenshot with a hotkey and automatically deletes it after a set number of days — unless you explicitly mark it as a keeper.

No more folders full of screenshots you don't remember taking.

## Features

- **Global hotkeys** — works from anywhere, no need to switch windows.
- **Auto-expiring screenshots** — set once and forget; old screenshots clean themselves up.
- **"Keeper" mode** — mark a screenshot to never auto-delete.
- **Full screen or area select** — drag to capture just the region you need.
- **Clipboard copy** — every screenshot is copied to your clipboard instantly for pasting into chats, emails, etc.
- **Runs quietly in the background** — no console window, minimal resource use.
- **Self-contained** — expiry is stored in the filename itself, no database required.

## Hotkeys

| Hotkey | Action |
|---|---|
| `Ctrl+Shift+S` | Full-screen screenshot, expires in `EXPIRY_MINUTES` (default 7 days) |
| `Ctrl+Shift+K` | Full-screen screenshot, **keeper** (never auto-deletes) |
| `Ctrl+Shift+A` | Drag-select an area, expires |
| `Ctrl+Shift+D` | Drag-select an area, **keeper** |
| `Ctrl+Shift+Q` | Quit the program |
| `Esc` | Cancel an area selection in progress |

## Installation

### Requirements
- Windows 10/11
- [Python 3.8+](https://www.python.org/downloads/) (make sure "Add python.exe to PATH" is checked during install)

### Setup
1. Clone or download this repo and unzip it.
2. Double-click `setup.bat`.

That's it. `setup.bat` will:
- Install the required Python packages (`keyboard`, `pillow`, `pywin32`)
- Launch ShotSweep immediately in the background
- Register it to auto-start every time you log into Windows

Screenshots are saved to `Pictures\ShotSweep` in your user folder.

### Manual install (alternative)
```
pip install -r requirements.txt
python ShotSweep.py
```

## Configuration

Open `ShotSweep.py` and edit the values near the top of the file:

```python
EXPIRY_MINUTES = 7 * 24 * 60   # how long until an expiring screenshot is deleted
SAVE_DIR = os.path.join(os.path.expanduser("~"), "Pictures", "ShotSweep")
CLEANUP_CHECK_INTERVAL_SECONDS = 60 * 60   # how often the cleanup check runs
```

Lower `EXPIRY_MINUTES` and `CLEANUP_CHECK_INTERVAL_SECONDS` if you want to test the expiry behavior quickly (e.g. `EXPIRY_MINUTES = 2`, `CLEANUP_CHECK_INTERVAL_SECONDS = 20`).

## How it works

- Screenshot files are named like `shot_2026-07-09_18-30-12_exp2026-07-16_18-30-12.png` — the expiry timestamp is embedded directly in the filename.
- A background thread wakes up periodically, checks all files in the save folder, and deletes any whose embedded expiry timestamp has passed.
- "Keeper" screenshots are saved with `expnever` in the filename and are never touched by the cleanup thread.
- Because hotkeys are handled by a background listener thread but screenshot area-selection needs a UI window, hotkey presses are routed through a thread-safe queue and processed on the main thread — this keeps the selection overlay responsive and avoids Windows threading quirks with Tkinter.

## Uninstalling

1. Delete the shortcut/file from your Startup folder: press `Win+R`, type `shell:startup`, and remove `start_quick_shot.vbs`.
2. End the `pythonw.exe` process in Task Manager if it's currently running, or press `Ctrl+Shift+Q` while it's focused... it has no window, so Task Manager is the reliable way to stop it if you didn't use the quit hotkey.
3. Delete the project folder.

## Notes

- Requires the `keyboard` library's global hook, which occasionally needs to be run as Administrator to register hotkeys reliably, especially if other elevated apps are running.
- This is a personal utility project — contributions and forks welcome, but it comes with no warranty. Double check `Pictures\ShotSweep` occasionally until you trust the expiry settings you've configured.

## License

MIT — do whatever you want with it.