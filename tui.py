
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Static, Button, Input, ListView, ListItem, Label
from textual.screen import Screen

from discovery_api import get_available_peers

class StartupScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Enter your peer ID:")
        yield Input(placeholder="peer123", id="peer_input")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        peer_id = event.value.strip()
        if peer_id:
            self.app.peer_id = peer_id
            self.app.push_screen(MainMenuScreen())

class MainMenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Verite P2P Messenger", classes="title")
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
                self.app.console.log("Checking chat requests...")
            case "quit":
                self.app.exit()

class PeerListScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Available Peers")
        peer_list = ListView(id="peer_list")
        for peer in self.app.peer_cache:
            label = Label(f"{peer['id']} at {peer['ip']}:{peer['port']}")
            peer_list.append(ListItem(label))
        yield peer_list
        yield Button("Back", id="back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()

class MessengerApp(App):
    peer_id = "unknown"
    peer_cache = []

    def on_mount(self) -> None:
        self.push_screen(StartupScreen())

if __name__ == "__main__":
    MessengerApp().run()
