"""
Tests for the permissions system.
"""
import pytest
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from callings.permissions import (
    user_in_group,
    is_stake_president,
    is_bishop,
    is_clerk,
    is_leadership,
    can_edit_calling,
    can_approve_calling,
    can_delete_calling,
    can_manage_units,
    STAKE_PRESIDENT_GROUP,
    BISHOP_GROUP,
    CLERK_GROUP,
    STAKE_CLERK_GROUP,
    LEADERSHIP_GROUP,
)

User = get_user_model()


@pytest.fixture
def stake_president_group(db):
    """Create stake president group."""
    return Group.objects.create(name=STAKE_PRESIDENT_GROUP)


@pytest.fixture
def bishop_group(db):
    """Create bishop group."""
    return Group.objects.create(name=BISHOP_GROUP)


@pytest.fixture
def clerk_group(db):
    """Create clerk group."""
    return Group.objects.create(name=CLERK_GROUP)


@pytest.fixture
def stake_clerk_group(db):
    """Create stake clerk group."""
    return Group.objects.create(name=STAKE_CLERK_GROUP)


@pytest.fixture
def leadership_group(db):
    """Create leadership group."""
    return Group.objects.create(name=LEADERSHIP_GROUP)


@pytest.fixture
def regular_user(db):
    """Create a regular user with no groups."""
    return User.objects.create_user(
        username='regular',
        email='regular@example.com',
        password='pass123'
    )


@pytest.fixture
def stake_president_user(db, stake_president_group):
    """Create a user in stake president group."""
    user = User.objects.create_user(
        username='stake_pres',
        email='stakepres@example.com',
        password='pass123'
    )
    user.groups.add(stake_president_group)
    return user


@pytest.fixture
def bishop_user(db, bishop_group):
    """Create a user in bishop group."""
    user = User.objects.create_user(
        username='bishop',
        email='bishop@example.com',
        password='pass123'
    )
    user.groups.add(bishop_group)
    return user


@pytest.fixture
def clerk_user(db, clerk_group):
    """Create a user in clerk group."""
    user = User.objects.create_user(
        username='clerk',
        email='clerk@example.com',
        password='pass123'
    )
    user.groups.add(clerk_group)
    return user


@pytest.mark.django_db
class TestPermissionHelpers:
    """Tests for permission helper functions."""
    
    def test_user_in_group(self, regular_user, bishop_group):
        """Test user_in_group function."""
        assert user_in_group(regular_user, BISHOP_GROUP) is False
        regular_user.groups.add(bishop_group)
        assert user_in_group(regular_user, BISHOP_GROUP) is True
        
    def test_is_stake_president_superuser(self, superuser):
        """Test superuser is always stake president."""
        assert is_stake_president(superuser) is True
        
    def test_is_stake_president_with_group(self, stake_president_user):
        """Test user with stake president group."""
        assert is_stake_president(stake_president_user) is True
        
    def test_is_stake_president_regular_user(self, regular_user):
        """Test regular user is not stake president."""
        assert is_stake_president(regular_user) is False
        
    def test_is_bishop_superuser(self, superuser):
        """Test superuser is always bishop."""
        assert is_bishop(superuser) is True
        
    def test_is_bishop_with_group(self, bishop_user):
        """Test user with bishop group."""
        assert is_bishop(bishop_user) is True
        
    def test_is_bishop_regular_user(self, regular_user):
        """Test regular user is not bishop."""
        assert is_bishop(regular_user) is False
        
    def test_is_clerk_with_group(self, clerk_user):
        """Test user with clerk group."""
        assert is_clerk(clerk_user) is True
        
    def test_is_clerk_with_stake_clerk_group(self, regular_user, stake_clerk_group):
        """Test user with stake clerk group is also clerk."""
        regular_user.groups.add(stake_clerk_group)
        assert is_clerk(regular_user) is True
        
    def test_is_leadership_stake_president(self, stake_president_user):
        """Test stake president is leadership."""
        assert is_leadership(stake_president_user) is True
        
    def test_is_leadership_bishop(self, bishop_user):
        """Test bishop is leadership."""
        assert is_leadership(bishop_user) is True
        
    def test_is_leadership_with_group(self, regular_user, leadership_group):
        """Test user with leadership group."""
        regular_user.groups.add(leadership_group)
        assert is_leadership(regular_user) is True
        
    def test_is_leadership_regular_user(self, regular_user):
        """Test regular user is not leadership."""
        assert is_leadership(regular_user) is False


@pytest.mark.django_db
class TestCallingPermissions:
    """Tests for calling-specific permissions."""
    
    def test_can_edit_calling_leadership(self, stake_president_user):
        """Test leadership can edit callings."""
        assert can_edit_calling(stake_president_user) is True
        
    def test_can_edit_calling_clerk(self, clerk_user):
        """Test clerks can edit callings."""
        assert can_edit_calling(clerk_user) is True
        
    def test_can_edit_calling_regular_user(self, regular_user):
        """Test regular users cannot edit callings."""
        assert can_edit_calling(regular_user) is False
        
    def test_can_approve_calling_stake_president(self, stake_president_user):
        """Test stake president can approve callings."""
        assert can_approve_calling(stake_president_user) is True
        
    def test_can_approve_calling_bishop(self, bishop_user):
        """Test bishop can approve callings."""
        assert can_approve_calling(bishop_user) is True
        
    def test_can_approve_calling_clerk(self, clerk_user):
        """Test clerks cannot approve callings."""
        assert can_approve_calling(clerk_user) is False
        
    def test_can_delete_calling_superuser(self, superuser):
        """Test superuser can delete callings."""
        assert can_delete_calling(superuser) is True
        
    def test_can_delete_calling_stake_president(self, stake_president_user):
        """Test stake president can delete callings."""
        assert can_delete_calling(stake_president_user) is True
        
    def test_can_delete_calling_bishop(self, bishop_user):
        """Test bishop cannot delete callings."""
        assert can_delete_calling(bishop_user) is False
        
    def test_can_manage_units_stake_president(self, stake_president_user):
        """Test stake president can manage units."""
        assert can_manage_units(stake_president_user) is True
        
    def test_can_manage_units_clerk(self, clerk_user):
        """Test clerks can manage units."""
        assert can_manage_units(clerk_user) is True
        
    def test_can_manage_units_bishop(self, bishop_user):
        """Test bishops cannot manage units."""
        assert can_manage_units(bishop_user) is False
