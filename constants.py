"""
Constants for the Windsurf Project.
This file contains all global constants used throughout the application.
"""
from typing import List

# JWT Authentication constants
ACCESS_TOKEN_EXPIRY_MINUTES: int = 60  # 1 hour
REFRESH_TOKEN_EXPIRY_MINUTES: int = 10080  # 7 days (60 * 24 * 7)

# Admin configuration
ALLOWED_ADMIN_EMAILS: List[str] = [
    'admin@windsurf.com',
    'superadmin@windsurf.com',
    'support@windsurf.com'
]

# Add more constants below as needed