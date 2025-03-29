import socket
import threading

HOST = '127.0.0.1'  # Localhost
PORT = 65432        # Non-privileged port

clients = [] # List to keep track of connected clients

#TODO def handle_client(conn, addr):

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