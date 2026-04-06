#!/usr/bin/env python
"""Test forgot_password route with detailed error output"""
from app import app, db, User
import traceback

with app.app_context():
    db.create_all()
    
    with app.test_client() as client:
        # Test with an actual registered user
        print("Testing forgot_password route...\n")
        
        # First, let's check what users exist
        users = User.query.all()
        print(f"📊 Users in database: {len(users)}")
        for u in users:
            print(f"   - {u.username} ({u.email})")
        
        if not users:
            print("\n❌ No users registered! Creating test user...\n")
            from werkzeug.security import generate_password_hash
            test_user = User(
                username="testuser",
                email="testuser@example.com",
                password_hash=generate_password_hash("Test123!"),
                is_admin=False
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"✅ Test user created: testuser@example.com\n")
        
        # Now test the forgot_password form
        print("Testing form submission...\n")
        test_email = users[0].email if users else "testuser@example.com"
        
        try:
            response = client.post('/forgot_password', data={'email': test_email})
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            if response.status_code != 302:  # 302 is redirect (success)
                print(f"\n❌ Error response:\n{response.data.decode()[:500]}")
            else:
                print("✅ Form submission successful (redirect)")
        except Exception as e:
            print(f"\n🔴 EXCEPTION during form submission:")
            print(f"{type(e).__name__}: {e}")
            traceback.print_exc()
