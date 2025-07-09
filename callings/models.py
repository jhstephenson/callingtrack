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


class Organization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='organizations', null=True, blank=True)
    leader = models.ForeignKey('Member', on_delete=models.SET_NULL, null=True, blank=True, related_name='led_organizations')
    is_active = models.BooleanField(default=True, help_text="Whether this organization is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Position(models.Model):
    title = models.CharField(max_length=100)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='positions')
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
        unique_together = ['title', 'organization']

    def __str__(self):
        return f"{self.title} - {self.organization.name}"


class Member(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('', 'Prefer not to say'),
    ]
    
    MEMBERSHIP_STATUS_CHOICES = [
        ('MEMBER', 'Member'),
        ('NON_MEMBER', 'Non-Member'),
        ('PROSPECTIVE', 'Prospective Member'),
        ('OTHER', 'Other'),
    ]
    
    # Name fields
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    suffix = models.CharField(max_length=10, blank=True, null=True, help_text="e.g., Jr., Sr., III")
    
    # Personal information
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        blank=True, 
        null=True,
        help_text="Profile picture of the member"
    )
    
    # Contact information
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=15, blank=True, null=True)
    
    # Membership information
    home_unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    membership_status = models.CharField(
        max_length=20, 
        choices=MEMBERSHIP_STATUS_CHOICES, 
        default='MEMBER',
        help_text="Membership status in the church"
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="Whether this member is currently active in the unit"
    )
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['home_unit']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        name_parts = [self.first_name]
        if self.middle_name:
            name_parts.append(self.middle_name)
        name_parts.append(self.last_name)
        if self.suffix:
            name_parts.append(self.suffix)
        return ' '.join(name_parts)
        
    @property
    def full_name(self):
        """Return the full name of the member."""
        return str(self)
        
    @property
    def age(self):
        """Calculate and return the member's age based on birth date."""
        if not self.birth_date:
            return None
        today = timezone.now().date()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))


class Calling(models.Model):
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('ON_HOLD', 'On Hold'),
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
    
    # Core relationships
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='callings')
    position = models.ForeignKey(Position, on_delete=models.PROTECT, related_name='callings')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='callings')
    
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
    called_by = models.ForeignKey(
        Member, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='callings_made',
        help_text="Member who extended the calling"
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
    bishop_consulted_by = models.ForeignKey(
        Member, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='consulted_callings',
        help_text="Bishop who was consulted for the calling"
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
        return f"{self.member} - {self.position} in {self.unit}"

    def get_absolute_url(self):
        return reverse('calling-detail', kwargs={'pk': self.pk})


class CallingHistory(models.Model):
    ACTION_CHOICES = [
        ('CALLED', 'Called'),
        ('RELEASED', 'Released'),
        ('UPDATED', 'Updated'),
    ]
    
    calling = models.ForeignKey(Calling, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, related_name='calling_history')
    # Changed by field moved after the User model import
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
