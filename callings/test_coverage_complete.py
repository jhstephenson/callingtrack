"""
Additional tests to achieve 100% code coverage.
Tests for edge cases, admin interfaces, and template tags.
"""
import pytest
from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.template import Context, Template
from callings.models import Unit, Organization, Position, Calling, CallingHistory
from callings.admin import CallingHistoryAdmin, CallingAdmin
from accounts.admin import UserAdmin

User = get_user_model()


@pytest.mark.django_db
class TestModelEdgeCases:
    """Test edge cases in models for 100% coverage."""
    
    def test_calling_get_display_name_without_name(self, ward, organization, position):
        """Test get_display_name when name is None (line 239 in models.py)."""
        calling = Calling.objects.create(
            name=None,  # Explicitly None
            unit=ward,
            organization=organization,
            position=position,
            status='PENDING'
        )
        # When name is None, should return None
        result = calling.get_display_name()
        assert result is None


@pytest.mark.django_db
class TestAdminInterfaces:
    """Test admin interface methods for 100% coverage."""
    
    def test_calling_history_admin_has_no_add_permission(self, user):
        """Test that CallingHistory admin prevents adding (line 33 in admin.py)."""
        site = AdminSite()
        admin = CallingHistoryAdmin(CallingHistory, site)
        factory = RequestFactory()
        request = factory.get('/admin/')
        request.user = user  # Add user to request
        
        # Should return False - cannot add CallingHistory through admin
        assert admin.has_add_permission(request) is False
        
    def test_calling_admin_list_display(self, ward, organization, position):
        """Test CallingAdmin list display configuration."""
        site = AdminSite()
        admin = CallingAdmin(Calling, site)
        
        # Verify list_display is configured
        assert 'unit' in admin.list_display
        assert 'position' in admin.list_display
        assert 'status' in admin.list_display


@pytest.mark.django_db
class TestTemplateTagsEdgeCases:
    """Test template tag edge cases for 100% coverage."""
    
    def test_sort_header_default_order(self):
        """Test sort_header template tag with default order."""
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/callings/')
        context = Context({'request': request})
        
        template = Template(
            "{% load table_tags %}"
            "{% sort_header 'name' 'Name' %}"
        )
        result = template.render(context)
        assert 'Name' in result
        assert 'sort=name' in result
        
    def test_sort_header_toggle_order(self):
        """Test sort_header toggles order when already sorted."""
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/callings/?sort=name&order=asc')
        context = Context({'request': request})
        
        template = Template(
            "{% load table_tags %}"
            "{% sort_header 'name' 'Name' %}"
        )
        result = template.render(context)
        assert 'order=desc' in result  # Should toggle to desc
        assert 'fa-sort-up' in result  # Should show up arrow for asc
        
    def test_sort_header_shows_desc_icon(self):
        """Test sort_header shows descending icon when sorted desc."""
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/callings/?sort=name&order=desc')
        context = Context({'request': request})
        
        template = Template(
            "{% load table_tags %}"
            "{% sort_header 'name' 'Name' %}"
        )
        result = template.render(context)
        assert 'fa-sort-down' in result  # Should show down arrow for desc
        assert 'order=asc' in result  # Should toggle to asc
        
    def test_sort_url_tag(self):
        """Test sort_url template tag."""
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/callings/')
        context = Context({'request': request})
        
        template = Template(
            "{% load table_tags %}"
            "{% sort_url 'status' 'desc' %}"
        )
        result = template.render(context)
        assert 'sort=status' in result
        assert 'order=desc' in result


@pytest.mark.django_db  
class TestCallingReleaseForm:
    """Test CallingReleaseForm for complete coverage."""
    
    def test_calling_release_form_init(self, calling):
        """Test CallingReleaseForm __init__ method."""
        from callings.forms import CallingReleaseForm
        form = CallingReleaseForm(instance=calling)
        
        # Check that only release fields are included
        assert 'date_released' in form.fields
        assert 'released_by' in form.fields
        assert 'release_notes' in form.fields
        
        # Check that other fields are excluded
        assert 'name' not in form.fields
        assert 'position' not in form.fields
        
    def test_calling_release_form_save(self, calling):
        """Test CallingReleaseForm save method."""
        from datetime import date
        from callings.forms import CallingReleaseForm
        
        data = {
            'date_released': date.today(),
            'released_by': 'Bishop Smith',
            'release_notes': 'Completed service',
        }
        form = CallingReleaseForm(data=data, instance=calling)
        assert form.is_valid()
        
        updated_calling = form.save()
        assert updated_calling.date_released == date.today()
        assert updated_calling.released_by == 'Bishop Smith'
        assert updated_calling.release_notes == 'Completed service'


@pytest.mark.django_db
class TestCustomUserCreationFormInCallings:
    """Test CustomUserCreationForm in callings.forms for complete coverage."""
    
    def test_form_init_sets_required_fields(self):
        """Test __init__ method sets email, first_name, last_name as required."""
        from callings.forms import CustomUserCreationForm
        form = CustomUserCreationForm()
        
        assert form.fields['email'].required is True
        assert form.fields['first_name'].required is True
        assert form.fields['last_name'].required is True
        
    def test_form_save_method(self):
        """Test save method sets user fields correctly."""
        from callings.forms import CustomUserCreationForm
        
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        form = CustomUserCreationForm(data=form_data)
        assert form.is_valid()
        
        user = form.save()
        assert user.email == 'newuser@example.com'
        assert user.first_name == 'New'
        assert user.last_name == 'User'
        
    def test_form_save_without_commit(self):
        """Test save method with commit=False."""
        from callings.forms import CustomUserCreationForm
        
        form_data = {
            'username': 'tempuser',
            'email': 'temp@example.com',
            'first_name': 'Temp',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        form = CustomUserCreationForm(data=form_data)
        assert form.is_valid()
        
        user = form.save(commit=False)
        assert user.email == 'temp@example.com'
        assert user.pk is None  # Not saved yet
        user.save()  # Now save it
        assert user.pk is not None


@pytest.mark.django_db
class TestAccountsViews:
    """Test accounts views (currently just imports)."""
    
    def test_accounts_views_imports(self):
        """Test that accounts.views can be imported."""
        from accounts import views
        # Just verify the import works
        assert views is not None
