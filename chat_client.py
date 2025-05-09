import socket
import threading
import base64
import os

def receive_messages(sock):
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                print("\n[!] Connection closed by peer.")
                break
            print(f"\n[←] {data.decode().strip()}\n> ", end="")
    except Exception as e:
        print(f"[!] Error receiving message: {e}")

def send_file(sock):
    file_path = input("Enter the path of the file to send: ").strip()
    if not os.path.isfile(file_path):
        print("[!] File not found.")
        return
    try:
        with open(file_path, "rb") as f:
            encoded_data = base64.b64encode(f.read()).decode("utf-8")
        filename = os.path.basename(file_path)
        message = f"FILE_TRANSFER:{filename}:{encoded_data}"
        sock.sendall(message.encode("utf-8"))
        print(f"[✓] Sent file '{filename}'")
    except Exception as e:
        print(f"[!] Failed to send file: {e}")

def start_chat_session(sock, peer_id):
    """
    Begin a chat session, handling both sending and receiving messages gracefully.
    """
    print("[*] Chat session started. Type '/quit' to exit.")
    # Spawn the receiver thread
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    try:
        while True:
            # Read user input
            message = input("> ")
            if message.strip().lower() == "/quit":
                # User ends the chat
                sock.close()
                print("[*] Chat ended.")
                break
            elif message.strip().lower() == "/sendfile":
                # Delegate to file‐send helper
                send_file(sock)
                continue

            # Try sending the text message
            try:
                sock.sendall(f"{peer_id} says: {message}".encode())
            except ConnectionResetError:
                # Peer hung up
                print("\n[!] Peer disconnected unexpectedly. Returning to menu.")
                break

    except (KeyboardInterrupt, EOFError):
        # Handle Ctrl+C or Ctrl+D in the input loop
        sock.close()
        print("\n[*] Chat aborted. Returning to menu.")
    except Exception as e:
        # Catch‐all for any other errors
        print(f"[!] Unexpected error during chat session: {e}")


def request_chat_with_peer(peer_id, peer_ip, peer_port):
    print(f"[*] Connecting to {peer_ip}:{peer_port}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((peer_ip, peer_port))
            sock.sendall(f"CHAT_REQUEST:{peer_id}".encode())
            response = sock.recv(4096).decode().strip()
            if response == "ACCEPT":
                start_chat_session(sock, peer_id)
            else:
                print("[X] Chat declined.")
    except Exception as e:
        print(f"[!] Could not connect: {e}")
