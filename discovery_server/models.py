from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime, timezone
from .database import Base

class Peer(Base):
    __tablename__ = "peers"

    id = Column(String, primary_key=True, index=True)
    ip = Column(String)
    port = Column(Integer)
    last_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))