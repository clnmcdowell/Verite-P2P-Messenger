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
                print("\n[!] Server disconnected.")
                break  # No data means the server has disconnected
            print(f"\n[Server]: {data.decode()}")
        except Exception as e:
            print(f"\n[-] Error receiving message: {e}")
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
            print(f"\n[+] Connected to server at {HOST}:{PORT}")
            # Start a thread to receive messages from the server
            thread = threading.Thread(target=receive_message, args=(client_socket,), daemon=True)
            thread.start()

            # Main loop: user input -> send to server
            while True:
                message = input("Enter message (or /quit to exit): ")

                # Check for exit command
                if message.lower() == '/quit':
                    print("\n[*] Disconnecting...")
                    break
                try: 
                    # Send message to server as encoded bytes
                    client_socket.sendall(message.encode())
                except Exception as e:
                    print(f"\n[-] Error sending message: {e}")
                    break
        except Exception as e:
            print(f"\n[-] Error connecting to server: {e}")
        finally:
            print ("\n[*] Closing connection.")
            client_socket.close()
            
if __name__ == "__main__":
    start_client()


