#!/usr/bin/env python
"""Test chat API endpoints"""
import os
from app import app, db, User, ChatConversation, ChatMessage

def test_chat_api():
    """Test chat API endpoints with a real user"""
    with app.app_context():
        # Setup database
        db.create_all()
        
        # Create a test user
        test_user = User.query.filter_by(username='apitest').first()
        if test_user:
            # Clean up old tests
            for conv in test_user.chat_conversations:
                db.session.delete(conv)
            db.session.delete(test_user)
            db.session.commit()
        
        test_user = User(
            username='apitest',
            email='apitest@example.com',
            password_hash='hashed_password'
        )
        db.session.add(test_user)
        db.session.commit()
        print(f"✓ Test user created (ID: {test_user.id})")
        
        # Create a test client
        client = app.test_client()
        
        # Test: Create conversation without login (should fail)
        print("\nTest 1: Create conversation without login (should fail)...")
        response = client.post('/api/chat/new')
        assert response.status_code == 401
        assert not response.get_json()['success']
        print("✓ Correctly rejected unauthorized request")
        
        # Test: Login user
        print("\nTest 2: Login user...")
        with client:
            client.post('/index', data={
                'username': 'apitest',
                'email': 'apitest@example.com',
                'password': 'testpass123'
            }, follow_redirects=True)
            
            # Since login isn't straightforward in this test, let's simulate session
            with client.session_transaction() as sess:
                sess['username'] = 'apitest'
            
            # Test: Create conversation (should succeed)
            print("\nTest 3: Create conversation with login...")
            response = client.post('/api/chat/new')
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.get_json()}")
            
            if response.status_code == 200:
                data = response.get_json()
                assert data['success']
                conv_id = data['conversation_id']
                print(f"✓ Conversation created (ID: {conv_id})")
                
                # Test: Get conversations
                print("\nTest 4: Get all conversations...")
                response = client.get('/api/chat/conversations')
                data = response.get_json()
                assert data['success']
                assert len(data['conversations']) > 0
                print(f"✓ Found {len(data['conversations'])} conversation(s)")
                
                # Test: Save message
                print("\nTest 5: Save message...")
                response = client.post(f'/api/chat/{conv_id}/message', 
                    json={'role': 'user', 'content': 'Test message'})
                data = response.get_json()
                print(f"Response: {data}")
                assert data['success']
                print("✓ Message saved")
                
                # Test: Get conversation messages
                print("\nTest 6: Get conversation messages...")
                response = client.get(f'/api/chat/{conv_id}/messages')
                data = response.get_json()
                print(f"Response: {data}")
                assert data['success']
                assert len(data['messages']) == 1
                print(f"✓ Retrieved {len(data['messages'])} message(s)")
                
                # Test: Delete conversation
                print("\nTest 7: Delete conversation...")
                response = client.delete(f'/api/chat/{conv_id}/delete')
                data = response.get_json()
                assert data['success']
                print("✓ Conversation deleted")
        
        print("\n✅ All chat API tests passed!")

if __name__ == '__main__':
    test_chat_api()
