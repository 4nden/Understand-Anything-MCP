import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# By default use sqlite if no DATABASE_URL is set
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./licenses.db")

# If using Postgres from Supabase, avoid check_same_thread
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class LicenseKey(Base):
    __tablename__ = "license_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    tier = Column(String, default="Free") # Free, Pro, Team
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    email = Column(String, index=True, nullable=True)
    stripe_session_id = Column(String, unique=True, index=True, nullable=True)

Base.metadata.create_all(bind=engine)
