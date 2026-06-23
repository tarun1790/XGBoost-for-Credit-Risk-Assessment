import os
import time

# PyAutoGUI display connection check
try:
    import pyautogui
    pyautogui.FAILSAFE = True # Fail-safe: move mouse to corner to abort
    import pyperclip
    HAS_GUI = True
except Exception:
    HAS_GUI = False

from app.core.config import settings

class DesktopControlAgent:
    def __init__(self):
        self.screenshots_dir = settings.SCREENSHOTS_DIR
        os.makedirs(self.screenshots_dir, exist_ok=True)
        if not HAS_GUI:
            print("[Warning] GUI Display or PyAutoGUI/Pyperclip not found. Desktop Control will operate in SIMULATION mode.")

    def click(self, x: int, y: int) -> dict:
        """
        Left clicks at the exact screen coordinates (x, y).
        """
        if HAS_GUI:
            try:
                pyautogui.click(x, y)
                return {"success": True, "action": f"Clicked at ({x}, {y})"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            return {"success": True, "simulated": True, "action": f"Mock click at ({x}, {y})"}

    def type(self, text: str, press_enter: bool = False) -> dict:
        """
        Types the specified text on the active keyboard focus.
        """
        if HAS_GUI:
            try:
                pyautogui.write(text, interval=0.05)
                if press_enter:
                    pyautogui.press('enter')
                return {"success": True, "action": f"Typed text: '{text}'"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            return {"success": True, "simulated": True, "action": f"Mock type text: '{text}'"}

    def press_key(self, key_combination: str) -> dict:
        """
        Executes keyboard combinations (e.g. 'ctrl', 'c' or 'win', 'r').
        """
        if HAS_GUI:
            try:
                keys = [k.strip() for k in key_combination.split('+')]
                if len(keys) > 1:
                    pyautogui.hotkey(*keys)
                else:
                    pyautogui.press(keys[0])
                return {"success": True, "action": f"Executed hotkey: {key_combination}"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            return {"success": True, "simulated": True, "action": f"Mock hotkey execution: {key_combination}"}

    def drag_to(self, x: int, y: int, duration: float = 1.0) -> dict:
        if HAS_GUI:
            try:
                pyautogui.dragTo(x, y, duration=duration)
                return {"success": True, "action": f"Dragged cursor to ({x}, {y})"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            return {"success": True, "simulated": True, "action": f"Mock drag to ({x}, {y})"}

    def get_clipboard(self) -> str:
        if HAS_GUI:
            try:
                return pyperclip.paste()
            except Exception:
                return ""
        return "Simulated clipboard content"

    def set_clipboard(self, text: str) -> bool:
        if HAS_GUI:
            try:
                pyperclip.copy(text)
                return True
            except Exception:
                return False
        return True

    def capture_desktop_screenshot(self, filename: str) -> str:
        """
        Takes a full screenshot of the local physical screen.
        """
        path = os.path.join(self.screenshots_dir, filename)
        if HAS_GUI:
            try:
                screenshot = pyautogui.screenshot()
                screenshot.save(path)
                return path
            except Exception as e:
                print(f"Failed to capture physical screen: {e}. Falling back to blank image.")
                
        # Fallback / Mock: Generate a solid black image representing empty screen
        try:
            from PIL import Image
            img = Image.new('RGB', (1920, 1080), color=(10, 10, 10))
            img.save(path)
        except Exception:
            pass
        return path

desktop_agent = DesktopControlAgent()
