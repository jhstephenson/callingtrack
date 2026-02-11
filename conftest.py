"""
Pytest configuration and shared fixtures for CallingTrack tests.
"""
import pytest
from django.contrib.auth import get_user_model
from callings.models import Unit, Organization, Position, Calling

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a regular test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def superuser(db):
    """Create a superuser for admin tests."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User'
    )


@pytest.fixture
def stake(db):
    """Create a test stake unit."""
    return Unit.objects.create(
        name='Test Stake',
        unit_type='STAKE',
        sort_order=1,
        is_active=True
    )


@pytest.fixture
def ward(db, stake):
    """Create a test ward unit under a stake."""
    return Unit.objects.create(
        name='Test Ward',
        unit_type='WARD',
        parent_unit=stake,
        sort_order=1,
        is_active=True
    )


@pytest.fixture
def organization(db, ward):
    """Create a test organization."""
    return Organization.objects.create(
        name='Relief Society',
        unit=ward,
        leader='Jane Doe',
        is_active=True
    )


@pytest.fixture
def position(db):
    """Create a test position."""
    return Position.objects.create(
        title='Relief Society President',
        description='Leads the Relief Society organization',
        is_leadership=True,
        requires_setting_apart=True,
        display_order=1,
        is_active=True
    )


@pytest.fixture
def calling(db, ward, organization, position):
    """Create a test calling."""
    return Calling.objects.create(
        unit=ward,
        organization=organization,
        position=position,
        name='Jane Smith',
        status='PENDING',
        is_active=True
    )
