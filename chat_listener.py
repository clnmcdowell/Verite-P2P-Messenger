import socket
import threading
from queue import Queue

import logging

# Shared queue for chat requests
chat_requests = Queue()

def handle_incoming_connection(conn, addr, my_peer_id):
    """
    Handle an incoming socket connection. If it's a valid chat request, queue it.
    """
    try:
        data = conn.recv(4096).decode().strip()
        logging.debug(f"[chat_listener] got raw data from {addr}: {data!r}")
        if data.startswith("CHAT_REQUEST:"):
            requester_id = data.split(":", 1)[1]
            chat_requests.put((conn, requester_id, addr))
        else:
            conn.close()
    except Exception as e:
        print(f"[!] Error in connection from {addr}: {e}")
        conn.close()

def start_listener_thread(listen_port, my_peer_id):
    """
    Start a background thread to listen for incoming peer chat connections.
    """
    def listen_loop():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", listen_port))
        sock.listen()
        logging.debug(f"[chat_listener] Listening on 0.0.0.0:{listen_port} for CHAT_REQUESTs (peer_id={my_peer_id})")

        while True:
            conn, addr = sock.accept()
            threading.Thread(target=handle_incoming_connection, args=(conn, addr, my_peer_id), daemon=True).start()

    threading.Thread(target=listen_loop, daemon=True).start()
