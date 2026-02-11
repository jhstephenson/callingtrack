# CallingTrack - Copilot Instructions

## Project Overview

CallingTrack is a Django 5.2.4 web application for managing church leadership callings within The Church of Jesus Christ of Latter-day Saints organizational structure. It tracks the complete calling lifecycle from proposal through approval, calling, sustaining, setting apart, and eventual release.

## Build, Test, and Development Commands

### Setup and Installation
```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix/Mac

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (includes testing tools)
pip install -r requirements-dev.txt

# Environment setup
cp .env.example .env  # Edit .env with your settings
```

### Database Management
```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Create permission groups (required for RBAC)
python manage.py create_groups
```

### Running the Application
```bash
# Development server
python manage.py runserver

# Production server (Heroku)
gunicorn callingtrack.wsgi --log-file -
```

### Testing
```bash
# Run tests (when implemented)
python manage.py test

# Run tests for specific app
python manage.py test callings
python manage.py test accounts
```

### Testing
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov

# Run specific test file
pytest callings/tests.py

# Run specific test class
pytest callings/tests.py::TestCallingModel

# Run specific test method
pytest callings/tests.py::TestCallingModel::test_create_calling

# Run tests without coverage
pytest --no-cov

# Run tests and stop on first failure
pytest -x
```

### Deployment
- **Production URL**: https://callingtrack-7e68d5e1da3a.herokuapp.com/
- **Platform**: Heroku with automatic migrations via release phase (see Procfile)
- **Database**: PostgreSQL in production, SQLite in development

## Architecture

### High-Level Structure

**Two Django Apps:**
1. **accounts** - Custom user authentication extending AbstractUser
2. **callings** - Core application with all calling management logic

**Data Model Hierarchy:**
```
Unit (Stake/Ward/Branch)
  └── Organizations (Relief Society, Primary, etc.)
      └── Positions (Teacher, President, etc.)
          └── Callings (Assignment of person to position)
              └── CallingHistory (Audit trail)
```

**Key Relationships:**
- **Hierarchical Units**: Units can have parent_unit relationships (e.g., Ward belongs to Stake)
- **One-to-Many**: Unit → Organizations, Organization → Callings, Position → Callings
- **Self-Referential**: Unit.parent_unit enables stake/ward hierarchies
- **Audit Trail**: CallingHistory records snapshots of all calling changes

### Calling Workflow and Status

The application implements a multi-stage approval workflow:

**Status Progression:**
```
PENDING → APPROVED (Stake Presidency) → HC_APPROVED (High Council) → CALLED → LCR_UPDATED
                                           ↓
                                       ON_HOLD (temporary pause)
```

**Date-Based Approval Tracking:**
- `presidency_approved`: Date field - when presidency approves
- `hc_approved`: Date field - when high council approves
- Auto-status updates: Setting `presidency_approved` date automatically changes status from PENDING to APPROVED

**Important**: The system used to have separate approval status fields but now uses date-based tracking. Setting an approval date automatically triggers status transitions in the `save()` method.

### Custom User Model

- Uses `accounts.User` extending `AbstractUser`
- Requires `AUTH_USER_MODEL = 'accounts.User'` in settings
- All ForeignKey references to users should use `settings.AUTH_USER_MODEL`

### Template Structure

Templates follow Django's app-based organization:
- Global templates in `/templates/`
- App-specific templates in `callings/templates/callings/`
- Base template: `callings/templates/callings/base.html`
- Dashboard: `callings/templates/callings/dashboard.html`

### Static Files

- Static files in `callings/static/callings/`
- Collected static files in `/staticfiles/` (for production)
- Uses WhiteNoise for serving static files in production

## Key Conventions

### Security and Permissions

**Role-Based Access Control (RBAC):**
- Uses Django groups for permission management
- Five roles: Stake President, Bishop, Stake Clerk, Clerk, Leadership
- Superusers bypass all permission checks
- See `docs/PERMISSIONS.md` for complete guide

**Permission Helpers:**
```python
from callings.permissions import (
    is_stake_president, is_bishop, is_clerk, is_leadership,
    can_edit_calling, can_approve_calling, can_delete_calling
)
```

**Permission Decorators and Mixins:**
- Function-based views: Use decorators like `@stake_president_required`, `@leadership_required`
- Class-based views: Use mixins like `StakePresidentRequiredMixin`, `CanEditCallingMixin`
- Always combine with `@login_required` or `LoginRequiredMixin`

**Security Settings:**
- Production security settings in `settings.py` (HSTS, secure cookies, etc.)
- Session timeout: 4 hours
- All security features enabled when `DEBUG=False`

**Logging:**
- Logs stored in `logs/` directory
- `callingtrack.log` - general application logs
- `errors.log` - error-level logs only
- Automatic log rotation (10MB max, 5 backups)
- Use `import logging; logger = logging.getLogger(__name__)` in modules

### Database Performance

**Indexes:**
The Calling and CallingHistory models have database indexes for common query patterns:
- Calling: status+date, unit+status, organization+status, is_active+status, date_released, lcr_updated
- CallingHistory: calling+changed_at, action+changed_at

Always use `select_related()` and `prefetch_related()` for foreign key queries to avoid N+1 problems.

### Model Patterns

**Display Methods:**
All models implement:
- `__str__()` - Human-readable string representation
- `get_absolute_url()` - Returns URL for detail view
- `get_list_display()` - Returns list of fields for table display

**Active/Inactive Pattern:**
Most models have `is_active` boolean field for soft deletion/archival. Always filter by `is_active=True` when showing current records.

**Ordering and Display:**
- `Unit`: Uses `sort_order` field, then alphabetically by name
- `Position`: Uses `display_order` field, then alphabetically by title
- `Calling`: Ordered by most recent `date_called` (descending)

### Calling-Specific Logic

**Name Display with (N/R) Suffix:**
- `get_display_name()` method appends "(N/R)" (Not Released) to calling names where `date_released` is null
- This indicates the person is still actively serving in the calling

**Status Badge Classes:**
Use `get_status_badge_class()` method which returns Bootstrap alert classes:
- PENDING → 'warning' (yellow)
- APPROVED → 'success' (green)
- HC_APPROVED → 'success' (green)
- CALLED → 'primary' (blue)
- ON_HOLD → 'warning' (yellow)
- LCR_UPDATED → 'info' (light blue)

**Date Validation:**
Calling dates should follow logical order:
1. `date_called` (when person is called)
2. `date_sustained` (when sustained by congregation)
3. `date_set_apart` (when person is set apart)
4. `date_released` (when released from calling)

### URL Patterns

All callings app URLs use `callings:` namespace:
- List views: `callings:calling-list`, `callings:unit-list`, etc.
- Detail views: `callings:calling-detail`, `callings:unit-detail`, etc.
- Create views: `callings:calling-create`, `callings:unit-create`, etc.
- Update views: `callings:calling-update`, `callings:unit-update`, etc.
- Delete views: `callings:calling-delete`, `callings:unit-delete`, etc.

### Environment Variables

Required in `.env` file:
- `SECRET_KEY` - Django secret key
- `DEBUG` - Boolean (default: False)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `DATABASE_URL` - PostgreSQL connection string (production only)

Uses `python-decouple` for configuration management.

### Authentication Requirements

- All views require authentication via `@login_required` decorator or `LoginRequiredMixin`
- Login URL: `/accounts/login/`
- Logout URL: `/accounts/logout/`
- Admin interface: `/admin/` (superuser access required)

### Forms and Validation

Forms are in `callings/forms.py` and handle:
- Field-level validation
- Cross-field validation (e.g., date ordering)
- Custom widgets for date fields
- Help text for user guidance

### Migration Best Practices

When modifying models:
1. Make model changes
2. Run `python manage.py makemigrations`
3. Review generated migration file
4. Test migration locally: `python manage.py migrate`
5. Commit both model changes and migration files together

## Code Style

- Follow Django's model field ordering convention: relationships, core fields, dates, metadata
- Use `blank=True, null=True` for optional fields
- Provide `help_text` for fields that need clarification
- Use `CHOICES` constants for status/type fields (all caps, plural names)
- Import `User` model as: `User = settings.AUTH_USER_MODEL`

## Important Files

- **PRD_CallingTrack.md** - Complete product requirements and business rules
- **PROJECT_PLAN.md** - Development roadmap and status tracking
- **docs/PERMISSIONS.md** - Complete RBAC documentation and usage guide
- **docs/** - User, admin, and technical documentation
- **Procfile** - Heroku deployment configuration
- **runtime.txt** - Python version specification (3.12)
- **.env.example** - Template for environment variables
- **pytest.ini** - Test configuration
- **.coveragerc** - Coverage reporting configuration
- **requirements.txt** - Production dependencies
- **requirements-dev.txt** - Development/testing dependencies

## LCR Integration

The system has `lcr_updated` boolean field on Calling model and `LCR_UPDATED` status for future integration with LDS Church's Leader and Clerk Resources system. This is preparation work - actual integration is not yet implemented.
