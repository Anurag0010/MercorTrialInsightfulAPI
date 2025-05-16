"""
Constants for the Windsurf Project.
This file contains all global constants used throughout the application.
"""
from typing import List

# JWT Authentication constants
ACCESS_TOKEN_EXPIRY_MINUTES: int = 60  # 1 hour
REFRESH_TOKEN_EXPIRY_MINUTES: int = 24 * 60 * 7  # 7 days (60 * 24 * 7)

# Admin configuration
ALLOWED_ADMIN_EMAILS: List[str] = [
    'pranav.pieces@gmail.com',
    'an1gupta0693@gmail.com',
]

SCREENSHOT_STORAGE_CONTAINER: str = 'screenshots'

CONTAINER_NAMES = [ SCREENSHOT_STORAGE_CONTAINER ]
# Add more constants below as needed