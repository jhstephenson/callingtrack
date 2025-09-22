# CallingTrack - Project Plan

## Overview
This Django application is designed to track callings and releases within church units (wards, branches, stake). It provides a comprehensive web-based interface for managing the complete calling lifecycle from proposal to completion.

## Current Status (as of 2025-09-22)

### ✅ Completed Features
- [x] **Project setup and configuration** - Full Django 5.2.4 setup
- [x] **Django models created for:**
  - Unit (Wards, Branches, Stakes with hierarchical relationships)
  - Organization (Relief Society, Primary, etc.)
  - Position (specific callings with leadership flags)
  - Calling (comprehensive tracking with approval workflow)
  - CallingHistory (audit trail for changes)
  - Custom User model (extending AbstractUser)
- [x] **Complete web interface** - Full CRUD operations for all entities
- [x] **User authentication and authorization** - Login required, role-based access
- [x] **Dashboard** - Active callings overview with statistics and charts
- [x] **Advanced search and filtering** - Multi-field search across all calling data
- [x] **Status tracking system** - Complete workflow from Pending to LCR Updated
- [x] **Responsive design** - Bootstrap 5 interface for all devices
- [x] **Production deployment** - Heroku deployment with automatic migrations
- [x] **Documentation system** - Built-in user, admin, and technical guides
- [x] **Data management** - Import/export capabilities and database management
- [x] **LCR integration preparation** - Status tracking for external system sync

### 🚀 Recently Completed
- [x] **Approval workflow optimization** - Removed unused approval status fields
- [x] **Enhanced status choices** - Added HC_APPROVED for High Council workflow
- [x] **UI improvements** - Better navigation and status indicators
- [x] **Database optimization** - Cleaned up redundant fields and improved structure

## Data Model

### Current Model Structure
```mermaid
erDiagram
    USER ||--o{ CALLING_HISTORY : tracks_changes
    UNIT ||--o{ ORGANIZATION : contains
    UNIT ||--o{ CALLING : has
    ORGANIZATION ||--o{ CALLING : has
    POSITION ||--o{ CALLING : used_in
    CALLING ||--o{ CALLING_HISTORY : has_history
    
    USER {
        string username
        string email
        string first_name
        string last_name
        string phone
        bool is_staff
        bool is_superuser
    }
    
    UNIT {
        string name
        string unit_type
        FK parent_unit
        time meeting_time
        string location
        int sort_order
        bool is_active
        datetime created_at
        datetime updated_at
    }
    
    ORGANIZATION {
        string name
        text description
        FK unit
        string leader
        bool is_active
        datetime created_at
        datetime updated_at
    }
    
    POSITION {
        string title
        text description
        bool is_leadership
        bool requires_setting_apart
        int display_order
        bool is_active
        datetime created_at
        datetime updated_at
    }
    
    CALLING {
        FK unit
        FK organization
        FK position
        string name
        string status
        bool is_active
        date date_called
        date date_sustained
        date date_set_apart
        date date_released
        string called_by
        string released_by
        string proposed_replacement
        FK home_unit
        date presidency_approved
        date hc_approved
        string bishop_consulted_by
        bool lcr_updated
        text notes
        text release_notes
        datetime created_at
        datetime updated_at
    }
    
    CALLING_HISTORY {
        FK calling
        string action
        string member_name
        datetime changed_at
        text notes
        json snapshot
        FK changed_by
    }
```

### Status Workflow
```
PENDING → APPROVED (Stake Presidency) → HC_APPROVED (High Council) → CALLED → LCR_UPDATED
                                          ↓
                                      ON_HOLD (temporary pause)
```

## Project Structure
```
CallingTrack/
├── callings/               # Main app
│   ├── migrations/         # Database migrations
│   ├── admin.py           # Admin interface config
│   ├── models.py          # Data models
│   └── ...
├── callingtrack/          # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── venv/                  # Virtual environment
├── db.sqlite3             # Database file
└── manage.py              # Django management script
```

## Setup Instructions
1. Activate virtual environment:
   ```
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Mac/Linux
   ```

2. Install requirements:
   ```
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```
   python manage.py migrate
   ```

4. Create superuser:
   ```
   python manage.py createsuperuser
   ```

5. Run development server:
   ```
   python manage.py runserver
   ```

## Current Application Status

### Production Deployment
- **Live URL**: https://callingtrack-7e68d5e1da3a.herokuapp.com/
- **Database**: PostgreSQL (production), SQLite (development)
- **Admin interface**: Available at /admin/ with role-based access
- **Security**: HTTPS enabled, environment variables for secrets
- **Monitoring**: Automatic migrations via Heroku release process

### Key Features Available
- **Dashboard**: Real-time overview with active callings and statistics
- **Calling Management**: Complete CRUD operations with smart navigation
- **Search & Filter**: Multi-field search across all calling data
- **Status Tracking**: Comprehensive workflow from proposal to completion
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **User Management**: Authentication with role-based permissions
- **Documentation**: Built-in help system for users and administrators

## Future Enhancements

### Short Term (Next Release)
- [ ] **Enhanced reporting** - Export capabilities (PDF, CSV)
- [ ] **Notification system** - Email alerts for status changes
- [ ] **Bulk operations** - Mass status updates and data import
- [ ] **Advanced filtering** - Date range and multi-criteria filters

### Medium Term
- [ ] **Unit tests** - Comprehensive test coverage
- [ ] **REST API** - External integration capabilities
- [ ] **Audit logging** - Enhanced change tracking and reporting
- [ ] **Performance optimization** - Database indexing and query optimization

### Long Term
- [ ] **Mobile app** - Native iOS/Android applications
- [ ] **LCR integration** - Direct synchronization with church systems
- [ ] **Advanced analytics** - Trend analysis and predictive insights
- [ ] **Multi-language support** - Internationalization capabilities
