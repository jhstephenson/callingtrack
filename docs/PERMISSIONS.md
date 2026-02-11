# CallingTrack Permissions System

## Overview

CallingTrack implements a role-based access control (RBAC) system using Django's built-in groups and permissions. This system controls who can view, create, edit, approve, and delete callings and organizational data.

## Permission Groups

### Stake President
- **Full access** to all callings and organizational data
- Can create, edit, approve, and delete all records
- Can manage units, organizations, and positions
- Highest level of access

### Bishop
- Access to **ward-level callings**
- Can create, edit, and approve callings
- Can view units, organizations, and positions
- Cannot delete callings or manage units

### Stake Clerk
- **Administrative access** to all callings
- Can create and edit all callings
- Can manage units, organizations, and positions
- Cannot approve or delete callings

### Clerk
- **Administrative access** to ward callings
- Can create and edit callings
- Can view units, organizations, and positions
- Cannot approve, delete, or manage organizational structure

### Leadership
- **View-only access** to callings
- Can view all calling data for reporting/oversight
- Cannot make any changes

## Setup

### 1. Create Permission Groups

Run the management command to create all groups:

```bash
python manage.py create_groups
```

This will create all five groups with appropriate permissions.

### 2. Assign Users to Groups

**Via Django Admin:**
1. Go to `/admin/`
2. Navigate to **Users**
3. Select a user
4. Scroll to **Groups** section
5. Add user to appropriate group(s)

**Programmatically:**
```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()
user = User.objects.get(username='john_doe')

# Add to group
stake_president_group = Group.objects.get(name='Stake President')
user.groups.add(stake_president_group)

# Remove from group
user.groups.remove(stake_president_group)
```

## Using Permissions in Code

### Function-Based Views

```python
from callings.permissions import stake_president_required, leadership_required

@stake_president_required
def manage_stakes(request):
    # Only stake presidents can access
    pass

@leadership_required
def view_reports(request):
    # Any leadership member can access
    pass
```

### Class-Based Views

```python
from callings.permissions import StakePresidentRequiredMixin, CanEditCallingMixin

class CallingCreateView(CanEditCallingMixin, CreateView):
    # Only users who can edit callings can create
    model = Calling
    fields = [...]

class UnitManageView(StakePresidentRequiredMixin, UpdateView):
    # Only stake presidents can manage units
    model = Unit
    fields = [...]
```

### Template Usage

```django
{% if user.is_superuser or user.groups.filter(name='Stake President').exists %}
    <a href="{% url 'callings:calling-delete' calling.pk %}">Delete</a>
{% endif %}
```

### Permission Helper Functions

```python
from callings.permissions import (
    is_stake_president,
    is_bishop,
    is_clerk,
    can_edit_calling,
    can_approve_calling,
)

if can_edit_calling(request.user):
    # User can edit callings
    pass

if can_approve_calling(request.user):
    # User can approve callings
    pass
```

## Available Decorators

- `@stake_president_required` - Requires Stake President role
- `@bishop_required` - Requires Bishop role
- `@clerk_required` - Requires any Clerk role
- `@leadership_required` - Requires any Leadership role
- `@can_edit_required` - Requires calling edit permission

## Available Mixins

- `StakePresidentRequiredMixin`
- `BishopRequiredMixin`
- `ClerkRequiredMixin`
- `LeadershipRequiredMixin`
- `CanEditCallingMixin`
- `CanApproveCallingMixin`
- `CanDeleteCallingMixin`
- `CanManageUnitsMixin`

## Permission Logic

### Superuser
- Superusers bypass all permission checks
- Have full access to everything

### Permission Hierarchy

```
Superuser
  └─ Stake President (full access)
      ├─ Bishop (ward callings + approve)
      ├─ Stake Clerk (all admin, no approve/delete)
      │   └─ Clerk (ward admin, no approve/delete)
      └─ Leadership (view only)
```

## Testing Permissions

Run permission tests:

```bash
pytest callings/test_permissions.py -v
```

Test specific permission:

```bash
pytest callings/test_permissions.py::TestCallingPermissions::test_can_edit_calling_leadership -v
```

## Security Notes

1. **Always use LoginRequiredMixin** or `@login_required` in addition to permission checks
2. **Superusers bypass all checks** - be careful who gets superuser status
3. **Groups are additive** - users can belong to multiple groups
4. **Test your permissions** - verify access controls work as expected

## Future Enhancements

- Unit-based access control (users can only access their assigned units)
- Custom permissions for specific callings or organizations
- Audit logging for permission changes
- Time-based permissions (temporary elevated access)
