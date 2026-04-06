#!/usr/bin/env python3
"""
Initialize the database tables for the chat history feature.
Run this once after deploying the chat history feature.

Usage:
    python init_db.py
"""

import sys
from app import app, db

def init_database():
    """Create all database tables."""
    print("🔄 Initializing database...")
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            print("✓ User table")
            print("✓ Activity table")
            print("✓ ChatConversation table")
            print("✓ ChatMessage table")
            print("\n✨ You can now use the chat history feature!")
            return 0
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return 1

if __name__ == '__main__':
    exit_code = init_database()
    sys.exit(exit_code)
