import requests
import json

URL = "https://htktaodjjxfsqsqedylu.supabase.co"
KEY = "sb_publishable_wokz-BbGYIvuc4Kvaz3qXg_vrkmg_yA"

def list_all_tables():
    # Supabase allows querying the rpc or a specialized view if exposed.
    # Alternatively, we can try to guess or use the standard PostgREST way to list tables
    # if the API allows it (usually it doesn't without proper permissions).
    # Since we are an "Expert", let's try to query the REST root which sometimes gives a list of tables.
    
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}"
    }
    
    print("\n--- FETCHING SUPABASE REST DEFINITION ---")
    r = requests.get(f"{URL}/rest/v1/", headers=headers)
    if r.status_code == 200:
        try:
            spec = r.json()
            definitions = spec.get("definitions", {})
            print("Found tables in definition:")
            for table in definitions.keys():
                print(f"- {table}")
        except:
            print("Could not parse JSON Spec.")
            print(r.text[:500])
    else:
        print(f"Error fetching spec: {r.status_code}")
        print(r.text)

if __name__ == "__main__":
    list_all_tables()
