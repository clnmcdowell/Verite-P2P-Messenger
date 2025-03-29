import socket
import threading

HOST = '127.0.0.1'  # Localhost
PORT = 65432        # Non-privileged port

clients = [] # List to keep track of connected clients

def handle_client(conn, addr):
    """
    Handles communication with a single connected client.
    Continuously listens for incoming messages from that client
    and logs them to the server. Cleans up on disconnect.
    """
    print(f"[+] New connection from {addr}")
    try:
        while True:
            # Receive data from the client
            data = conn.recv(1024)
            if not data:
                break  # No data means the client has disconnected
            print(f"[{addr}] {data.decode()}")
    except Exception as e:
        print(f"[-] Error: {e}")
    finally:
        print(f"[-] Connection closed from {addr}")
        conn.close()
        clients.remove(conn)

def start_server():
    """
    Starts a TCP server that listens for incoming client connections.
    Each client connection is handled in a separate thread allowing
    for concurrent messaging with multiple peers.
    """
    # Create a TCP/IP socket using IPv4
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))

        # Listen for incoming connections
        server_socket.listen()
        print(f"[*] Server started on {HOST}:{PORT}")
        print("[*] Waiting for connections...")

        # Main loop: accept and handle incoming client connections
        while True:
            conn, addr = server_socket.accept()
            clients.append(conn)
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()