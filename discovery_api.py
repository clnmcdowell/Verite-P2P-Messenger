
import os
import requests

DISCOVERY_URL = os.getenv("DISCOVERY_URL", "http://127.0.0.1:8000")

def get_available_peers(my_peer_id: str):
    try:
        response = requests.get(f"{DISCOVERY_URL}/peers")
        if response.status_code == 200:
            peers = response.json()
            return [peer for peer in peers if peer["id"] != my_peer_id]
        return []
    except Exception as e:
        print(f"[!] Failed to fetch peers: {e}")
        return []
