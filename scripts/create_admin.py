#!/usr/bin/env python
import sys
import os
from typing import Optional, Union, NoReturn

# Add project root to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db
from api.models.admin import Admin
from app import create_app
from constants import ALLOWED_ADMIN_EMAILS

def create_admin(email: str, password: str) -> bool:
    """Create an admin user"""
    if email not in ALLOWED_ADMIN_EMAILS:
        print(f"Error: {email} is not in the allowed admin emails list.")
        return False
    
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        existing: Optional[Admin] = Admin.query.filter_by(email=email).first()
        if existing:
            print(f"Admin with email {email} already exists.")
            return False
        
        admin = Admin(email=email)
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        print(f"Admin created successfully with email: {email}")
        return True

def main() -> Union[int, NoReturn]:
    """Main entry point for the script"""
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    if create_admin(email, password):
        print("Admin user created successfully.")
        return 0
    else:
        print("Failed to create admin user.")
        sys.exit(1)

if __name__ == "__main__":
    main()