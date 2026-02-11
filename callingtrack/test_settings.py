"""
Test-specific Django settings.
Overrides production settings to use SQLite and faster settings for testing.
"""
from callingtrack.settings import *

# Use SQLite for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable migrations for faster tests
# Note: pytest-django handles this with --reuse-db flag

# Don't send real emails during tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
