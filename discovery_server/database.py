from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# This file contains the database connection and session management for the discovery server
DATABASE_URL = "sqlite:///./peers.db"

# SQLite database file will be created in the current directory
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()