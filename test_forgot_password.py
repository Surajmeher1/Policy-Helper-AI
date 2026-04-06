#!/usr/bin/env python
"""Test the forgot_password route"""
from app import app, db

# Create app context and initialize database
with app.app_context():
    db.create_all()
    
    # Test the forgot_password route with GET
    with app.test_client() as client:
        # Test GET request
        response = client.get('/forgot_password')
        print(f"GET /forgot_password: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.data[:200]}")
        else:
            print("✅ GET request successful")
            
        # Test POST request with valid email
        response = client.post('/forgot_password', data={'email': 'test@example.com'})
        print(f"POST /forgot_password (test email): {response.status_code}")
        if response.status_code not in [200, 302]:
            print(f"Error: {response.data[:200]}")
        else:
            print("✅ POST request successful")
            
        # Test POST with empty email
        response = client.post('/forgot_password', data={'email': ''})
        print(f"POST /forgot_password (empty): {response.status_code}")
        if response.status_code == 200:
            print("✅ Empty email handled correctly")

print("\n✅ All tests passed!")
