from fastapi import FastAPI, Request, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from . import models
from .database import SessionLocal, engine
from .models import Peer

# Create the database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define Pydantic request model for registering a peer
class RegisterRequest(BaseModel):
    id: str 
    port: int

@app.post("/register")
def register_peer(request: RegisterRequest, fastapi_request: Request, db: Session = Depends(get_db)):
    """
    Register a peer with the server. The peer's IP address and port are recorded.
    """
    # Get the IP address of the peer from the request
    ip = fastapi_request.client.host

    # Check if the peer already exists in the database
    peer = db.query(Peer).filter(Peer.id == request.id).first()

    # If the peer exists update its IP address and last seen time
    # If it doesn't exist create a new entry
    if peer:
        peer.ip = ip
        peer.port = request.port
        peer.last_seen = datetime.now(timezone.utc)
    else:
        peer = Peer(
            id=request.id,
            ip=ip,
            port=request.port,
            last_seen=datetime.now(timezone.utc)
        )
        db.add(peer)

    db.commit()
    return {"message": "Peer registered", "ip": ip, "port": request.port}

