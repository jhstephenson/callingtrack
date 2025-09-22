# Technical Documentation

## Architecture Overview

CallingTrack is built using Django 5.2.4 with a Model-View-Template (MVT) architecture.

### Technology Stack
- **Backend**: Django 5.2.4, Python 3.12+ (3.8+ supported)
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: Bootstrap 5.3.0, HTML5, JavaScript ES6
- **Charts**: Chart.js for dashboard analytics
- **Icons**: Font Awesome 6
- **Deployment**: Heroku with automatic migrations
- **Static Files**: WhiteNoise for production serving

### Project Structure
```
CallingTrack/
├── callingtrack/          # Django project settings
│   ├── settings.py        # Main configuration
│   ├── urls.py           # Root URL configuration
│   └── wsgi.py           # WSGI configuration
├── callings/             # Main Django app
│   ├── models.py         # Data models
│   ├── views.py          # View logic
│   ├── forms.py          # Form definitions
│   ├── urls.py           # App URL patterns
│   ├── admin.py          # Django admin configuration
│   └── templates/        # HTML templates
├── static/               # Static files (CSS, JS, images)
├── media/               # User uploaded files
└── docs/               # Documentation files
```

## Data Models

### Core Models

#### Unit
Represents organizational units (Stakes, Wards, Branches, etc.)
```python
class Unit(models.Model):
    name = models.CharField(max_length=100)
    unit_type = models.CharField(max_length=50)
    parent_unit = models.ForeignKey('self', null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    # ... additional fields
```

#### Organization
Represents organizations within units (Bishopric, Relief Society, etc.)
```python
class Organization(models.Model):
    name = models.CharField(max_length=100)
    unit = models.ForeignKey(Unit)
    leader_position = models.CharField(max_length=100)
    sort_order = models.IntegerField(default=0)
    # ... additional fields
```

#### Position
Defines specific calling positions
```python
class Position(models.Model):
    title = models.CharField(max_length=100)
    organization = models.ForeignKey(Organization)
    requires_setting_apart = models.BooleanField(default=False)
    is_leadership = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    # ... additional fields
```

#### Calling
Main model for tracking individual callings
```python
class Calling(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Stake Presidency Approved'),
        ('HC_APPROVED', 'High Council Approved'),
        ('ON_HOLD', 'On Hold'),
        ('CALLED', 'Called'),
        ('LCR_UPDATED', 'LCR Updated'),
    ]
    
    # Core relationships
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    position = models.ForeignKey(Position, on_delete=models.PROTECT)
    
    # Member information
    name = models.CharField(max_length=200, blank=True, null=True)
    proposed_replacement = models.CharField(max_length=200, blank=True, null=True)
    home_unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status and dates
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='PENDING')
    date_called = models.DateField(null=True, blank=True)
    date_sustained = models.DateField(null=True, blank=True)
    date_set_apart = models.DateField(null=True, blank=True)
    date_released = models.DateField(null=True, blank=True)
    
    # Approval tracking (date-based)
    presidency_approved = models.DateField(null=True, blank=True)
    hc_approved = models.DateField(null=True, blank=True)
    bishop_consulted_by = models.CharField(max_length=200, blank=True, null=True)
    
    # System fields
    lcr_updated = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    # ... additional fields
```

### Model Relationships
- **Unit** → **Organization** (One-to-Many)
- **Organization** → **Position** (One-to-Many)
- **Unit/Organization/Position** → **Calling** (Foreign Keys)

### Key Model Methods

#### Calling.get_status_badge_class()
Returns Bootstrap CSS class for status badges:
```python
def get_status_badge_class(self):
    status_map = {
        'PENDING': 'warning',
        'APPROVED': 'success',
        'HC_APPROVED': 'success', 
        'CALLED': 'success',
        'LCR_UPDATED': 'info',
        'ON_HOLD': 'warning',
    }
    return status_map.get(self.status, 'secondary')
```

**Note**: Removed CANCELLED and COMPLETED statuses in recent model updates

#### Calling.get_absolute_url()
Returns the canonical URL for a calling detail view:
```python
def get_absolute_url(self):
    return reverse('callings:calling-detail', kwargs={'pk': self.pk})
```

## View Architecture

### View Types Used

#### Function-Based Views
- `dashboard`: Main dashboard with active callings overview

#### Class-Based Views
- **ListView**: For listing callings, units, organizations, positions
- **DetailView**: For viewing individual items
- **CreateView**: For creating new items
- **UpdateView**: For editing existing items
- **DeleteView**: For removing items

### Key Views

#### CallingUpdateView
Handles calling edit form with smart return navigation:
```python
class CallingUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, UpdateView):
    def get_return_url(self, referer):
        # Logic to determine where to redirect after editing
        if 'dashboard' in referer:
            return reverse_lazy('dashboard')
        elif 'status=active' in referer:
            return reverse_lazy('callings:callings-by-unit') + '?status=active'
        # ... more conditions
```

#### Dashboard View
Central hub showing active callings and statistics:
```python
@login_required
def dashboard(request):
    active_callings = Calling.objects.exclude(
        status__in=['COMPLETED', 'LCR_UPDATED', 'CANCELLED']
    ).select_related('position', 'unit', 'organization')[:15]
    # ... additional context
```

### Mixins Used

#### LoginRequiredMixin
Ensures user authentication for all views

#### SuperuserRequiredMixin
Custom mixin restricting access to superusers:
```python
class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser
```

#### TitleMixin
Provides consistent page titles:
```python
class TitleMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.get_title()
        return context
```

## URL Configuration

### URL Patterns
```python
urlpatterns = [
    # Dashboard
    path('', dashboard, name='dashboard'),
    
    # Callings
    path('callings/', CallingListView.as_view(), name='calling-list'),
    path('callings/by-unit/', CallingsByUnitView.as_view(), name='callings-by-unit'),
    path('callings/<int:pk>/', CallingDetailView.as_view(), name='calling-detail'),
    path('callings/<int:pk>/update/', CallingUpdateView.as_view(), name='calling-update'),
    
    # Units, Organizations, Positions...
]
```

### URL Naming Convention
- List views: `{model}-list`
- Detail views: `{model}-detail`
- Create views: `{model}-create`
- Update views: `{model}-update`
- Delete views: `{model}-delete`

## Forms

### CallingForm
Main form for creating/editing callings:
```python
class CallingForm(forms.ModelForm):
    class Meta:
        model = Calling
        fields = [
            'unit', 'organization', 'position', 'status',
            'name', 'proposed_replacement', 'date_called',
            'date_sustained', 'date_set_apart', 'notes'
        ]
        widgets = {
            'date_called': forms.DateInput(attrs={'type': 'date'}),
            'date_sustained': forms.DateInput(attrs={'type': 'date'}),
            'date_set_apart': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }
```

## Templates

### Template Structure
```
templates/
├── callings/
│   ├── base.html              # Base template
│   ├── dashboard.html         # Dashboard
│   ├── calling/
│   │   ├── calling_list.html
│   │   ├── callings_by_unit.html
│   │   ├── calling_detail.html
│   │   └── calling_form.html
│   ├── unit/
│   ├── organization/
│   └── position/
└── registration/              # Auth templates
```

### Template Context

#### Dashboard Context
```python
context = {
    'title': 'Dashboard',
    'total_callings': int,
    'active_callings_count': int,
    'active_callings': QuerySet,
    'calling_status_data': list,
}
```

#### List View Context
```python
context = {
    'callings': QuerySet,
    'current_status': str,
    'current_search': str,
    'active_count': int,
    'all_count': int,
}
```

### JavaScript Integration

#### Chart.js Implementation
```javascript
const statusData = {
    labels: data.map(item => statusMap[item.status] || item.status),
    datasets: [{
        data: data.map(item => item.count),
        backgroundColor: ['rgba(54, 162, 235, 0.7)', ...],
    }]
};

new Chart(ctx, {
    type: 'doughnut',
    data: statusData,
    options: { responsive: true }
});
```

## Database Queries

### Query Optimization

#### Select Related
Used to avoid N+1 queries:
```python
callings = Calling.objects.select_related(
    'position', 'unit', 'organization'
).filter(status='PENDING')
```

#### Queryset Filtering
```python
# Active callings definition
active_callings = Calling.objects.exclude(
    status__in=['COMPLETED', 'LCR_UPDATED', 'CANCELLED']
)

# Search functionality
search_results = Calling.objects.filter(
    Q(name__icontains=search) |
    Q(position__title__icontains=search) |
    Q(organization__name__icontains=search)
)
```

## Authentication & Authorization

### Authentication Backend
Uses Django's built-in authentication system

### Permission System
- Superuser: Full access
- Staff: Limited admin access
- Regular users: Application access only

### Login Required
All views require authentication via `@login_required` or `LoginRequiredMixin`

## Static Files

### CSS Framework
- Bootstrap 5 for responsive design
- Custom CSS in `static/css/styles.css`

### JavaScript Libraries
- Bootstrap 5 JS for interactive components
- Chart.js for dashboard charts
- Font Awesome for icons

### Static File Handling
```python
# settings.py
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

## Deployment Considerations

### Environment Variables
```python
import os
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')
```

### Database Configuration
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
```

### Security Settings
```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

## Testing

### Test Structure (Recommended)
```
tests/
├── test_models.py
├── test_views.py
├── test_forms.py
└── test_utils.py
```

### Sample Tests
```python
class CallingModelTest(TestCase):
    def test_status_badge_class(self):
        calling = Calling(status='PENDING')
        self.assertEqual(calling.get_status_badge_class(), 'info')
        
    def test_active_callings_queryset(self):
        # Test active calling definition
        pass
```

## API Considerations

### Future REST API
If REST API is needed, consider Django REST Framework:
```python
# serializers.py
class CallingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calling
        fields = '__all__'
```

## Performance Optimization

### Database Indexing
```python
class Calling(models.Model):
    status = models.CharField(max_length=20, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
```

### Caching (Future Enhancement)
```python
from django.core.cache import cache

def get_active_callings_count():
    count = cache.get('active_callings_count')
    if count is None:
        count = Calling.objects.exclude(
            status__in=['COMPLETED', 'LCR_UPDATED', 'CANCELLED']
        ).count()
        cache.set('active_callings_count', count, 300)  # 5 minutes
    return count
```

## Development Workflow

### Local Development
```bash
python manage.py runserver
```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files
```bash
python manage.py collectstatic
```

## Troubleshooting

### Common Development Issues

#### Migration Problems
```bash
# Reset migrations (development only)
python manage.py migrate callings zero
rm callings/migrations/0*.py
python manage.py makemigrations
python manage.py migrate
```

#### Static Files Issues
```bash
python manage.py collectstatic --clear --noinput
```

#### Debug Information
Enable debug toolbar for development:
```python
if DEBUG:
    import debug_toolbar
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
```
