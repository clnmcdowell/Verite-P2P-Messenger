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
    
def handle_incoming_connection(conn, addr):
    """
    Handle incoming connections from other peers."
    """
    print(f"\n[+] Incoming connection from {addr}\n> ", end="")

    # Receive data from the peer
    try:
        while True:
            data = conn.recv(4096) # Buffer size of 4096 bytes
            if not data:
                break
    except Exception as e:
        print(f"[!] Error handling connection from {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Disconnected from {addr}")

def start_listener():
    """
    Start a listener to accept incoming connections from other peers."
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", LISTEN_PORT))
    server_socket.listen()
    print(f"[*] Listening for incoming peer messages on port {LISTEN_PORT}...")

    print("[*] Press Ctrl+C to exit.")

    # Start a thread to handle incoming connections
    def listen_loop():
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_incoming_connection, args=(conn, addr), daemon=True).start()

    # Start the listener loop in a separate thread
    threading.Thread(target=listen_loop, daemon=True).start()

def receive_messages(sock):
    """
    Continuously receive and print messages from the connected peer.
    Runs in a separate thread.
    """
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                print("\n[!] Connection closed by peer.")
                break
            print(f"\n[←] {data.decode().strip()}\n> ", end="")
    except Exception as e:
        print(f"[!] Error receiving message: {e}")


def chat_with_peer(peer_ip, peer_port):
    """
    Start a chat session with another peer.
    Sends multiple messages until 'exit' is entered.
    """
    print(f"[*] Connecting to {peer_ip}:{peer_port}...")

    # Check if the peer is reachable
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((peer_ip, peer_port))
            print("[✓] Connected. Type messages below (type '/quit' to quit):")

            # Start background thread to receive messages
            threading.Thread(target=receive_messages, args=(s,), daemon=True).start()

            # Main loop: send messages
            while True:
                message = input("> ")
                if message.strip().lower() == "/quit":
                    print("[*] Ending chat session.")
                    
                # Tag the message with the peer ID and send it
                tagged_message = f"{PEER_ID} says: {message}"
                s.sendall(tagged_message.encode())

    except Exception as e:
        print(f"[!] Error connecting to {peer_ip}:{peer_port}: {e}")


if __name__ == "__main__":
    register_with_discovery_server()
    start_listener()

    print(f"\n[✓] Peer '{PEER_ID}' is registered and listening on port {LISTEN_PORT}.")
    print("[*] You can now send a message to another peer.\n")


    # Get destination peer's IP and port
    peer_ip = input("Enter peer IP: ").strip()
    peer_port = int(input("Enter peer port: ").strip())

    chat_with_peer(peer_ip, peer_port)

    print("[*] Message sent. Exiting...")
