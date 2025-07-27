"""Database module for persisting avatar generation requests to PostgreSQL."""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Construct from individual components if DATABASE_URL not provided
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "superhero_avatars")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create base class for models
Base = declarative_base()


class AvatarRequest(Base):
    """Model for avatar generation requests."""
    __tablename__ = 'avatar_requests'
    
    request_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    superhero = Column(String(100), nullable=False)
    car = Column(String(100), nullable=False)
    color = Column(String(50), nullable=False)
    request_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    generation_time_seconds = Column(Integer, nullable=True)
    status = Column(String(20), default='pending', nullable=False)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    original_image_path = Column(String(500), nullable=True)
    generated_image_path = Column(String(500), nullable=True)
    
    # Email tracking fields
    email_requested = Column(Boolean, default=False, nullable=False)
    email_request_time = Column(DateTime, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'request_id': self.request_id,
            'name': self.name,
            'email': self.email,
            'superhero': self.superhero,
            'car': self.car,
            'color': self.color,
            'request_time': self.request_time.isoformat() if self.request_time else None,
            'generation_time_seconds': self.generation_time_seconds,
            'status': self.status,
            'error_message': self.error_message,
            'original_image_path': self.original_image_path,
            'generated_image_path': self.generated_image_path,
            'email_requested': self.email_requested,
            'email_request_time': self.email_request_time.isoformat() if self.email_request_time else None
        }


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        """Initialize database manager."""
        # Create engine with connection pooling disabled for serverless environments
        self.engine = create_engine(
            DATABASE_URL,
            poolclass=NullPool,  # Disable connection pooling
            echo=False  # Set to True for SQL debugging
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        self.create_tables()
    
    def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating tables: {e}")
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_avatar_request(
        self,
        name: str,
        email: str,
        superhero: str,
        car: str,
        color: str
    ) -> str:
        """Create a new avatar request record.
        
        Args:
            name: User's name
            email: User's email
            superhero: Selected superhero
            car: Selected car
            color: Selected color
            
        Returns:
            request_id of the created record
        """
        with self.get_session() as session:
            request = AvatarRequest(
                name=name,
                email=email,
                superhero=superhero,
                car=car,
                color=color,
                status='pending'
            )
            session.add(request)
            session.flush()  # Get the ID before commit
            return request.request_id
    
    def update_request_processing(self, request_id: str):
        """Update request status to processing.
        
        Args:
            request_id: ID of the request to update
        """
        with self.get_session() as session:
            request = session.query(AvatarRequest).filter_by(request_id=request_id).first()
            if request:
                request.status = 'processing'
    
    def update_request_completed(
        self,
        request_id: str,
        generation_time: float,
        original_image_path: str,
        generated_image_path: str
    ):
        """Update request when generation is completed.
        
        Args:
            request_id: ID of the request to update
            generation_time: Time taken to generate in seconds
            original_image_path: Path to original image
            generated_image_path: Path to generated avatar
        """
        with self.get_session() as session:
            request = session.query(AvatarRequest).filter_by(request_id=request_id).first()
            if request:
                request.status = 'completed'
                request.generation_time_seconds = int(generation_time)
                request.original_image_path = str(original_image_path)
                request.generated_image_path = str(generated_image_path)
    
    def update_request_failed(self, request_id: str, error_message: str):
        """Update request when generation fails.
        
        Args:
            request_id: ID of the request to update
            error_message: Error message describing the failure
        """
        with self.get_session() as session:
            request = session.query(AvatarRequest).filter_by(request_id=request_id).first()
            if request:
                request.status = 'failed'
                request.error_message = error_message
    
    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a request by ID.
        
        Args:
            request_id: ID of the request
            
        Returns:
            Request data as dictionary or None if not found
        """
        with self.get_session() as session:
            request = session.query(AvatarRequest).filter_by(request_id=request_id).first()
            return request.to_dict() if request else None
    
    def get_recent_requests(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Get recent requests.
        
        Args:
            limit: Maximum number of requests to return
            
        Returns:
            List of request dictionaries
        """
        with self.get_session() as session:
            requests = session.query(AvatarRequest)\
                .order_by(AvatarRequest.request_time.desc())\
                .limit(limit)\
                .all()
            return [req.to_dict() for req in requests]


# Create global database manager instance
db_manager = DatabaseManager()