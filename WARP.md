# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

CallingTrack is a Django 5.2.4 web application for managing church leadership callings within The Church of Jesus Christ of Latter-day Saints organizational structure. It provides a complete workflow for tracking callings from proposal through completion, with approval workflows and status management.

## Architecture Overview

### Core Django Structure
- **Django Version**: 5.2.4 with Python 3.12.5
- **Custom User Model**: `accounts.User` extends AbstractUser
- **Main Apps**: `accounts` (authentication) and `callings` (core functionality)
- **Database**: PostgreSQL (production) / SQLite (development) via `dj-database-url`
- **Static Files**: Managed with WhiteNoise for production

### Data Model Architecture

The application follows a hierarchical organizational model:

#### Core Models
1. **Unit** → **Organization** → **Position** → **Calling**
   - `Unit`: Wards, Branches, Stakes with hierarchical parent-child relationships
   - `Organization`: Relief Society, Elders Quorum, etc. within units
   - `Position`: Specific calling titles with leadership designations
   - `Calling`: Individual calling assignments with complex approval workflows

#### Key Model Relationships
- Unit can have multiple Organizations
- Organization can have multiple Positions  
- Callings reference Unit, Organization, and Position (Many-to-One)
- CallingHistory tracks all changes with JSON snapshots

#### Status Management
Callings progress through statuses: `PENDING` → `APPROVED` → `COMPLETED` → `LCR_UPDATED`
Additional statuses: `CANCELLED`, `ON_HOLD`, `RELEASED`

### View Architecture

#### View Patterns
- **Function-based**: `dashboard()` - main dashboard with active callings
- **Class-based**: CRUD operations using ListView, DetailView, CreateView, UpdateView, DeleteView
- **Custom Mixins**:
  - `SuperuserRequiredMixin`: Restricts admin operations
  - `TitleMixin`: Consistent page titles
  - `SortableMixin`: Sortable table functionality

#### Key Views
- `dashboard`: Central hub showing active callings and statistics
- `CallingsByUnitView`: Organized calling listings by unit with filtering
- `CallingUpdateView`: Smart return navigation after edits
- Documentation views for user, admin, and technical guides

### URL Structure
- Root: Dashboard (`/`)
- Callings: `/callings/`, `/callings/by-unit/`, `/callings/<id>/`
- Units: `/units/`
- Organizations: `/organizations/`
- Positions: `/positions/`
- Docs: `/docs/user-guide/`, `/docs/admin-guide/`, `/docs/technical-guide/`

### Template Organization
```
templates/
├── callings/
│   ├── base.html (Bootstrap 5 layout)
│   ├── dashboard.html
│   ├── calling/ (CRUD templates)
│   ├── unit/ (Unit management)
│   ├── organization/ (Organization management)
│   ├── position/ (Position management)
│   └── docs/ (Documentation)
└── registration/ (Authentication)
```

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Environment configuration
# Create .env file with required variables:
# SECRET_KEY, DEBUG, DATABASE_URL, ALLOWED_HOSTS
```

### Database Operations
```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Reset migrations (development only)
python manage.py migrate callings zero
# Delete migration files: callings/migrations/0*.py
python manage.py makemigrations
python manage.py migrate
```

### Development Server
```bash
# Run development server
python manage.py runserver

# Run on specific port
python manage.py runserver 8080

# Access points:
# http://localhost:8000/ (main dashboard)
# http://localhost:8000/admin/ (Django admin)
```

### Static Files Management
```bash
# Collect static files for production
python manage.py collectstatic

# Clear and recollect static files
python manage.py collectstatic --clear --noinput
```

### Testing and Validation
```bash
# Run Django checks
python manage.py check

# Test database connection
python manage.py dbshell

# Django shell for model testing
python manage.py shell
```

### Data Management
```bash
# Load initial data (if fixtures exist)
python manage.py loaddata initial_data.json

# Create database backup (JSON format)
python manage.py dumpdata --indent 2 > backup.json

# Load specific app data
python manage.py loaddata callings
```

## Key Configuration

### Settings Structure
- Environment-based configuration using `python-decouple`
- Database URL configuration for flexible deployment
- WhiteNoise for static file serving
- Custom user model: `accounts.User`

### Dependencies
Core packages from `requirements.txt`:
- Django 5.2.4
- psycopg2-binary (PostgreSQL)
- python-decouple (environment variables)
- dj-database-url (database configuration)
- gunicorn (WSGI server)
- whitenoise (static files)

### Security Features
- CSRF protection enabled
- Custom user model with email uniqueness
- Superuser-restricted admin operations
- Login required for all views

## Development Workflow

### Adding New Features
1. Create/modify models in appropriate app
2. Generate migrations: `python manage.py makemigrations`
3. Apply migrations: `python manage.py migrate`
4. Update forms, views, and templates
5. Test with development server
6. Update admin interfaces if needed

### Model Changes
- Always create migrations after model modifications
- Test migrations on development database first
- Consider data migration for complex changes
- Update model documentation in technical guide

### Status and Approval Logic
The calling workflow includes complex approval states:
- Presidency approval tracking
- High Council approval for specific positions
- Bishop consultation requirements
- Automatic status updates based on approval completion

### Performance Considerations
- Use `select_related()` for foreign key relationships
- Implement database indexes for frequently queried fields
- Consider caching for dashboard statistics in production
- Limit querysets in list views (pagination implemented)

## Deployment Notes

### Production Configuration
- Set `DEBUG=False`
- Configure `ALLOWED_HOSTS`
- Use PostgreSQL database
- Collect static files with WhiteNoise
- Set proper `SECRET_KEY`

### Environment Variables Required
- `SECRET_KEY`: Django secret key
- `DEBUG`: Boolean for debug mode
- `DATABASE_URL`: Database connection string
- `ALLOWED_HOSTS`: Comma-separated host list

## Troubleshooting

### Common Issues
- **Migration conflicts**: Reset migrations in development
- **Static files not loading**: Run `collectstatic`
- **Database connection**: Check `DATABASE_URL` format
- **Permission errors**: Verify user is superuser for admin operations

### Debug Information
Enable Django debug toolbar in development by adding to `INSTALLED_APPS` and `MIDDLEWARE` when `DEBUG=True`.
