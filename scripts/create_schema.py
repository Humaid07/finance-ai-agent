"""
Creates all database tables from SQLAlchemy models.
Run this before seed_data.py.

Usage:
    cd backend
    python ../scripts/create_schema.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from shared_code.database import get_engine
from shared_code.models import Base

def main():
    print("Creating database schema...")
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("[OK] Schema created successfully.")

if __name__ == "__main__":
    main()
