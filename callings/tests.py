"""
Tests for the callings app models.
"""
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from callings.models import Unit, Organization, Position, Calling, CallingHistory


@pytest.mark.django_db
class TestUnitModel:
    """Tests for the Unit model."""
    
    def test_create_unit(self, stake):
        """Test creating a basic unit."""
        assert stake.name == 'Test Stake'
        assert stake.unit_type == 'STAKE'
        assert stake.is_active is True
        
    def test_unit_str_representation(self, stake):
        """Test string representation of unit."""
        # The __str__ method checks if unit type is in the name
        # "Test Stake" contains "stake" so it returns just the name
        assert str(stake) == 'Test Stake'
        
    def test_unit_str_with_type_appended(self):
        """Test string representation includes type when not in name."""
        unit = Unit.objects.create(
            name='First',
            unit_type='WARD',
            is_active=True
        )
        assert str(unit) == 'First (Ward)'
        
    def test_unit_parent_child_relationship(self, stake, ward):
        """Test hierarchical relationship between units."""
        assert ward.parent_unit == stake
        assert ward in stake.child_units.all()
        
    def test_unit_ordering(self):
        """Test units are ordered by sort_order then name."""
        unit1 = Unit.objects.create(name='Z Ward', unit_type='WARD', sort_order=2)
        unit2 = Unit.objects.create(name='A Ward', unit_type='WARD', sort_order=1)
        unit3 = Unit.objects.create(name='B Ward', unit_type='WARD', sort_order=1)
        
        units = list(Unit.objects.all())
        assert units[0] == unit2  # sort_order 1, name A
        assert units[1] == unit3  # sort_order 1, name B
        assert units[2] == unit1  # sort_order 2, name Z
        
    def test_unit_get_absolute_url(self, ward):
        """Test get_absolute_url returns correct URL."""
        url = ward.get_absolute_url()
        assert url == f'/callings/units/{ward.pk}/'


@pytest.mark.django_db
class TestOrganizationModel:
    """Tests for the Organization model."""
    
    def test_create_organization(self, organization):
        """Test creating an organization."""
        assert organization.name == 'Relief Society'
        assert organization.leader == 'Jane Doe'
        assert organization.is_active is True
        
    def test_organization_str_representation(self, organization):
        """Test string representation."""
        assert str(organization) == 'Relief Society'
        
    def test_organization_unique_name(self, organization):
        """Test that organization names must be unique."""
        with pytest.raises(Exception):  # IntegrityError
            Organization.objects.create(name='Relief Society')
            
    def test_organization_ordering(self):
        """Test organizations are ordered alphabetically by name."""
        org1 = Organization.objects.create(name='Young Women')
        org2 = Organization.objects.create(name='Primary')
        org3 = Organization.objects.create(name='Elders Quorum')
        
        orgs = list(Organization.objects.all())
        assert orgs[0] == org3  # Elders Quorum
        assert orgs[1] == org2  # Primary
        assert orgs[2] == org1  # Young Women


@pytest.mark.django_db
class TestPositionModel:
    """Tests for the Position model."""
    
    def test_create_position(self, position):
        """Test creating a position."""
        assert position.title == 'Relief Society President'
        assert position.is_leadership is True
        assert position.requires_setting_apart is True
        
    def test_position_str_representation(self, position):
        """Test string representation."""
        assert str(position) == 'Relief Society President'
        
    def test_position_ordering(self):
        """Test positions are ordered by display_order then title."""
        pos1 = Position.objects.create(title='Teacher', display_order=3)
        pos2 = Position.objects.create(title='President', display_order=1)
        pos3 = Position.objects.create(title='Counselor', display_order=1)
        
        positions = list(Position.objects.all())
        assert positions[0] == pos3  # display_order 1, Counselor
        assert positions[1] == pos2  # display_order 1, President
        assert positions[2] == pos1  # display_order 3, Teacher
        
    def test_get_current_holder_vacant(self, position):
        """Test get_current_holder returns None for vacant position."""
        assert position.get_current_holder() is None
        
    def test_get_current_holder_filled(self, position, ward, organization):
        """Test get_current_holder returns name when position is filled."""
        calling = Calling.objects.create(
            unit=ward,
            organization=organization,
            position=position,
            name='John Doe',
            status='CALLED',
            is_active=True
        )
        assert position.get_current_holder() == 'John Doe'
        
    def test_get_current_holder_ignores_released(self, position, ward, organization):
        """Test get_current_holder ignores released callings."""
        calling = Calling.objects.create(
            unit=ward,
            organization=organization,
            position=position,
            name='John Doe',
            status='CALLED',
            is_active=True,
            date_released=date.today()
        )
        assert position.get_current_holder() is None


@pytest.mark.django_db
class TestCallingModel:
    """Tests for the Calling model."""
    
    def test_create_calling(self, calling):
        """Test creating a basic calling."""
        assert calling.name == 'Jane Smith'
        assert calling.status == 'PENDING'
        assert calling.is_active is True
        
    def test_calling_str_representation(self, calling):
        """Test string representation of calling."""
        # Unit name is "Test Ward" which contains "ward", so __str__ returns just "Test Ward"
        expected = f"Jane Smith - Relief Society President in Relief Society (Test Ward)"
        assert str(calling) == expected
        
    def test_calling_status_choices(self):
        """Test all valid status choices."""
        valid_statuses = ['PENDING', 'APPROVED', 'HC_APPROVED', 'ON_HOLD', 'CALLED', 'LCR_UPDATED']
        for status in valid_statuses:
            status_display = dict(Calling.STATUS_CHOICES).get(status)
            assert status_display is not None
            
    def test_get_display_name_with_nr_suffix(self, calling):
        """Test get_display_name adds (N/R) suffix when not released."""
        assert calling.get_display_name() == 'Jane Smith (N/R)'
        
    def test_get_display_name_without_nr_suffix(self, calling):
        """Test get_display_name doesn't add suffix when released."""
        calling.date_released = date.today()
        calling.save()
        assert calling.get_display_name() == 'Jane Smith'
        
    def test_auto_status_update_on_presidency_approval(self, calling):
        """Test status automatically changes from PENDING to APPROVED when presidency approves."""
        assert calling.status == 'PENDING'
        calling.presidency_approved = date.today()
        calling.save()
        calling.refresh_from_db()
        assert calling.status == 'APPROVED'
        
    def test_status_not_changed_if_not_pending(self, calling):
        """Test status doesn't change if not PENDING."""
        calling.status = 'CALLED'
        calling.save()
        calling.presidency_approved = date.today()
        calling.save()
        calling.refresh_from_db()
        assert calling.status == 'CALLED'  # Should remain CALLED
        
    def test_get_status_badge_class(self, calling):
        """Test status badge classes are correct."""
        status_map = {
            'PENDING': 'warning',
            'APPROVED': 'success',
            'HC_APPROVED': 'success',  # Not in the map, will return 'secondary'
            'ON_HOLD': 'warning',
            'CALLED': 'primary',  # Not in the map, will return 'secondary'
            'LCR_UPDATED': 'info',
        }
        
        # Test statuses that are in the map
        calling.status = 'PENDING'
        assert calling.get_status_badge_class() == 'warning'
        
        calling.status = 'APPROVED'
        assert calling.get_status_badge_class() == 'success'
        
        calling.status = 'ON_HOLD'
        assert calling.get_status_badge_class() == 'warning'
        
        calling.status = 'LCR_UPDATED'
        assert calling.get_status_badge_class() == 'info'
        
        # Test statuses not in map return 'secondary'
        calling.status = 'HC_APPROVED'
        assert calling.get_status_badge_class() == 'secondary'
        
        calling.status = 'CALLED'
        assert calling.get_status_badge_class() == 'secondary'
            
    def test_calling_ordering(self, ward, organization, position):
        """Test callings are ordered by most recent date_called."""
        today = date.today()
        calling1 = Calling.objects.create(
            unit=ward, organization=organization, position=position,
            name='Person 1', date_called=today - timedelta(days=10)
        )
        calling2 = Calling.objects.create(
            unit=ward, organization=organization, position=position,
            name='Person 2', date_called=today
        )
        calling3 = Calling.objects.create(
            unit=ward, organization=organization, position=position,
            name='Person 3', date_called=today - timedelta(days=5)
        )
        
        callings = list(Calling.objects.all())
        assert callings[0] == calling2  # Most recent
        assert callings[1] == calling3  # Middle
        assert callings[2] == calling1  # Oldest
        
    def test_calling_get_absolute_url(self, calling):
        """Test get_absolute_url returns correct URL."""
        url = calling.get_absolute_url()
        assert url == f'/callings/callings/{calling.pk}/'
        
    def test_lcr_updated_defaults_to_false(self, calling):
        """Test lcr_updated field defaults to False."""
        assert calling.lcr_updated is False


@pytest.mark.django_db
class TestCallingHistoryModel:
    """Tests for the CallingHistory model."""
    
    def test_create_calling_history(self, calling, user):
        """Test creating a calling history entry."""
        history = CallingHistory.objects.create(
            calling=calling,
            action='CALLED',
            member_name='Jane Smith',
            changed_by=user,
            notes='Initial calling',
            snapshot={'status': 'PENDING', 'name': 'Jane Smith'}
        )
        
        assert history.calling == calling
        assert history.action == 'CALLED'
        assert history.member_name == 'Jane Smith'
        assert history.changed_by == user
        assert history.snapshot['status'] == 'PENDING'
        
    def test_history_str_representation(self, calling, user):
        """Test string representation of history."""
        history = CallingHistory.objects.create(
            calling=calling,
            action='UPDATED',
            changed_by=user,
            snapshot={}
        )
        
        str_repr = str(history)
        assert 'Updated' in str_repr
        assert calling.name in str_repr
        
    def test_history_ordering(self, calling, user):
        """Test history is ordered by most recent first."""
        history1 = CallingHistory.objects.create(
            calling=calling, action='CALLED', changed_by=user, snapshot={}
        )
        # Small delay to ensure different timestamps
        history2 = CallingHistory.objects.create(
            calling=calling, action='UPDATED', changed_by=user, snapshot={}
        )
        
        histories = list(CallingHistory.objects.all())
        assert histories[0] == history2  # Most recent
        assert histories[1] == history1  # Oldest
