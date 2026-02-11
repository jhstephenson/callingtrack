"""
Tests for the callings app forms.
"""
import pytest
from datetime import date, timedelta, time
from django.forms import ValidationError
from callings.forms import (
    UnitForm, OrganizationForm, PositionForm, 
    CallingForm, CallingReleaseForm
)
from callings.models import Unit, Organization, Position, Calling


@pytest.mark.django_db
class TestUnitForm:
    """Tests for UnitForm."""
    
    def test_valid_unit_form(self):
        """Test form with valid data."""
        form_data = {
            'name': 'Test Ward',
            'unit_type': 'WARD',
            'meeting_time': '09:00',
            'location': '123 Main St',
            'sort_order': 1,
            'is_active': True,
        }
        form = UnitForm(data=form_data)
        assert form.is_valid()
        
    def test_unit_form_required_fields(self):
        """Test that name and unit_type are required."""
        form = UnitForm(data={})
        assert not form.is_valid()
        assert 'name' in form.errors
        assert 'unit_type' in form.errors
        
    def test_unit_form_excludes_self_from_parent(self, ward):
        """Test that unit cannot be its own parent."""
        form = UnitForm(instance=ward)
        # The queryset should exclude the ward itself
        assert ward not in form.fields['parent_unit'].queryset
        
    def test_unit_form_parent_unit_optional(self):
        """Test that parent_unit is optional."""
        form_data = {
            'name': 'Test Stake',
            'unit_type': 'STAKE',
            'sort_order': 0,  # Add missing required field
            'is_active': True,
        }
        form = UnitForm(data=form_data)
        assert form.is_valid(), form.errors
        
    def test_unit_form_time_widget(self):
        """Test that meeting_time uses HTML5 time input."""
        form = UnitForm()
        widget = form.fields['meeting_time'].widget
        assert widget.input_type == 'time'


@pytest.mark.django_db
class TestOrganizationForm:
    """Tests for OrganizationForm."""
    
    def test_valid_organization_form(self, ward):
        """Test form with valid data."""
        form_data = {
            'name': 'Young Men',
            'unit': ward.id,
            'leader': 'John Doe',
            'description': 'Young Men organization',
            'is_active': True,
        }
        form = OrganizationForm(data=form_data)
        assert form.is_valid()
        
    def test_organization_form_required_fields(self):
        """Test that name is required."""
        form = OrganizationForm(data={})
        assert not form.is_valid()
        assert 'name' in form.errors
        
    def test_organization_form_optional_fields(self, ward):
        """Test that unit, leader, and description are optional."""
        form_data = {
            'name': 'Primary',
            'is_active': True,
        }
        form = OrganizationForm(data=form_data)
        assert form.is_valid()


@pytest.mark.django_db
class TestPositionForm:
    """Tests for PositionForm."""
    
    def test_valid_position_form(self):
        """Test form with valid data."""
        form_data = {
            'title': 'Elder Quorum President',
            'description': 'Leads the Elder Quorum',
            'is_active': True,
            'is_leadership': True,
            'requires_setting_apart': True,
        }
        form = PositionForm(data=form_data)
        assert form.is_valid()
        
    def test_position_form_required_fields(self):
        """Test that title is required."""
        form = PositionForm(data={})
        assert not form.is_valid()
        assert 'title' in form.errors
        
    def test_position_form_boolean_defaults(self):
        """Test boolean fields have correct defaults."""
        form_data = {
            'title': 'Teacher',
            'is_active': False,  # Explicitly set to False
        }
        form = PositionForm(data=form_data)
        assert form.is_valid()
        position = form.save()
        assert position.is_active is False  # Should be False as set in form
        assert position.is_leadership is False  # Model default
        assert position.requires_setting_apart is False  # Model default


@pytest.mark.django_db
class TestCallingForm:
    """Tests for CallingForm."""
    
    def test_valid_calling_form(self, ward, organization, position):
        """Test form with valid complete data."""
        today = date.today()
        form_data = {
            'name': 'John Smith',
            'unit': ward.id,
            'organization': organization.id,
            'position': position.id,
            'status': 'PENDING',
            'date_called': today,
            'date_sustained': today + timedelta(days=7),
            'date_set_apart': today + timedelta(days=14),
            'called_by': 'Bishop Jones',
            'is_active': True,
        }
        form = CallingForm(data=form_data)
        assert form.is_valid(), form.errors
        
    def test_calling_form_required_fields(self):
        """Test that unit, organization, position are required."""
        form = CallingForm(data={})
        assert not form.is_valid()
        assert 'unit' in form.errors
        assert 'organization' in form.errors
        assert 'position' in form.errors
        
    def test_calling_form_name_not_required(self, ward, organization, position):
        """Test that name is not required initially."""
        form_data = {
            'unit': ward.id,
            'organization': organization.id,
            'position': position.id,
            'status': 'PENDING',
            'is_active': True,
        }
        form = CallingForm(data=form_data)
        assert form.is_valid()
        
    def test_calling_form_initial_status_pending(self):
        """Test that status defaults to PENDING for new callings."""
        form = CallingForm()
        assert form.fields['status'].initial == 'PENDING'
        
    def test_calling_form_date_validation_sustained_before_called(
        self, ward, organization, position
    ):
        """Test that sustained date cannot be before called date."""
        today = date.today()
        form_data = {
            'unit': ward.id,
            'organization': organization.id,
            'position': position.id,
            'date_called': today,
            'date_sustained': today - timedelta(days=1),  # Before called!
            'is_active': True,
        }
        form = CallingForm(data=form_data)
        assert not form.is_valid()
        assert 'date_sustained' in form.errors
        assert 'cannot be before called date' in str(form.errors['date_sustained'])
        
    def test_calling_form_date_validation_set_apart_before_sustained(
        self, ward, organization, position
    ):
        """Test that set apart date cannot be before sustained date."""
        today = date.today()
        form_data = {
            'unit': ward.id,
            'organization': organization.id,
            'position': position.id,
            'date_called': today,
            'date_sustained': today + timedelta(days=7),
            'date_set_apart': today + timedelta(days=3),  # Before sustained!
            'is_active': True,
        }
        form = CallingForm(data=form_data)
        assert not form.is_valid()
        assert 'date_set_apart' in form.errors
        assert 'cannot be before sustained date' in str(form.errors['date_set_apart'])
        
    def test_calling_form_valid_date_order(self, ward, organization, position):
        """Test that correct date order validates successfully."""
        today = date.today()
        form_data = {
            'unit': ward.id,
            'organization': organization.id,
            'position': position.id,
            'status': 'PENDING',  # Add required status field
            'date_called': today,
            'date_sustained': today + timedelta(days=7),
            'date_set_apart': today + timedelta(days=14),
            'date_released': today + timedelta(days=365),
            'is_active': True,
        }
        form = CallingForm(data=form_data)
        assert form.is_valid(), form.errors
        
    def test_calling_form_date_widgets(self):
        """Test that date fields use HTML5 date input."""
        form = CallingForm()
        assert form.fields['date_called'].widget.input_type == 'date'
        assert form.fields['date_sustained'].widget.input_type == 'date'
        assert form.fields['date_set_apart'].widget.input_type == 'date'
        assert form.fields['date_released'].widget.input_type == 'date'
        
    def test_calling_form_partial_dates_valid(self, ward, organization, position):
        """Test that having only some dates is valid."""
        today = date.today()
        form_data = {
            'unit': ward.id,
            'organization': organization.id,
            'position': position.id,
            'status': 'PENDING',  # Add required status field
            'date_called': today,
            # No sustained or set apart dates
            'is_active': True,
        }
        form = CallingForm(data=form_data)
        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestCallingReleaseForm:
    """Tests for CallingReleaseForm."""
    
    def test_valid_release_form(self, calling):
        """Test form with valid data."""
        form_data = {
            'date_released': date.today(),
            'released_by': 'Bishop Smith',
            'release_notes': 'Member moving to another ward',
        }
        form = CallingReleaseForm(data=form_data, instance=calling)
        assert form.is_valid()
        
    def test_release_form_required_fields(self, calling):
        """Test that date_released and release_notes are required."""
        form = CallingReleaseForm(data={}, instance=calling)
        assert not form.is_valid()
        assert 'date_released' in form.errors
        assert 'release_notes' in form.errors
        
    def test_release_form_only_includes_release_fields(self, calling):
        """Test that form only includes release-related fields."""
        form = CallingReleaseForm(instance=calling)
        assert 'date_released' in form.fields
        assert 'released_by' in form.fields
        assert 'release_notes' in form.fields
        # Should not include other calling fields
        assert 'name' not in form.fields
        assert 'status' not in form.fields
        assert 'date_called' not in form.fields
        
    def test_release_form_date_widget(self):
        """Test that date_released uses HTML5 date input."""
        form = CallingReleaseForm()
        assert form.fields['date_released'].widget.input_type == 'date'
        
    def test_release_form_save(self, calling):
        """Test that form saves release data correctly."""
        today = date.today()
        form_data = {
            'date_released': today,
            'released_by': 'Bishop Smith',
            'release_notes': 'Completed service term',
        }
        form = CallingReleaseForm(data=form_data, instance=calling)
        assert form.is_valid()
        calling = form.save()
        assert calling.date_released == today
        assert calling.released_by == 'Bishop Smith'
        assert calling.release_notes == 'Completed service term'


@pytest.mark.django_db
class TestFormIntegration:
    """Integration tests for forms working together."""
    
    def test_create_complete_calling_workflow(self, ward, organization, position):
        """Test creating a calling with complete workflow."""
        today = date.today()
        
        # Create calling
        calling_data = {
            'name': 'Jane Doe',
            'unit': ward.id,
            'organization': organization.id,
            'position': position.id,
            'status': 'PENDING',
            'date_called': today,
            'called_by': 'Bishop Jones',
            'is_active': True,
        }
        calling_form = CallingForm(data=calling_data)
        assert calling_form.is_valid()
        calling = calling_form.save()
        
        # Update with sustained date
        calling_data.update({
            'date_sustained': today + timedelta(days=7),
            'status': 'APPROVED',
        })
        update_form = CallingForm(data=calling_data, instance=calling)
        assert update_form.is_valid()
        calling = update_form.save()
        
        # Release calling
        release_data = {
            'date_released': today + timedelta(days=365),
            'released_by': 'Bishop Smith',
            'release_notes': 'End of term',
        }
        release_form = CallingReleaseForm(data=release_data, instance=calling)
        assert release_form.is_valid()
        calling = release_form.save()
        
        assert calling.date_released is not None
        assert calling.released_by == 'Bishop Smith'
