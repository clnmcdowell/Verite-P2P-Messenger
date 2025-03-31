import requests
import socket
import threading
import time
from queue import Queue

DISCOVERY_URL = "http://127.0.0.1:8000"  # Replace with your discovery server URL or LAN IP
PEER_ID = input("Enter your peer ID: ")
LISTEN_PORT = int(input("Enter the port to listen on: "))

chat_requests = Queue() # Queue to hold incoming chat requests
peer_cache = [] # Cache to store available peers


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
    print(f"\n[+] Incoming connection from {addr}")

    try:
        # Receive data from the peer
        data = conn.recv(4096).decode().strip()

        if not data:
            print("[!] No data received. Closing connection.")
            conn.close()
            return
        
        # Queue chat requests for the main thread to handle
        if data.startswith("CHAT_REQUEST:"):
            peer_name = data.split(":", 1)[1]
            chat_requests.put((conn, peer_name, addr))
        else:
            print(f"[←] {data}")
            conn.close()
    except Exception as e:
        print(f"[!] Error handling connection from {addr}: {e}")

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

def request_chat_with_peer(peer_ip, peer_port):
    """"
    Request to chat with another peer.
    """
    print(f"[*] Requesting chat with {peer_ip}:{peer_port}...")

    # Check if the peer is reachable
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((peer_ip, peer_port))
            s.sendall(f"CHAT_REQUEST:{PEER_ID}".encode())

            # Wait for the peer's response
            response = s.recv(4096).decode().strip()
            if response == "ACCEPT":
                print("[✓] Chat accepted. Starting session.")
                threading.Thread(target=receive_messages, args=(s,), daemon=True).start()
                while True:
                    message = input("> ")
                    if message.strip().lower() == "/quit":
                        s.close()
                        print("[*] Chat session ended.")
                        break
                    tagged_message = f"{PEER_ID} says: {message}"
                    s.sendall(tagged_message.encode())
            else:
                print("[X] Chat declined.")
    except Exception as e:
        print(f"[!] Failed to request chat: {e}")

def start_chat_loop(conn):
    """
    Start the chat loop for sending and receiving messages.
    """
    print("[*] Chat session started. Type '/quit' to exit.")
    threading.Thread(target=receive_messages, args=(conn,), daemon=True).start()

    while True:
        message = input("> ")
        if message.strip().lower() == "/quit":
            conn.close()
            break
        tagged_message = f"{PEER_ID} says: {message}"
        conn.sendall(tagged_message.encode())

def handle_pending_requests():
    """
    Handle pending chat requests from other peers.
    """
    print("[*] Checking for incoming chat requests...")
    while not chat_requests.empty():
        # Get the next chat request from the queue and process it
        conn, peer_name, addr = chat_requests.get()
        response = input(f"\n[?] {peer_name} wants to chat. Accept? (y/n): ").strip().lower()
        if response == "y":
            conn.sendall("ACCEPT".encode())
            print("[✓] Chat started.")
            start_chat_loop(conn)
        else:
            conn.sendall("DECLINE".encode())
            conn.close()

def refresh_peer_list():
    """
    Refresh the cached list of available peers.
    """
    global peer_cache
    peer_cache = get_available_peers()

def display_peer_list():
    """
    Display the list of available peers.
    """
    if not peer_cache:
        return

    # Print the list of available peers
    print(f"\n=== Available Peers ({len(peer_cache)}) ===")
    for idx, peer in enumerate(peer_cache, start=1):
        print(f"{idx}. {peer['id']} at {peer['ip']}:{peer['port']}")

def handle_peer_selection():
    if not peer_cache:
        print("[!] No peers available. Try refreshing first.")
        return

    selection = input("Enter peer number to chat: ").strip()
    if not selection.isdigit():
        print("[!] Invalid input.")
        return

    index = int(selection)
    if 1 <= index <= len(peer_cache):
        peer = peer_cache[index - 1]
        request_chat_with_peer(peer["ip"], peer["port"])
    else:
        print("[!] Invalid peer number.")


if __name__ == "__main__":
    register_with_discovery_server()
    start_listener()

    print(f"\n[✓] Peer '{PEER_ID}' is registered and listening on port {LISTEN_PORT}.")
    print("[*] You can now send a message to another peer.\n")

    # Main loop for the client
    while True:
        print("\n=== Main Menu ===")
        print("1. View available peers")
        print("2. Refresh peer list")
        print("3. View incoming chat requests", end="")
        if not chat_requests.empty():
            print(f" ({chat_requests.qsize()} pending)")
        else:
            print()
        print("q. Quit")

        choice = input("Select an option: ").strip().lower()

        if choice == "1":
            display_peer_list()
            handle_peer_selection()
        elif choice == "2":
            refresh_peer_list()
        elif choice == "3":
            handle_pending_requests()
        elif choice == "q":
            break
        else:
            print("[!] Invalid option.")
