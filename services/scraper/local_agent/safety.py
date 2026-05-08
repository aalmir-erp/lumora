"""Failsafe controls for desktop automation.

Three layers, all enabled when desktop mode is active:
1. pyautogui mouse-to-corner failsafe (built-in)
2. Global hotkey: Ctrl+Alt+Q -> immediate exit
3. Dry-run mode: print the action and require ENTER before executing
"""
from __future__ import annotations

import os
import sys
import threading


DRY_RUN = os.getenv("AGENT_DRY_RUN", "0") == "1"


def install_failsafes() -> None:
    """Install pyautogui failsafe + global Ctrl+Alt+Q kill switch."""
    try:
        import pyautogui  # type: ignore
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05
    except Exception as e:
        print(f"[safety] pyautogui not available: {e}", file=sys.stderr)

    def _hotkey_loop() -> None:
        try:
            from pynput import keyboard  # type: ignore
        except Exception:
            return
        pressed: set[str] = set()

        def on_press(key) -> None:
            try:
                k = key.char if hasattr(key, "char") and key.char else str(key)
            except Exception:
                k = str(key)
            pressed.add(k)
            if "Key.ctrl" in pressed or "Key.ctrl_l" in pressed or "Key.ctrl_r" in pressed:
                if "Key.alt" in pressed or "Key.alt_l" in pressed or "Key.alt_r" in pressed:
                    if "q" in pressed or "Q" in pressed:
                        print("[safety] Ctrl+Alt+Q pressed — exiting agent.", file=sys.stderr)
                        os._exit(2)

        def on_release(key) -> None:
            try:
                k = key.char if hasattr(key, "char") and key.char else str(key)
            except Exception:
                k = str(key)
            pressed.discard(k)

        with keyboard.Listener(on_press=on_press, on_release=on_release) as l:
            l.join()

    t = threading.Thread(target=_hotkey_loop, daemon=True)
    t.start()


def confirm_action(description: str) -> bool:
    if not DRY_RUN:
        return True
    print(f"[dry-run] About to: {description}")
    try:
        ans = input("[dry-run] Press ENTER to execute, or type 'skip': ").strip().lower()
    except EOFError:
        return False
    return ans != "skip"
