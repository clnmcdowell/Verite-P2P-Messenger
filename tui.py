
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Static, Button, Input, ListView, ListItem, Label
from textual.screen import Screen

from discovery_api import get_available_peers
from chat_client import request_chat_with_peer, start_chat_session
from chat_listener import chat_requests, start_listener_thread
from registration import register_peer

class StartupScreen(Screen):
    def compose(self) -> ComposeResult:
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

                start_listener_thread(self.app.listen_port, self.app.peer_id)
                register_peer(self.app.peer_id, self.app.listen_port)

                self.app.push_screen(MainMenuScreen())
            else:
                print("[!] Invalid input. Please enter both a valid ID and port.")


    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "peer_input":
            self.app.temp_peer_id = event.value.strip()
        elif event.input.id == "port_input":
            port_str = event.value.strip()
            if port_str.isdigit():
                self.app.peer_id = self.app.temp_peer_id
                self.app.listen_port = int(port_str)
                start_listener_thread(self.app.listen_port, self.app.peer_id)
                register_peer(self.app.peer_id, self.app.listen_port)
                self.app.push_screen(MainMenuScreen())

class MainMenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Verite P2P Messenger", classes="title")
        yield Static(f"Logged in as: {self.app.peer_id} on port {self.app.listen_port}")
        yield Button("1. View available peers", id="view")
        yield Button("2. Refresh peer list", id="refresh")
        yield Button("3. View incoming chat requests", id="requests")
        yield Button("q. Quit", id="quit")

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

class PeerListScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Available Peers")
        self.peer_list = ListView(id="peer_list")
        yield self.peer_list
        yield Button("Chat with selected peer", id="chat")
        yield Button("Back", id="back")

    def on_mount(self) -> None:
        self.peer_list.clear()
        for peer in self.app.peer_cache:
            label = Label(f"{peer['id']} at {peer['ip']}:{peer['port']}")
            item = ListItem(label, id=peer["id"])
            item.data = peer
            self.peer_list.append(item)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "chat":
            selected = self.peer_list.index
            if selected is not None and selected < len(self.app.peer_cache):
                peer = self.app.peer_cache[selected]
                request_chat_with_peer(self.app.peer_id, peer["ip"], peer["port"])

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
            self.app.pop_screen()
            start_chat_session(self.conn, self.app.peer_id)
        elif event.button.id == "decline":
            self.conn.sendall("DECLINE".encode())
            self.conn.close()
            self.app.pop_screen()
        elif event.button.id == "back":
            self.app.pop_screen()

class MessengerApp(App):
    def __init__(self):
        super().__init__()
        self.peer_id = "unknown"
        self.listen_port = 5000
        self.peer_cache = []
        self.temp_peer_id = ""

    def on_mount(self) -> None:
        self.push_screen(StartupScreen())

if __name__ == "__main__":
    MessengerApp().run()
