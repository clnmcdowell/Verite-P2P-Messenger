from textual import events
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Static, Button, Input, ListView, ListItem, Label
from textual.screen import Screen
from textual.timer import Timer
from discovery_api import get_available_peers
from chat_client import request_chat_with_peer, start_chat_session
from chat_listener import chat_requests, start_listener_thread
from registration import register_peer

import threading
import logging
import base64
import os

logging.basicConfig(
    filename="tui_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)


class StartupScreen(Screen):
    def compose(self) -> ComposeResult:
        with Vertical(id="registration_form"):
            with Vertical(id="form_fields"):
                yield Static("Enter your peer ID:")
                self.peer_input = Input(placeholder="peer123", id="peer_input")
                yield self.peer_input

                yield Static("Enter the port you want to listen on:")
                self.port_input = Input(placeholder="5000", id="port_input")
                yield self.port_input

            yield Button("Start", id="start")


    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            peer_id = self.peer_input.value.strip()
            port_str = self.port_input.value.strip()

            if peer_id and port_str.isdigit():
                self.app.peer_id = peer_id
                self.app.listen_port = int(port_str)
                self.app.push_screen(MainMenuScreen())
            else:
                print("[!] Invalid input. Please enter both a valid ID and port.")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "peer_input":
            # Save the temp ID and move focus to port field
            self.app.temp_peer_id = event.input.value.strip()
            self.set_focus(self.port_input)
        elif event.input.id == "port_input":
            peer_id = self.peer_input.value.strip()
            port_str = self.port_input.value.strip()
            if peer_id and port_str.isdigit():
                self.app.peer_id = peer_id
                self.app.listen_port = int(port_str)
                start_listener_thread(self.app.listen_port, self.app.peer_id)
                register_peer(self.app.peer_id, self.app.listen_port)
                self.app.push_screen(MainMenuScreen())
            else:
                print("[!] Invalid input. Please enter both a valid ID and port.")


class MainMenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Verite P2P Messenger", classes="title")
        yield Static(f"Logged in as: {self.app.peer_id} on port {self.app.listen_port}")
        yield Button("View available peers", id="view")
        yield Button("Refresh peer list", id="refresh")
        yield Button("View incoming chat requests", id="requests")
        yield Button("Quit", id="quit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "view":
                self.app.push_screen(PeerListScreen())
            case "refresh":
                self.app.peer_cache = get_available_peers(self.app.peer_id)
                self.app.push_screen(PeerListScreen())
            case "requests":
                self.app.push_screen(ChatRequestsScreen())
            case "quit":
                self.app.exit()

    def on_mount(self) -> None:
        if not hasattr(self.app, "listener_started"):
            self.app.listener_started = True
            logging.debug(f"[TUI] Starting listener on {self.app.listen_port}")
            logging.debug(f"[TUI] Starting listener on {self.app.listen_port}")
            start_listener_thread(self.app.listen_port, self.app.peer_id)
            register_peer(self.app.peer_id, self.app.listen_port)

class PeerListScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Available Peers")
        self.peer_list = ListView(id="peer_list")
        yield self.peer_list
        yield Button("Chat with selected peer", id="chat")
        yield Button("Back", id="back")

    def on_mount(self) -> None:
        self.peer_list.clear()
        for i, peer in enumerate(self.app.peer_cache):
            display_id = peer["id"] if peer["id"] else f"peer-{i}"
            label = Label(f"{peer['id'] or '[no id]'} at {peer['ip']}:{peer['port']}", markup=False)
            item = ListItem(label, id=display_id)
            item.data = peer
            self.peer_list.append(item)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "chat":
            selected = self.peer_list.index
            if selected is not None and selected < len(self.app.peer_cache):
                peer = self.app.peer_cache[selected]
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((peer["ip"], peer["port"]))
                    sock.sendall(f"CHAT_REQUEST:{self.app.peer_id}".encode())

                    response = sock.recv(4096).decode().strip()
                    if response == "ACCEPT":
                        self.app.push_screen(ChatScreen(sock, peer["id"], self.app.peer_id))
                    else:
                        sock.close()
                        from textual.widgets import Label
                        self.app.push_screen(MainMenuScreen())
                        self.app.call_later(lambda: print(f"[!] Chat request declined by {peer['id']}"))
                except Exception as e:
                    print(f"[!] Error initiating chat: {e}")
                    self.app.push_screen(MainMenuScreen())


class ChatRequestsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Pending Chat Requests")
        if chat_requests.empty():
            yield Static("No pending requests.")
            yield Button("Back", id="back")
        else:
            self.conn, self.peer_name, self.addr = chat_requests.get()
            yield Static(f"{self.peer_name} ({self.addr[0]}) wants to chat.")
            yield Button("Accept", id="accept")
            yield Button("Decline", id="decline")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "accept":
            self.conn.sendall("ACCEPT".encode())
            self.app.push_screen(ChatScreen(self.conn, self.peer_name, self.app.peer_id))
        elif event.button.id == "decline":
            self.conn.sendall("DECLINE".encode())
            self.conn.close()
            self.app.pop_screen()
        elif event.button.id == "back":
            self.app.pop_screen()

class ChatScreen(Screen):
    """
    A simple chat screen: history on top, input at bottom.
    """
    def __init__(self, conn, peer_name, my_id):
        super().__init__()
        self.conn = conn
        self.peer_name = peer_name
        self.my_id = my_id
        self.stop_event = threading.Event()
        self.awaiting_file_path = False

    def compose(self) -> ComposeResult:
        yield Header(f"Chat with {self.peer_name}")
        
        with Vertical(id="chat_layout"):
            self.history = ListView(id="history")
            yield VerticalScroll(self.history, id="history_container")
            
            with Vertical(id="input_area"):
                self.input = Input(placeholder="Type a message and press Enter", id="chat_input")
                yield self.input
                with Horizontal(id="chat_buttons"):
                    yield Button("Send File", id="send_file")
                    yield Button("Quit Chat", id="quit_chat")
        
        yield Footer()

    def on_mount(self) -> None:
        # start a thread to recv messages
        def receiver():
            try:
                while not self.stop_event.is_set():
                    data = self.conn.recv(4096)
                    if not data:
                        self.app.push_screen(MainMenuScreen())
                        break
                    raw = data.decode().strip()

                    # File transfer message:
                    if raw.startswith("FILE_TRANSFER:"):
                        parts = raw.split(":", 2)
                        if len(parts) == 3:
                            _, filename, encoded_data = parts
                            try:
                                file_bytes = base64.b64decode(encoded_data)
                                save_path = f"received_{filename}"

                                with open(save_path, "wb") as f:
                                    f.write(file_bytes)

                                self.app.call_from_thread(lambda: (
                                    self.history.append(
                                        ListItem(Label(f"[📁] Received file '{filename}' (saved to {save_path})", markup=False))
                                    )
                                ))
                            except Exception as e:
                                self.app.call_from_thread(lambda: (
                                    self.history.append(
                                        ListItem(Label(f"[!] Failed to save received file: {e}", markup=False))
                                    )
                                ))
                            continue  # skip normal message handling

                    # Normal chat messages:
                    prefix = f"{self.peer_name} says: "
                    content = raw[len(prefix):] if raw.startswith(prefix) else raw

                    # append peer message in cyan
                    self.app.call_from_thread(lambda: (
                        self.history.append(
                            ListItem(
                                (lambda label: (label.styles.__setattr__("color", "cyan"), label)[1])(Label(f"{self.peer_name}: {content}"))
                            )
                        )
                    ))
            except Exception:
                self.app.call_from_thread(lambda: (
                    self.history.append(ListItem(Label("[!] Connection lost", markup=False)))
                ))
            finally:
                self.stop_event.set()

        threading.Thread(target=receiver, daemon=True).start()
        self.set_focus(self.input)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        if text.lower() == "/quit":
            self.conn.close()
            self.stop_event.set()
            self.app.push_screen(MainMenuScreen())
            return
        if text.lower() == "/sendfile":
            self.awaiting_file_path = True
            self.input.placeholder = "Enter path to file..."
            self.input.value = ""
            self.set_focus(self.input)
            return

        if self.awaiting_file_path:
            import os
            import base64
            file_path = text
            if not os.path.isfile(file_path):
                self.history.append(ListItem(Label("[!] File not found.", markup=False)))
                self.input.placeholder = "Type message and hit Enter"
                self.input.value = ""
                self.awaiting_file_path = False
                self.set_focus(self.input)
                return

            try:
                with open(file_path, "rb") as f:
                    encoded_data = base64.b64encode(f.read()).decode("utf-8")
                filename = os.path.basename(file_path)
                message = f"FILE_TRANSFER:{filename}:{encoded_data}"
                self.conn.sendall(message.encode("utf-8"))
                label = Label(f"[📁] Sent file '{filename}'", markup=False)
                label.styles.color = "yellow"
                self.history.append(ListItem(label))
            except Exception as e:
                self.history.append(ListItem(Label(f"[!] Failed to send file: {e}", markup=False)))

            self.input.placeholder = "Type message and hit Enter"
            self.input.value = ""
            self.awaiting_file_path = False
            self.set_focus(self.input)
            return
        try:
            self.conn.sendall(f"{self.my_id} says: {text}".encode())
            label = Label(f"You: {text}", markup=False)
            label.styles.color = "green"
            self.history.append(ListItem(label))
        except ConnectionResetError:
            self.history.append(ListItem(Label("[!] Peer disconnected", markup=False)))
            self.stop_event.set()
        finally:
            self.input.value = ""
            self.set_focus(self.input)


    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send_file":
            self.awaiting_file_path = True
            self.input.placeholder = "Enter path to file..."
            self.input.value = ""
            self.set_focus(self.input)
        elif event.button.id == "quit_chat":
            self.conn.close()
            self.stop_event.set()
            self.app.push_screen(MainMenuScreen())

    async def on_key(self, event: events.Key) -> None:
        # press ESC to quit chat
        if event.key == "escape":
            self.conn.close()
            self.stop_event.set()
            self.app.push_screen(MainMenuScreen())


class VeriteConsole(App):
    CSS_PATH = "verite_console.tcss"

    def __init__(self):
        super().__init__()
        self.peer_id = "unknown"
        self.listen_port = 5000
        self.peer_cache = []
        self.temp_peer_id = ""
        self.chat_request_checker: Timer | None = None

    def on_mount(self) -> None:
        self.chat_request_checker = self.set_interval(1.5, self.check_chat_requests)
        self.push_screen(StartupScreen())

    def check_chat_requests(self) -> None:
        if not chat_requests.empty():
            self.push_screen(ChatRequestsScreen())


if __name__ == "__main__":
    VeriteConsole().run()
