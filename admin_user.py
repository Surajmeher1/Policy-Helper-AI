#!/usr/bin/env python3
"""
Find admin users and optionally reset their password.
Usage:
    python admin_user.py list          # List all admin users
    python admin_user.py reset <new_password>  # Reset first admin password
"""

import sys
from app import app, db, User
from werkzeug.security import generate_password_hash

def list_admins():
    """List all admin users."""
    with app.app_context():
        admins = User.query.filter_by(is_admin=True).all()
        
        if not admins:
            print("❌ No admin users found")
            return False
        
        print("✅ Admin Users Found:\n")
        for user in admins:
            print(f"  ID: {user.id}")
            print(f"  Username: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  Is Admin: {user.is_admin}")
            print()
        
        return True

def reset_password(new_password):
    """Reset the first admin user's password."""
    with app.app_context():
        admin = User.query.filter_by(is_admin=True).first()
        
        if not admin:
            print("❌ No admin user found")
            return False
        
        if len(new_password) < 6:
            print("❌ Password must be at least 6 characters")
            return False
        
        try:
            admin.password_hash = generate_password_hash(new_password)
            db.session.commit()
            print(f"✅ Password reset successfully!")
            print(f"   Username: {admin.username}")
            print(f"   New password: {new_password}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python admin_user.py list                    # List admin users")
        print("  python admin_user.py reset <new_password>    # Reset admin password")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'list':
        success = list_admins()
        sys.exit(0 if success else 1)
    elif command == 'reset':
        if len(sys.argv) < 3:
            print("Usage: python admin_user.py reset <new_password>")
            sys.exit(1)
        new_pass = sys.argv[2]
        success = reset_password(new_pass)
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
