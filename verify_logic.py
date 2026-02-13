import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.domain.messages import MESSAGES
from src.presentation.dashboard.card_security_watch import SecurityWatchCard

def test_logic_only():
    print("--- TESTING TRANSLATION OBJECTS ---")
    app = QApplication(sys.argv)
    
    print(f"Current Lang: {MESSAGES.LANG}")
    
    # Check if CARDS section exists in MESSAGES
    if hasattr(MESSAGES, 'CARDS'):
        print("[SUCCESS] MESSAGES.CARDS section exists!")
        print(f"Sample (EN): {MESSAGES.CARDS.SECURITY_WATCH}")
    else:
        print("[FAILURE] MESSAGES.CARDS section missing!")
        return

    print("--- TESTING CARD ISOLATION ---")
    card = SecurityWatchCard()
    print(f"Card Title (Initial): {card.va_h.text()}")
    
    print("--- CHANGING LANG TO ES ---")
    MESSAGES.LANG = "ES"
    # Normally DashboardView calls this recursively. Here we call it manually on the isolated card.
    card.retranslateUi()
    
    print(f"Card Title (After ES Sync): {card.va_h.text()}")
    if "VIGILANCIA" in card.va_h.text().upper():
        print("[SUCCESS] Card retranslated successfully!")
    else:
        print("[FAILURE] Card retranslation failed!")

    print("--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    test_logic_only()
