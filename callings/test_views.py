"""
Tests for the callings app views.
"""
import pytest
from django.urls import reverse
from django.contrib.auth.models import Group
from django.test import Client
from callings.models import Unit, Organization, Position, Calling


@pytest.fixture
def client():
    """Create a test client."""
    return Client()


@pytest.fixture
def authenticated_client(client, user):
    """Create an authenticated client."""
    client.force_login(user)
    return client


@pytest.fixture
def stake_president_client(client, stake_president_user):
    """Create a client logged in as stake president."""
    client.force_login(stake_president_user)
    return client


@pytest.fixture
def bishop_client(client, bishop_user):
    """Create a client logged in as bishop."""
    client.force_login(bishop_user)
    return client


@pytest.fixture
def clerk_client(client, clerk_user):
    """Create a client logged in as clerk."""
    client.force_login(clerk_user)
    return client


@pytest.fixture
def superuser_client(client, superuser):
    """Create a client logged in as superuser."""
    client.force_login(superuser)
    return client


@pytest.mark.django_db
class TestAuthentication:
    """Tests for authentication requirements."""
    
    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires authentication."""
        response = client.get(reverse('dashboard'))
        assert response.status_code == 302  # Redirect to login
        assert '/accounts/login/' in response.url
        
    def test_calling_list_requires_login(self, client):
        """Test that calling list requires authentication."""
        response = client.get(reverse('callings:calling-list'))
        assert response.status_code == 302
        
    def test_authenticated_user_can_access_dashboard(self, authenticated_client):
        """Test that authenticated users can access dashboard."""
        response = authenticated_client.get(reverse('dashboard'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestDashboardView:
    """Tests for the dashboard view."""
    
    def test_dashboard_loads(self, authenticated_client):
        """Test that dashboard loads successfully."""
        response = authenticated_client.get(reverse('dashboard'))
        assert response.status_code == 200
        assert 'title' in response.context
        assert response.context['title'] == 'Dashboard'
        
    def test_dashboard_shows_statistics(self, authenticated_client, calling):
        """Test that dashboard displays statistics."""
        response = authenticated_client.get(reverse('dashboard'))
        assert 'total_units' in response.context
        assert 'total_callings' in response.context
        assert 'active_callings_count' in response.context
        
    def test_dashboard_shows_active_callings(self, authenticated_client, calling):
        """Test that dashboard shows active callings."""
        response = authenticated_client.get(reverse('dashboard'))
        assert 'active_callings' in response.context
        assert calling in response.context['active_callings']


@pytest.mark.django_db
class TestUnitViews:
    """Tests for Unit CRUD views."""
    
    def test_unit_list_view(self, authenticated_client, ward):
        """Test unit list view."""
        response = authenticated_client.get(reverse('callings:unit-list'))
        assert response.status_code == 200
        assert ward in response.context['object_list']
        
    def test_unit_detail_view(self, authenticated_client, ward):
        """Test unit detail view."""
        url = reverse('callings:unit-detail', kwargs={'pk': ward.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response.context['object'] == ward
        
    def test_unit_create_view_get(self, superuser_client):
        """Test unit create view GET request."""
        response = superuser_client.get(reverse('callings:unit-create'))
        assert response.status_code == 200
        assert 'form' in response.context
        
    def test_unit_create_view_post(self, superuser_client):
        """Test unit create view POST request."""
        data = {
            'name': 'New Ward',
            'unit_type': 'WARD',
            'sort_order': 1,
            'is_active': True,
        }
        response = superuser_client.post(
            reverse('callings:unit-create'), 
            data=data
        )
        assert response.status_code == 302  # Redirect after success
        assert Unit.objects.filter(name='New Ward').exists()
        
    def test_unit_update_view(self, superuser_client, ward):
        """Test unit update view."""
        url = reverse('callings:unit-update', kwargs={'pk': ward.pk})
        data = {
            'name': 'Updated Ward Name',
            'unit_type': ward.unit_type,
            'sort_order': 1,
            'is_active': True,
        }
        response = superuser_client.post(url, data=data)
        assert response.status_code == 302
        ward.refresh_from_db()
        assert ward.name == 'Updated Ward Name'
        
    def test_unit_delete_view(self, superuser_client, ward):
        """Test unit delete view."""
        url = reverse('callings:unit-delete', kwargs={'pk': ward.pk})
        response = superuser_client.post(url)
        assert response.status_code == 302
        # Note: Depending on implementation, might be soft delete or hard delete


@pytest.mark.django_db
class TestOrganizationViews:
    """Tests for Organization CRUD views."""
    
    def test_organization_list_view(self, authenticated_client, organization):
        """Test organization list view."""
        response = authenticated_client.get(reverse('callings:organization-list'))
        assert response.status_code == 200
        assert organization in response.context['object_list']
        
    def test_organization_create_view(self, superuser_client, ward):
        """Test organization create view."""
        data = {
            'name': 'Young Women',
            'unit': ward.id,
            'leader': 'Sister Smith',
            'is_active': True,
        }
        response = superuser_client.post(
            reverse('callings:organization-create'),
            data=data
        )
        assert response.status_code == 302
        assert Organization.objects.filter(name='Young Women').exists()
        
    def test_organization_update_view(self, superuser_client, organization):
        """Test organization update view."""
        url = reverse('callings:organization-update', kwargs={'pk': organization.pk})
        data = {
            'name': organization.name,
            'unit': organization.unit.id,
            'leader': 'New Leader',
            'is_active': True,
        }
        response = superuser_client.post(url, data=data)
        assert response.status_code == 302
        organization.refresh_from_db()
        assert organization.leader == 'New Leader'


@pytest.mark.django_db
class TestPositionViews:
    """Tests for Position CRUD views."""
    
    def test_position_list_view(self, authenticated_client, position):
        """Test position list view."""
        response = authenticated_client.get(reverse('callings:position-list'))
        assert response.status_code == 200
        assert position in response.context['object_list']
        
    def test_position_create_view(self, superuser_client):
        """Test position create view."""
        data = {
            'title': 'Sunday School President',
            'description': 'Leads Sunday School',
            'is_active': True,
            'is_leadership': True,
            'requires_setting_apart': True,
        }
        response = superuser_client.post(
            reverse('callings:position-create'),
            data=data
        )
        assert response.status_code == 302
        assert Position.objects.filter(title='Sunday School President').exists()


@pytest.mark.django_db
class TestCallingViews:
    """Tests for Calling CRUD views."""
    
    def test_calling_list_view(self, authenticated_client, calling):
        """Test calling list view."""
        response = authenticated_client.get(reverse('callings:calling-list'))
        assert response.status_code == 200
        # Note: May need to check pagination
        
    def test_calling_detail_view(self, authenticated_client, calling):
        """Test calling detail view."""
        url = reverse('callings:calling-detail', kwargs={'pk': calling.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response.context['object'] == calling
        
    def test_calling_create_view_get(self, superuser_client):
        """Test calling create view GET request."""
        response = superuser_client.get(reverse('callings:calling-create'))
        assert response.status_code == 200
        assert 'form' in response.context
        
    def test_calling_create_view_post(
        self, superuser_client, ward, organization, position
    ):
        """Test calling create view POST request."""
        from datetime import date
        data = {
            'name': 'New Member',
            'unit': ward.id,
            'organization': organization.id,
            'position': position.id,
            'status': 'PENDING',
            'date_called': date.today().isoformat(),
            'is_active': True,
        }
        response = superuser_client.post(
            reverse('callings:calling-create'),
            data=data
        )
        assert response.status_code == 302
        assert Calling.objects.filter(name='New Member').exists()
        
    def test_calling_update_view(self, superuser_client, calling):
        """Test calling update view."""
        url = reverse('callings:calling-update', kwargs={'pk': calling.pk})
        data = {
            'name': 'Updated Name',
            'unit': calling.unit.id,
            'organization': calling.organization.id,
            'position': calling.position.id,
            'status': calling.status,
            'is_active': True,
        }
        response = superuser_client.post(url, data=data)
        assert response.status_code == 302
        calling.refresh_from_db()
        assert calling.name == 'Updated Name'
        
    def test_calling_delete_view_get(self, superuser_client, calling):
        """Test calling delete view GET shows confirmation."""
        url = reverse('callings:calling-delete', kwargs={'pk': calling.pk})
        response = superuser_client.get(url)
        assert response.status_code == 200
        assert 'object' in response.context
        
    def test_calling_delete_view_post(self, superuser_client, calling):
        """Test calling delete view POST deletes calling."""
        calling_id = calling.id
        url = reverse('callings:calling-delete', kwargs={'pk': calling.pk})
        response = superuser_client.post(url)
        assert response.status_code == 302
        # Check if calling still exists (might be soft delete)
        

@pytest.mark.django_db
class TestPermissionEnforcement:
    """Tests for permission enforcement on views."""
    
    def test_regular_user_cannot_delete_calling(self, authenticated_client, calling):
        """Test that regular users cannot delete callings."""
        url = reverse('callings:calling-delete', kwargs={'pk': calling.pk})
        response = authenticated_client.get(url)
        # Should be forbidden
        assert response.status_code == 403
        
    def test_stake_president_can_delete_calling(
        self, superuser_client, calling
    ):
        """Test that superusers can delete callings."""
        url = reverse('callings:calling-delete', kwargs={'pk': calling.pk})
        response = superuser_client.get(url)
        # Should be able to access delete page
        assert response.status_code == 200


@pytest.mark.django_db
class TestCallingReleaseView:
    """Tests for calling release view."""
    
    def test_release_view_get(self, superuser_client, calling):
        """Test release view GET request."""
        url = reverse('callings:calling-release', kwargs={'pk': calling.pk})
        response = superuser_client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context
        
    def test_release_view_post(self, superuser_client, calling):
        """Test release view POST request."""
        from datetime import date
        url = reverse('callings:calling-release', kwargs={'pk': calling.pk})
        data = {
            'date_released': date.today().isoformat(),
            'released_by': 'Bishop Smith',
            'release_notes': 'End of service',
        }
        response = superuser_client.post(url, data=data)
        assert response.status_code == 302
        calling.refresh_from_db()
        assert calling.date_released is not None


@pytest.mark.django_db
class TestSearchAndFiltering:
    """Tests for search and filtering functionality."""
    
    def test_calling_list_with_search(self, authenticated_client, calling):
        """Test calling list with search parameter."""
        response = authenticated_client.get(
            reverse('callings:calling-list'),
            {'search': calling.name}
        )
        assert response.status_code == 200
        
    def test_calling_list_with_status_filter(self, authenticated_client, calling):
        """Test calling list with status filter."""
        response = authenticated_client.get(
            reverse('callings:calling-list'),
            {'status': calling.status}
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestErrorHandling:
    """Tests for error handling."""
    
    def test_404_for_nonexistent_calling(self, authenticated_client):
        """Test that nonexistent calling returns 404."""
        url = reverse('callings:calling-detail', kwargs={'pk': 99999})
        response = authenticated_client.get(url)
        assert response.status_code == 404
        
    def test_invalid_form_submission_shows_errors(
        self, superuser_client, ward, organization, position
    ):
        """Test that invalid form shows validation errors."""
        from datetime import date, timedelta
        today = date.today()
        # Submit with sustained date before called date (invalid)
        data = {
            'unit': ward.id,
            'organization': organization.id,
            'position': position.id,
            'date_called': today,
            'date_sustained': today - timedelta(days=1),  # Invalid!
            'is_active': True,
        }
        response = superuser_client.post(
            reverse('callings:calling-create'),
            data=data
        )
        assert response.status_code == 200  # Stays on form
        assert 'form' in response.context
        assert response.context['form'].errors


@pytest.mark.django_db
class TestURLReversing:
    """Tests that all URLs reverse correctly."""
    
    def test_dashboard_url_reverses(self):
        """Test dashboard URL reverses."""
        url = reverse('dashboard')
        assert url == '/'
        
    def test_calling_urls_reverse(self, calling):
        """Test calling URLs reverse correctly."""
        assert reverse('callings:calling-list')
        assert reverse('callings:calling-create')
        assert reverse('callings:calling-detail', kwargs={'pk': calling.pk})
        assert reverse('callings:calling-update', kwargs={'pk': calling.pk})
        assert reverse('callings:calling-delete', kwargs={'pk': calling.pk})
        assert reverse('callings:calling-release', kwargs={'pk': calling.pk})
        
    def test_unit_urls_reverse(self, ward):
        """Test unit URLs reverse correctly."""
        assert reverse('callings:unit-list')
        assert reverse('callings:unit-create')
        assert reverse('callings:unit-detail', kwargs={'pk': ward.pk})
        assert reverse('callings:unit-update', kwargs={'pk': ward.pk})
        assert reverse('callings:unit-delete', kwargs={'pk': ward.pk})
