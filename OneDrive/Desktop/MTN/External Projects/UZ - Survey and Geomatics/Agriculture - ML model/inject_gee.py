import pyautogui
import pyperclip
import pygetwindow as gw
import time
import sys
import os

print("Starting Earth Engine script injection...")

# 1. Read the updated script
script_path = os.path.join(os.path.dirname(__file__), "gee_app.js")
try:
    with open(script_path, "r", encoding="utf-8") as f:
        code = f.read()
    pyperclip.copy(code)
    print("Code copied to clipboard.")
except Exception as e:
    print(f"Error reading script: {e}")
    sys.exit(1)

# 2. Find the active Earth Engine window. Usually it's in a Google Chrome tab named "Earth Engine Code Editor" or similar.
print("Searching for Earth Engine window...")
windows = gw.getWindowsWithTitle("Earth Engine")

if not windows:
    print("Could not find any window with 'Earth Engine' in the title. Make sure the tab is open.")
    sys.exit(1)

# Sort windows by title length or something, or just pick the first one which is usually the active tab if it matches.
win = None
for w in windows:
    if "Earth Engine" in w.title:
        win = w
        break

if not win:
    print("No matching Earth Engine window found.")
    sys.exit(1)

print(f"Found target window: {win.title}")

# 3. Bring window to front
try:
    if win.isMinimized:
        win.restore()
    win.activate()
except Exception as e:
    print(f"Warning on activating window: {e}")

time.sleep(1.0) # wait for window to surface

if not win.isMaximized:
    try:
        win.maximize()
    except Exception:
        pass

time.sleep(1.0)

# 4. Click inside the Code Editor panel.
# We know the GEE layout: The code editor is in the upper middle pane.
# Clicking at 50% width and 35% height usually hits the code area perfectly on most monitors.
click_x = win.left + int(win.width * 0.5)
click_y = win.top + int(win.height * 0.35)

print(f"Clicking inside Code Editor at ({click_x}, {click_y})...")
pyautogui.click(click_x, click_y)
time.sleep(0.5)

# 5. Inject the code
print("Selecting old script...")
pyautogui.hotkey('ctrl', 'a')
time.sleep(0.3)

print("Pasting new script...")
pyautogui.hotkey('ctrl', 'v')
time.sleep(1.0) # Wait for paste to complete, especially if code is long

# 6. Run the script!
print("Running the new script (Ctrl+Enter)...")
pyautogui.hotkey('ctrl', 'enter')

print("Injection complete! The application should now be updating in your browser.")
