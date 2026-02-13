from PyQt5.QtCore import QSettings
import sys
import os

ini_path = r"c:\PassGuardian_v2\data\global_settings.ini"
settings = QSettings(ini_path, QSettings.IniFormat)
settings.setValue("language", "ES")
settings.setValue("theme_active", "neon_overdrive")
settings.sync()

print(f"Verified sync to {ini_path}")
with open(ini_path, 'r') as f:
    print(f.read())
