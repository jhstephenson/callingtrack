"""
Tests for the accounts app models.
"""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Tests for the custom User model."""
    
    def test_create_user(self, user):
        """Test creating a regular user."""
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.is_staff is False
        assert user.is_superuser is False
        
    def test_create_superuser(self, superuser):
        """Test creating a superuser."""
        assert superuser.username == 'admin'
        assert superuser.email == 'admin@example.com'
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
        
    def test_user_str_representation(self, user):
        """Test string representation returns full name."""
        assert str(user) == 'Test User'
        
    def test_user_str_falls_back_to_username(self):
        """Test string representation falls back to username if no name."""
        user = User.objects.create_user(
            username='johndoe',
            email='john@example.com',
            password='pass123'
        )
        assert str(user) == 'johndoe'
        
    def test_email_is_unique(self, user):
        """Test that email addresses must be unique."""
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='anotheruser',
                email='test@example.com',  # Same email as user fixture
                password='pass123'
            )
            
    def test_user_password_is_hashed(self, user):
        """Test that passwords are properly hashed."""
        assert user.password != 'testpass123'
        assert user.check_password('testpass123') is True
        
    def test_phone_field_optional(self):
        """Test that phone field is optional."""
        user = User.objects.create_user(
            username='nophone',
            email='nophone@example.com',
            password='pass123'
        )
        assert user.phone == ''
        
    def test_phone_field_can_be_set(self):
        """Test that phone field can be set."""
        user = User.objects.create_user(
            username='withphone',
            email='withphone@example.com',
            password='pass123',
            phone='555-1234'
        )
        assert user.phone == '555-1234'

