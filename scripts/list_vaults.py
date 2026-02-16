import sqlite3
from pathlib import Path

def list_vaults():
    conn = sqlite3.connect("data/vultrax.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- Cloud/Global Vaults in vultrax.db ---")
    rows = cursor.execute("SELECT * FROM vaults").fetchall()
    for row in rows:
        print(dict(row))
        
    conn.close()

if __name__ == "__main__":
    list_vaults()
