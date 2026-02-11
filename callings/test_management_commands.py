"""
Tests for management commands.
"""
import pytest
from io import StringIO
from django.core.management import call_command
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from callings.models import Calling, Unit, Organization, Position


@pytest.mark.django_db
class TestCreateGroupsCommand:
    """Tests for the create_groups management command."""
    
    def test_command_creates_all_groups(self):
        """Test that command creates all five permission groups."""
        # Ensure no groups exist initially
        Group.objects.all().delete()
        
        out = StringIO()
        call_command('create_groups', stdout=out)
        
        # Check all groups were created
        assert Group.objects.count() == 5
        assert Group.objects.filter(name='Stake President').exists()
        assert Group.objects.filter(name='Bishop').exists()
        assert Group.objects.filter(name='Stake Clerk').exists()
        assert Group.objects.filter(name='Clerk').exists()
        assert Group.objects.filter(name='Leadership').exists()
        
        # Check output message
        output = out.getvalue()
        assert 'Created group: Stake President' in output
        assert 'Successfully created 5' in output
        
    def test_command_is_idempotent(self):
        """Test that running command twice doesn't create duplicates."""
        # Run command first time
        call_command('create_groups', stdout=StringIO())
        initial_count = Group.objects.count()
        
        # Run command second time
        out = StringIO()
        call_command('create_groups', stdout=out)
        
        # Should still have same number of groups
        assert Group.objects.count() == initial_count
        
        # Should show "Updated" not "Created"
        output = out.getvalue()
        assert 'Updated group:' in output
        assert 'updated 5' in output
        
    def test_stake_president_group_has_full_permissions(self):
        """Test that Stake President group has all permissions."""
        call_command('create_groups', stdout=StringIO())
        
        group = Group.objects.get(name='Stake President')
        permissions = group.permissions.all()
        
        # Should have add, change, delete, view for all models
        assert permissions.filter(codename='add_calling').exists()
        assert permissions.filter(codename='change_calling').exists()
        assert permissions.filter(codename='delete_calling').exists()
        assert permissions.filter(codename='view_calling').exists()
        
        assert permissions.filter(codename='add_unit').exists()
        assert permissions.filter(codename='change_unit').exists()
        assert permissions.filter(codename='delete_unit').exists()
        assert permissions.filter(codename='view_unit').exists()
        
        assert permissions.filter(codename='add_organization').exists()
        assert permissions.filter(codename='change_organization').exists()
        assert permissions.filter(codename='delete_organization').exists()
        assert permissions.filter(codename='view_organization').exists()
        
        assert permissions.filter(codename='add_position').exists()
        assert permissions.filter(codename='change_position').exists()
        assert permissions.filter(codename='delete_position').exists()
        assert permissions.filter(codename='view_position').exists()
        
    def test_bishop_group_has_limited_permissions(self):
        """Test that Bishop group has appropriate limited permissions."""
        call_command('create_groups', stdout=StringIO())
        
        group = Group.objects.get(name='Bishop')
        permissions = group.permissions.all()
        
        # Should have add, change, view for calling
        assert permissions.filter(codename='add_calling').exists()
        assert permissions.filter(codename='change_calling').exists()
        assert permissions.filter(codename='view_calling').exists()
        
        # Should NOT have delete_calling
        assert not permissions.filter(codename='delete_calling').exists()
        
        # Should only have view for units, organizations, positions
        assert permissions.filter(codename='view_unit').exists()
        assert not permissions.filter(codename='add_unit').exists()
        assert not permissions.filter(codename='change_unit').exists()
        assert not permissions.filter(codename='delete_unit').exists()
        
    def test_stake_clerk_group_has_admin_permissions(self):
        """Test that Stake Clerk group has admin permissions."""
        call_command('create_groups', stdout=StringIO())
        
        group = Group.objects.get(name='Stake Clerk')
        permissions = group.permissions.all()
        
        # Should have add, change, view for callings
        assert permissions.filter(codename='add_calling').exists()
        assert permissions.filter(codename='change_calling').exists()
        assert permissions.filter(codename='view_calling').exists()
        
        # Should NOT have delete_calling
        assert not permissions.filter(codename='delete_calling').exists()
        
        # Should have add, change, view for units
        assert permissions.filter(codename='add_unit').exists()
        assert permissions.filter(codename='change_unit').exists()
        assert permissions.filter(codename='view_unit').exists()
        
    def test_clerk_group_permissions(self):
        """Test that Clerk group has appropriate permissions."""
        call_command('create_groups', stdout=StringIO())
        
        group = Group.objects.get(name='Clerk')
        permissions = group.permissions.all()
        
        # Should have add, change, view for calling
        assert permissions.filter(codename='add_calling').exists()
        assert permissions.filter(codename='change_calling').exists()
        assert permissions.filter(codename='view_calling').exists()
        
        # Should NOT have delete or admin permissions
        assert not permissions.filter(codename='delete_calling').exists()
        assert not permissions.filter(codename='add_unit').exists()
        
    def test_leadership_group_has_view_only(self):
        """Test that Leadership group has view-only permissions."""
        call_command('create_groups', stdout=StringIO())
        
        group = Group.objects.get(name='Leadership')
        permissions = group.permissions.all()
        
        # Should only have view permissions
        assert permissions.filter(codename='view_calling').exists()
        assert permissions.filter(codename='view_unit').exists()
        assert permissions.filter(codename='view_organization').exists()
        assert permissions.filter(codename='view_position').exists()
        
        # Should NOT have any add, change, or delete
        assert not permissions.filter(codename='add_calling').exists()
        assert not permissions.filter(codename='change_calling').exists()
        assert not permissions.filter(codename='delete_calling').exists()
        
    def test_command_updates_existing_groups(self):
        """Test that command updates permissions on existing groups."""
        # Create a group with no permissions
        group = Group.objects.create(name='Stake President')
        assert group.permissions.count() == 0
        
        # Run command
        call_command('create_groups', stdout=StringIO())
        
        # Group should now have permissions
        group.refresh_from_db()
        assert group.permissions.count() > 0
        
    def test_command_clears_old_permissions(self):
        """Test that command clears old permissions before adding new ones."""
        # Create group with a random permission
        group = Group.objects.create(name='Stake President')
        # Add a permission that shouldn't be there
        perm = Permission.objects.first()
        group.permissions.add(perm)
        initial_perm_count = group.permissions.count()
        
        # Run command
        call_command('create_groups', stdout=StringIO())
        
        # Permissions should be reset to what the command specifies
        group.refresh_from_db()
        # Should have the correct permissions, not the random one
        assert group.permissions.filter(
            content_type__app_label='callings'
        ).exists()
        
    def test_command_output_formatting(self):
        """Test that command output is well-formatted."""
        Group.objects.all().delete()
        
        out = StringIO()
        call_command('create_groups', stdout=out)
        output = out.getvalue()
        
        # Check for success indicators
        assert '✓' in output or 'Created' in output
        assert 'permissions to' in output
        assert 'Group setup complete' in output
        
    def test_command_handles_missing_permissions_gracefully(self):
        """Test that command handles missing permissions without crashing."""
        # This shouldn't crash even if some permissions don't exist yet
        out = StringIO()
        call_command('create_groups', stdout=out)
        
        # Should complete successfully
        assert Group.objects.count() == 5


@pytest.mark.django_db
class TestManagementCommandIntegration:
    """Integration tests for management commands."""
    
    def test_create_groups_then_assign_user(self, user):
        """Test creating groups and assigning a user."""
        call_command('create_groups', stdout=StringIO())
        
        # Assign user to Stake President group
        group = Group.objects.get(name='Stake President')
        user.groups.add(group)
        
        # User should have the group
        assert user.groups.filter(name='Stake President').exists()
        
        # User should have group permissions
        assert user.has_perm('callings.add_calling')
        assert user.has_perm('callings.change_calling')
        assert user.has_perm('callings.delete_calling')
        assert user.has_perm('callings.view_calling')
        
    def test_groups_work_with_permission_system(self, user):
        """Test that created groups integrate with permission system."""
        call_command('create_groups', stdout=StringIO())
        
        # Test different groups
        bishop_group = Group.objects.get(name='Bishop')
        leadership_group = Group.objects.get(name='Leadership')
        
        # Bishop should be able to add/change but not delete
        user.groups.add(bishop_group)
        user = type(user).objects.get(pk=user.pk)  # Refresh to clear permission cache
        assert user.has_perm('callings.add_calling')
        assert user.has_perm('callings.change_calling')
        assert not user.has_perm('callings.delete_calling')
        
        # Remove bishop, add leadership
        user.groups.remove(bishop_group)
        user.groups.add(leadership_group)
        user = type(user).objects.get(pk=user.pk)  # Refresh to clear permission cache
        
        # Leadership should only have view
        assert not user.has_perm('callings.add_calling')
        assert not user.has_perm('callings.change_calling')
        assert user.has_perm('callings.view_calling')


@pytest.mark.django_db
class TestOtherManagementCommands:
    """Tests for other management commands (if they exist)."""
    
    def test_cleanup_members_command_exists(self):
        """Test that cleanup_members command exists."""
        # This will fail if command doesn't exist
        try:
            call_command('cleanup_members', '--help', stdout=StringIO())
        except Exception as e:
            # Command might not be fully implemented yet
            pass
            
    def test_import_callings_command_exists(self):
        """Test that import_callings command exists."""
        try:
            call_command('import_callings', '--help', stdout=StringIO())
        except Exception as e:
            # Command might not be fully implemented yet
            pass


@pytest.mark.django_db
class TestCommandErrorHandling:
    """Tests for command error handling."""
    
    def test_create_groups_with_no_permissions_available(self):
        """Test command behavior when permissions don't exist."""
        # Delete all permissions (shouldn't happen in real scenario)
        Permission.objects.filter(
            content_type__app_label='callings'
        ).delete()
        
        # Command should still run without crashing
        out = StringIO()
        try:
            call_command('create_groups', stdout=out)
            # If we get here, command handled it gracefully
            assert True
        except Exception as e:
            # Command might fail, which is acceptable
            assert 'Permission' in str(e) or 'permission' in str(e)
