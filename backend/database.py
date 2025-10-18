from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment variables
# Using SQLite as default for development (no setup required)
# For production, set DATABASE_URL in .env to postgresql+psycopg://user:pass@host:5432/dbname
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./hacknu.db"  # SQLite file-based database for easy development
)

# Create SQLAlchemy engine
# SQLite-specific config for thread safety
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
