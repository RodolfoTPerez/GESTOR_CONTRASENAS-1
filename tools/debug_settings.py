from PyQt5.QtCore import QSettings
from src.presentation.theme_manager import ThemeManager
import sys

def check():
    settings = QSettings(ThemeManager.APP_ID, "PassGuardian_Global")
    print(f"--- Global Settings ---")
    print(f"File: {settings.fileName()}")
    keys = settings.allKeys()
    for k in keys:
        try:
            val = settings.value(k)
            print(f"  {k}: {repr(val)}")
        except Exception as e:
            print(f"  {k}: [ERROR PRINTING VALUE: {e}]")
    
    print("\n--- User Settings (RODOLFO) ---")
    u_settings = QSettings(ThemeManager.APP_ID, "PassGuardian_RODOLFO")
    print(f"File: {u_settings.fileName()}")
    for k in u_settings.allKeys():
        try:
            val = u_settings.value(k)
            print(f"  {k}: {repr(val)}")
        except Exception as e:
            print(f"  {k}: [ERROR PRINTING VALUE: {e}]")

if __name__ == "__main__":
    check()
