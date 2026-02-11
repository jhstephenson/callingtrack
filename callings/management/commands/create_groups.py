"""
Management command to create default permission groups for CallingTrack.

Run this command after initial setup to create the standard groups:
- Stake President
- Bishop
- Clerk
- Stake Clerk
- Leadership

Usage:
    python manage.py create_groups
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from callings.models import Calling, Unit, Organization, Position


class Command(BaseCommand):
    help = 'Creates default permission groups for CallingTrack'

    def handle(self, *args, **options):
        self.stdout.write('Creating permission groups...')
        
        # Get content types
        calling_ct = ContentType.objects.get_for_model(Calling)
        unit_ct = ContentType.objects.get_for_model(Unit)
        org_ct = ContentType.objects.get_for_model(Organization)
        position_ct = ContentType.objects.get_for_model(Position)
        
        # Define groups and their permissions
        groups_config = {
            'Stake President': {
                'description': 'Full access to all callings and organizational data',
                'permissions': [
                    # Calling permissions
                    'add_calling', 'change_calling', 'delete_calling', 'view_calling',
                    # Unit permissions
                    'add_unit', 'change_unit', 'delete_unit', 'view_unit',
                    # Organization permissions
                    'add_organization', 'change_organization', 'delete_organization', 'view_organization',
                    # Position permissions
                    'add_position', 'change_position', 'delete_position', 'view_position',
                ]
            },
            'Bishop': {
                'description': 'Access to ward-level callings',
                'permissions': [
                    'add_calling', 'change_calling', 'view_calling',
                    'view_unit', 'view_organization', 'view_position',
                ]
            },
            'Stake Clerk': {
                'description': 'Administrative access to all callings',
                'permissions': [
                    'add_calling', 'change_calling', 'view_calling',
                    'add_unit', 'change_unit', 'view_unit',
                    'add_organization', 'change_organization', 'view_organization',
                    'add_position', 'change_position', 'view_position',
                ]
            },
            'Clerk': {
                'description': 'Administrative access to ward callings',
                'permissions': [
                    'add_calling', 'change_calling', 'view_calling',
                    'view_unit', 'view_organization', 'view_position',
                ]
            },
            'Leadership': {
                'description': 'View access to callings for leadership members',
                'permissions': [
                    'view_calling', 'view_unit', 'view_organization', 'view_position',
                ]
            },
        }
        
        created_count = 0
        updated_count = 0
        
        for group_name, config in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created group: {group_name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'• Updated group: {group_name}')
                )
            
            # Clear existing permissions and add new ones
            group.permissions.clear()
            
            for perm_codename in config['permissions']:
                try:
                    # Try to find permission in callings app models
                    permission = Permission.objects.get(
                        codename=perm_codename,
                        content_type__app_label='callings'
                    )
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Permission not found: {perm_codename}')
                    )
            
            self.stdout.write(
                f'  Added {group.permissions.count()} permissions to {group_name}'
            )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} and updated {updated_count} groups'
            )
        )
        self.stdout.write('')
        self.stdout.write('Group setup complete. You can now assign users to these groups via:')
        self.stdout.write('  - Django admin interface (/admin/)')
        self.stdout.write('  - Or programmatically using: user.groups.add(group)')
