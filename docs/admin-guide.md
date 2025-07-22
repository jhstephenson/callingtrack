# Administrator Guide

## Overview

This guide is for system administrators responsible for setting up and maintaining CallingTrack.

## Initial Setup

### System Requirements
- Python 3.8 or higher
- Django 4.x
- Database (SQLite for development, PostgreSQL/MySQL for production)
- Web server (for production deployment)

### Installation Steps

1. **Server Preparation**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and dependencies
   sudo apt install python3 python3-pip python3-venv
   ```

2. **Application Installation**
   ```bash
   # Clone repository
   git clone https://github.com/jhstephenson/callingtrack.git
   cd CallingTrack
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Database Configuration**
   - For development: SQLite is configured by default
   - For production: Update `DATABASES` setting in settings.py

4. **Environment Variables**
   Create `.env` file with:
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com,www.your-domain.com
   DATABASE_URL=your-database-url
   ```

5. **Initial Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py collectstatic
   python manage.py createsuperuser
   ```

## User Management

### Creating Users
1. Access Django Admin: `/admin/`
2. Navigate to Users section
3. Click "Add User"
4. Provide username and password
5. Set permissions as needed

### User Permissions

**Superuser**: Full access to all features and admin interface
**Staff**: Can access admin interface with limited permissions
**Regular User**: Can use the application but not admin features

### Permission Groups (Recommended)

Create these groups for role-based access:
- **Stake Leadership**: Full calling management access
- **Bishopric**: Ward-specific calling access  
- **Clerk**: Read-only access with LCR update permissions
- **Viewer**: Read-only access

## Data Structure Setup

### Units
Set up your organizational structure:

1. **Stakes/Districts**: Top-level units
2. **Wards/Branches**: Local congregations
3. **Auxiliaries**: Supporting organizations

**Required Fields:**
- Name
- Unit Type (Stake, Ward, Branch, etc.)
- Sort Order (for display ordering)

### Organizations
Create organizations within units:

Examples:
- Bishopric
- Relief Society
- Young Men
- Young Women
- Primary
- Sunday School

### Positions
Define all calling positions:

**Important Settings:**
- **Requires Setting Apart**: Check for positions requiring setting apart
- **Is Leadership**: Mark leadership positions
- **Organization**: Associate with correct organization
- **Sort Order**: Control display order

## Configuration

### Application Settings

Key settings to configure:

```python
# settings.py

# Security
SECURE_SSL_REDIRECT = True  # For production
SECURE_HSTS_SECONDS = 31536000

# Email (for notifications if implemented)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-server'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Database backup
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'callingtrack_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Customization Options

#### Status Badge Colors
Modify in models.py `get_status_badge_class()` method:
- PENDING: 'info' (blue)
- APPROVED: 'success' (green)
- COMPLETED: 'success' (green)
- LCR_UPDATED: 'secondary' (gray)
- ON_HOLD: 'warning' (yellow)
- CANCELLED: 'danger' (red)

#### Dashboard Settings
- Active callings display limit (currently 15)
- Chart colors and styles
- Status definitions

## Backup and Maintenance

### Database Backups

**Daily Backup Script:**
```bash
#!/bin/bash
# backup-db.sh
DATE=$(date +%Y%m%d_%H%M%S)
python manage.py dumpdata > backups/callingtrack_$DATE.json
```

**Restore from Backup:**
```bash
python manage.py loaddata backup_file.json
```

### Maintenance Tasks

#### Weekly
- Review error logs
- Check disk space
- Verify backups

#### Monthly
- Update dependencies
- Review user access
- Clean up old data if needed

#### Security Updates
- Monitor Django security releases
- Update dependencies regularly
- Review user permissions

## Monitoring

### Key Metrics to Monitor
- User activity levels
- Calling completion rates
- System performance
- Error rates

### Log Files
Monitor these logs:
- Django application logs
- Web server logs (nginx/apache)
- Database logs
- System logs

## Troubleshooting

### Common Issues

**Migration Errors:**
```bash
# Reset migrations (development only)
python manage.py migrate callings zero
python manage.py makemigrations
python manage.py migrate
```

**Static Files Not Loading:**
```bash
python manage.py collectstatic --clear
```

**Database Connection Issues:**
- Check database server status
- Verify connection credentials
- Check firewall settings

**Performance Issues:**
- Review database query performance
- Check server resources (CPU, memory, disk)
- Consider database indexing

### Debug Mode
Enable debug mode for troubleshooting:
```python
# settings.py
DEBUG = True
```
**Warning:** Never enable DEBUG in production!

## Security Considerations

### Production Security Checklist
- [ ] DEBUG = False
- [ ] Secure secret key
- [ ] HTTPS enabled
- [ ] Regular security updates
- [ ] Strong passwords enforced
- [ ] Limited admin access
- [ ] Regular backups
- [ ] Firewall configured

### User Security
- Enforce strong password requirements
- Regular password changes
- Monitor user access logs
- Disable unused accounts

## Deployment

### Production Deployment

**Using Gunicorn and Nginx:**

1. **Install Gunicorn:**
   ```bash
   pip install gunicorn
   ```

2. **Create Systemd Service:**
   ```ini
   # /etc/systemd/system/callingtrack.service
   [Unit]
   Description=CallingTrack Django Application
   After=network.target
   
   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/CallingTrack
   Environment="PATH=/path/to/CallingTrack/venv/bin"
   ExecStart=/path/to/CallingTrack/venv/bin/gunicorn callingtrack.wsgi:application
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Nginx Configuration:**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location /static/ {
           alias /path/to/CallingTrack/staticfiles/;
       }
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Environment Management

Maintain separate environments:
- **Development**: Local development with DEBUG=True
- **Staging**: Production-like environment for testing
- **Production**: Live environment with DEBUG=False

## Support and Maintenance

### Regular Updates
1. Test updates in staging environment
2. Backup production data
3. Apply updates during maintenance windows
4. Verify functionality post-update

### User Support
- Maintain user documentation
- Provide training for new users
- Monitor support requests
- Document common issues and solutions

### Contact Information
Maintain documentation of:
- System administrators
- Hosting provider details
- Database administrator
- Emergency contacts
