from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

# Use the custom User model
User = settings.AUTH_USER_MODEL

class Unit(models.Model):
    UNIT_TYPES = [
        ('WARD', 'Ward'),
        ('BRANCH', 'Branch'),
        ('STAKE', 'Stake'),
    ]
    
    name = models.CharField(max_length=100)
    unit_type = models.CharField(max_length=10, choices=UNIT_TYPES)
    parent_unit = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_units')
    meeting_time = models.TimeField(null=True, blank=True, help_text="Regular meeting time for this unit")
    location = models.CharField(max_length=200, blank=True, help_text="Physical location of the unit")
    is_active = models.BooleanField(default=True, help_text="Whether this unit is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_unit_type_display()})"
    
    def get_list_display(self):
        return [
            self.name,
            self.get_unit_type_display(),
            self.parent_unit.name if self.parent_unit else 'No Parent',
            self.meeting_time.strftime('%I:%M %p') if self.meeting_time else 'No Time Set',
            'Active' if self.is_active else 'Inactive'
        ]
    
    def get_absolute_url(self):
        return reverse('callings:unit-detail', kwargs={'pk': self.pk})


class Organization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='organizations', null=True, blank=True)
    leader = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Whether this organization is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def get_list_display(self):
        return [
            self.name,
            self.unit.name if self.unit else 'No Unit',
            self.leader or 'No Leader',
            'Active' if self.is_active else 'Inactive'
        ]
    
    def get_absolute_url(self):
        return reverse('callings:organization-detail', kwargs={'pk': self.pk})


class Position(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True, help_text="Description of the position's responsibilities")
    is_leadership = models.BooleanField(default=False, help_text="Whether this is a leadership position")
    is_active = models.BooleanField(default=True, help_text="Whether this position is currently active")
    requires_setting_apart = models.BooleanField(
        default=False, 
        help_text="Whether this position requires the member to be set apart"
    )
    display_order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Order in which positions should be displayed (lower numbers first)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'title']

    def __str__(self):
        return self.title
    
    def get_current_holder(self):
        """Get the current holder of this position"""
        active_calling = self.callings.filter(calling_status='ACTIVE', is_active=True).first()
        return active_calling.name if active_calling else None
    
    def get_list_display(self):
        current_holder = self.get_current_holder()
        return [
            self.title,
            current_holder or 'Vacant',
            'Active' if self.is_active else 'Inactive'
        ]
    
    def get_absolute_url(self):
        return reverse('callings:position-detail', kwargs={'pk': self.pk})



class Calling(models.Model):
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('ON_HOLD', 'On Hold'),
        ('LCR_UPDATED', 'LCR Updated'),
    ]
    
    CALLING_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('RELEASED', 'Released'),
        ('PENDING', 'Pending Approval'),
    ]
    
    APPROVAL_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('NOT_REQUIRED', 'Not Required'),
        ('DECLINED', 'Declined'),
    ]
    
    # Core relationships - all required
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='callings')
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='callings')
    position = models.ForeignKey(Position, on_delete=models.PROTECT, related_name='callings')
    name = models.CharField(max_length=200)
    
    # Status fields
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='IN_PROGRESS')
    calling_status = models.CharField(max_length=10, choices=CALLING_STATUS_CHOICES, default='ACTIVE')
    is_active = models.BooleanField(default=True, help_text="Whether this calling is currently active")
    
    # Date fields
    date_called = models.DateField(null=True, blank=True, default=None, help_text="Date when the calling was issued")
    date_sustained = models.DateField(null=True, blank=True, help_text="Date when the calling was sustained")
    date_set_apart = models.DateField(null=True, blank=True, help_text="Date when the member was set apart")
    date_released = models.DateField(null=True, blank=True, help_text="Date when the calling was released")
    
    # Approval status fields
    calling_approval_status = models.CharField(
        max_length=15, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='PENDING',
        help_text="Approval status of the calling"
    )
    sustaining_approval_status = models.CharField(
        max_length=15, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='NOT_REQUIRED',
        help_text="Approval status of the sustaining"
    )
    setting_apart_approval_status = models.CharField(
        max_length=15, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='NOT_REQUIRED',
        help_text="Approval status of the setting apart"
    )
    released_approval_status = models.CharField(
        max_length=15, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='NOT_REQUIRED',
        help_text="Approval status of the release"
    )
    
    # Approval details
    called_by = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Name of person who extended the calling"
    )
    released_by = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Name of person who released the calling"
    )
    proposed_replacement = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Name of the proposed replacement for this calling"
    )
    home_unit = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Home unit of the person (may differ from calling unit)"
    )
    presidency_approved = models.DateField(
        null=True, 
        blank=True,
        help_text="Date when the presidency approved the calling"
    )
    hc_approved = models.DateField(
        null=True, 
        blank=True,
        help_text="Date when the high council approved the calling"
    )
    bishop_consulted_by = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Name of bishop who was consulted for the calling"
    )
    
    # System fields
    lcr_updated = models.BooleanField(
        default=False,
        help_text="Whether this calling has been synced with LCR"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional notes about the calling"
    )
    release_notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Notes about the release of this calling"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_called']
        verbose_name_plural = 'Callings'

    def __str__(self):
        return f"{self.name} - {self.position} in {self.organization} ({self.unit})"

    def get_list_display(self):
        return [
            self.unit,
            self.organization,
            self.position,
            self.name,
            self.proposed_replacement or '',
            self.get_status_display()
        ]

    def get_absolute_url(self):
        return reverse('callings:calling-detail', kwargs={'pk': self.pk})
    
    def get_approval_status_class(self, approval_type):
        """Return CSS class for approval status badges"""
        status_map = {
            'calling': self.calling_approval_status,
            'sustaining': self.sustaining_approval_status,
            'setting_apart': self.setting_apart_approval_status,
            'released': self.released_approval_status,
        }
        
        status = status_map.get(approval_type, 'PENDING')
        
        class_map = {
            'PENDING': 'warning',
            'APPROVED': 'success',
            'NOT_REQUIRED': 'secondary',
            'DECLINED': 'danger',
        }
        
        return class_map.get(status, 'secondary')
    
    def get_status_badge_class(self):
        """Return CSS class for status badges"""
        status_map = {
            'IN_PROGRESS': 'primary',
            'COMPLETED': 'success',
            'CANCELLED': 'danger',
            'ON_HOLD': 'warning',
            'LCR_UPDATED': 'info',
        }
        return status_map.get(self.status, 'secondary')


class CallingHistory(models.Model):
    ACTION_CHOICES = [
        ('CALLED', 'Called'),
        ('RELEASED', 'Released'),
        ('UPDATED', 'Updated'),
    ]
    
    calling = models.ForeignKey(Calling, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    member_name = models.CharField(max_length=200, blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    # Store the state of the calling at the time of the change
    snapshot = models.JSONField()
    
    # Changed by field should reference the custom User model
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='changes_made')

    class Meta:
        verbose_name_plural = 'Calling History'
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.get_action_display()} - {self.calling} on {self.changed_at.strftime('%Y-%m-%d')}"
