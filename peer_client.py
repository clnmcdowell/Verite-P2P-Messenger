import requests
import socket
import threading

DISCOVERY_URL = "http://127.0.0.1:8000"  # Replace with your discovery server URL or LAN IP
PEER_ID = input("Enter your peer ID: ")
LISTEN_PORT = int(input("Enter the port to listen on: "))

def register_with_discovery_server():
    """
    Register the peer with the discovery server.
    """
    print("[*] Registering with discovery server...")
    payload = {
        "id": PEER_ID,
        "port": LISTEN_PORT
    }

    # Send a POST request to the discovery server to register the peer
    try:
        response = requests.post(f"{DISCOVERY_URL}/register", json=payload)
        if response.status_code == 200:
            print("[✓] Successfully registered with discovery server.")
            print("[*] Peer ID:", PEER_ID)
        else:
            print("[!] Failed to register with discovery server:", response.text)
    except Exception as e:
        print("[!] Error connecting to discovery server:", e)

def get_available_peers():
    """
    Fetch the list of currently available peers from the discovery server.
    Returns a list of peers excluding this one.
    """
    print("[*] Fetching list of available peers...")

    try:
        response = requests.get(f"{DISCOVERY_URL}/peers")
        if response.status_code == 200:
            peers = response.json()
            # Filter out this peer
            other_peers = [peer for peer in peers if peer['id'] != PEER_ID]
            print(f"[✓] Found {len(other_peers)} other peer(s) online.")
            for peer in other_peers:
                print(f"    - {peer['id']} at {peer['ip']}:{peer['port']}")
            return other_peers
        else:
            print("[!] Failed to fetch peers:", response.text)
            return []
    except Exception as e:
        print("[!] Error fetching peers:", e)
        return []
