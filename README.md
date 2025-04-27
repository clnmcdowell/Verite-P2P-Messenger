# Verite P2P Messenger

This project is a simple peer-to-peer messaging system with a centralized discovery server using FastAPI and SQLite. Peers can register with the server, discover other active peers, and initiate direct chat sessions with them.

## Features

- FastAPI-based **discovery server** for peer registration and lookup.
- Python-based **peer client** that:
  - Registers with the server
  - Sends automatic heartbeat updates to stay discoverable
  - Fetches online peers
  - Accepts or initiates chat sessions via TCP sockets
- Uses SQLite for storing peer info and last-seen timestamps.
- Multi-threaded design for handling chat and incoming connections concurrently.

---

## Project Structure

| File                            | Purpose                                                               |
|---------------------------------|-----------------------------------------------------------------------|
| `verite_shell.py`               | Verite Shell: CLI-based peer application that chats with other peers                |
| `verite_console.py`             | Verite Console: Textual-based TUI client for peer discovery and chat     |
| `discovery_server/main.py`      | FastAPI server with `/register`, `/heartbeat`, and `/peers` endpoints |
| `discovery_server/models.py`    | SQLAlchemy model for the `Peer` table                                 |
| `discovery_server/database.py`  | SQLite database configuration                                         |

---

## Setup and Usage

### Prerequisites

- Python 3.8 or higher  
- Git

### 1. Clone the repository and create a virtual environment

```bash
git clone <your-repo-url>
cd <your-repo-directory>
python -m venv venv
source venv/Scripts/activate   # Windows (PowerShell)
# or
# source venv/bin/activate     # macOS/Linux
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Start the discovery server

```bash
make server

```

### 4. Launch a client

```bash
make console
# or
make shell

```

### 5. Cleanup

```bash
make clean

```

## Peer Client Menu

Once started, the peer client offers a simple interactive menu:

- **View available peers** – Lists peers active in the last 60 seconds
- **Refresh peer list** – Fetches updated list from server
- **View incoming chat requests** – Accept or decline chat requests from other peers
- **Quit** – Exit the client
- The client stays active on the server via background heartbeats. No manual refresh is required to remain discoverable.

During a chat session type messages to send and `'/quit'` to leave.

---

## Notes

- Make sure each peer uses a **unique ID** and a **different port**.
- The discovery server keeps track of active peers based on periodic heartbeats (sent automatically every 30 seconds by each peer).
- You can change the discovery server's address by modifying the `DISCOVERY_URL` variable at the top of `peer_client.py`.
- This is a local prototype. For full LAN or Internet use modify IP addresses and enable port forwarding as needed.

---
