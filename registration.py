import requests
import os

DISCOVERY_URL = os.getenv("DISCOVERY_URL", "http://127.0.0.1:8000")

def register_peer(peer_id: str, port: int):
    payload = {"id": peer_id, "port": port}
    try:
        res = requests.post(f"{DISCOVERY_URL}/register", json=payload)
        if res.status_code == 200:
            print(f"[✓] Registered peer '{peer_id}' on port {port}")
        else:
            print("[!] Failed to register:", res.text)
    except Exception as e:
        print(f"[!] Error registering with discovery server: {e}")
