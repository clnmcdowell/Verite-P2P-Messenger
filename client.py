import socket
import threading

HOST = '127.0.0.1'  # Localhost
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

def start_client():
    """
    Starts a TCP client that connects to the server and allows
    the user to send messages to the server.
    """
    # Create a TCP/IP socket using IPv4
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((HOST, PORT))
            print(f"[+] Connected to server at {HOST}:{PORT}")
            # Start a thread to receive messages from the server
            thread = threading.Thread(target=receive_message, args=(client_socket,), daemon=True)
            thread.start()

            # Main loop: user input -> send to server
            while True:
                message = input("Enter message: ")

                # Check for exit command
                if message.lower() == '/quit':
                    print("[*] Disconnecting...")
                    break
                try: 
                    # Send message to server as encoded bytes
                    client_socket.sendall(message.encode())
                except Exception as e:
                    print(f"[-] Error sending message: {e}")
                    break
        except Exception as e:
            print(f"[-] Error connecting to server: {e}")
        finally:
            print ("[*] Closing connection.")
            client_socket.close()