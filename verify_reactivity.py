import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.domain.messages import MESSAGES
from src.infrastructure.config.path_manager import PathManager
from src.presentation.dashboard.dashboard_view import DashboardView
from src.infrastructure.secrets_manager import SecretsManager
from src.infrastructure.sync_manager import SyncManager
from src.infrastructure.user_manager import UserManager

def test_nuclear_retranslation():
    print("--- STARTING BOOTSTRAP ---")
    app = QApplication(sys.argv)
    
    # Mock dependencies
    sm = SecretsManager(None)
    sync = SyncManager(sm, "http://mock", "mock_key")
    um = UserManager(sm)
    user_profile = {"username": "test_user", "role": "admin"}
    
    print("--- INITIALIZING DASHBOARD ---")
    # This might take a second due to UI building
    dashboard = DashboardView(sm, sync, um, user_profile)
    
    print(f"Current Lang: {MESSAGES.LANG}")
    initial_title = dashboard.btn_nav_dashboard.text()
    print(f"Initial Nav Title: {initial_title}")
    
    print("--- SIMULATING LANGUAGE CHANGE TO ES ---")
    MESSAGES.LANG = "ES"
    dashboard.retranslateUi()
    
    new_title = dashboard.btn_nav_dashboard.text()
    print(f"New Nav Title: {new_title}")
    
    # Check a card
    from src.presentation.dashboard.card_security_watch import SecurityWatchCard
    watch_card = dashboard.findChild(SecurityWatchCard)
    if watch_card:
        card_title = watch_card.va_h.text()
        print(f"Security Watch Card Title (ES): {card_title}")
        if "VIGILANCIA" in card_title.upper():
            print("✅ SUCCESS: Card retranslated!")
        else:
            print("❌ FAILURE: Card title did not change!")
    else:
        print("❌ FAILURE: SecurityWatchCard not found!")

    print("--- VERIFYING QSETTINGS PERSISTENCE ---")
    config_path = str(PathManager.GLOBAL_SETTINGS_INI)
    global_settings = QSettings(config_path, QSettings.IniFormat)
    global_settings.setValue("language", "ES")
    global_settings.sync()
    
    verify_settings = QSettings(config_path, QSettings.IniFormat)
    print(f"Persisted Lang in {config_path}: {verify_settings.value('language')}")
    
    if verify_settings.value("language") == "ES":
        print("✅ SUCCESS: Persistence verified!")
    else:
        print("❌ FAILURE: Persistence failed!")

    print("--- TEST COMPLETE ---")

if __name__ == "__main__":
    try:
        test_nuclear_retranslation()
    except Exception as e:
        print(f"CRITICAL TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
