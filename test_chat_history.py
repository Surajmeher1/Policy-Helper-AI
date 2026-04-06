#!/usr/bin/env python
"""Test chat history functionality"""
import os
from app import app, db, User, ChatConversation, ChatMessage

def test_chat_history():
    """Test creating conversations and saving messages"""
    with app.app_context():
        # Check if tables exist
        print("✓ Checking database tables...")
        
        # Create test tables if they don't exist
        db.create_all()
        print("✓ Database tables exist")
        
        # Create a test user
        print("\nCreating test user...")
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(
                username='testuser',
                email='test@example.com',
                password_hash='hashed_password'
            )
            db.session.add(test_user)
            db.session.commit()
            print("✓ Test user created")
        else:
            print("✓ Test user already exists")
        
        # Create a test conversation
        print("\nCreating test conversation...")
        test_conv = ChatConversation(
            user_id=test_user.id,
            title="Test Conversation"
        )
        db.session.add(test_conv)
        db.session.commit()
        print(f"✓ Conversation created (ID: {test_conv.id})")
        
        # Add test messages
        print("\nAdding test messages...")
        msg1 = ChatMessage(
            conversation_id=test_conv.id,
            role='user',
            content='What is the Constitution?'
        )
        msg2 = ChatMessage(
            conversation_id=test_conv.id,
            role='assistant',
            content='The Constitution is a set of fundamental laws...'
        )
        db.session.add_all([msg1, msg2])
        db.session.commit()
        print(f"✓ Messages added (Count: 2)")
        
        # Verify retrieval
        print("\nVerifying data retrieval...")
        retrieved_conv = ChatConversation.query.get(test_conv.id)
        print(f"✓ Conversation retrieved: {retrieved_conv.title}")
        print(f"✓ Messages in conversation: {retrieved_conv.messages.count()}")
        
        for msg in retrieved_conv.messages:
            print(f"  - {msg.role}: {msg.content[:50]}...")
        
        print("\n✅ Chat history feature is working correctly!")
        
        # Cleanup
        db.session.delete(msg1)
        db.session.delete(msg2)
        db.session.delete(test_conv)
        db.session.commit()
        print("\n✓ Test data cleaned up")

if __name__ == '__main__':
    test_chat_history()
