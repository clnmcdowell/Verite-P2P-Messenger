import socket
import threading

HOST = '127.0.0.1'  # Localhost`
PORT = 65432        # Non-privileged port

def receive_message(sock):
    """
    Continuously listens for incoming messages from the server
    and prints them to the console.
    """
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break  # No data means the server has disconnected
            print(f"[Server]: {data.decode()}")
        except Exception as e:
            print(f"[-] Error receiving message: {e}")
            break