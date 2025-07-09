from django import forms
from django.forms import ModelForm, DateInput
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Unit, Organization, Position, Member, Calling

class UnitForm(ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'unit_type', 'parent_unit', 'meeting_time', 'location', 'is_active']
        widgets = {
            'meeting_time': forms.TimeInput(attrs={'type': 'time'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_unit'].queryset = Unit.objects.exclude(id=self.instance.id)

class OrganizationForm(ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'unit', 'leader', 'description', 'is_active']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PositionForm(ModelForm):
    class Meta:
        model = Position
        fields = ['title', 'organization', 'description', 'is_active', 'is_leadership', 'requires_setting_apart']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_leadership': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_setting_apart': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class MemberForm(ModelForm):
    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'middle_name', 'suffix', 'gender',
            'birth_date', 'phone', 'address', 'city', 'state',
            'zip_code', 'membership_status', 'is_active'
        ]
        widgets = {
            'birth_date': DateInput(attrs={'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

class CallingForm(ModelForm):
    class Meta:
        model = Calling
        fields = [
            'member', 'position', 'unit', 'calling_status', 'date_called',
            'date_sustained', 'date_set_apart', 'date_released',
            'calling_approval_status', 'sustaining_approval_status',
            'setting_apart_approval_status', 'released_approval_status',
            'notes', 'is_active'
        ]
        widgets = {
            'date_called': DateInput(attrs={'type': 'date'}),
            'date_sustained': DateInput(attrs={'type': 'date'}),
            'date_set_apart': DateInput(attrs={'type': 'date'}),
            'date_released': DateInput(attrs={'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].required = True
        self.fields['position'].required = True
        self.fields['unit'].required = True
        self.fields['date_called'].required = True
        
        # Set initial status if creating a new calling
        if not self.instance.pk:
            self.fields['calling_status'].initial = 'ACTIVE'
            
    def clean(self):
        cleaned_data = super().clean()
        date_called = cleaned_data.get('date_called')
        date_sustained = cleaned_data.get('date_sustained')
        date_set_apart = cleaned_data.get('date_set_apart')
        date_released = cleaned_data.get('date_released')
        calling_status = cleaned_data.get('calling_status')
        
        # Validate date order
        if date_sustained and date_called and date_sustained < date_called:
            self.add_error('date_sustained', 'Sustained date cannot be before called date')
            
        if date_set_apart and date_sustained and date_set_apart < date_sustained:
            self.add_error('date_set_apart', 'Set apart date cannot be before sustained date')
            
        if date_released and date_called and date_released < date_called:
            self.add_error('date_released', 'Released date cannot be before called date')
            
        # Validate status based on dates
        if calling_status == 'ACTIVE' and date_released:
            self.add_error('calling_status', 'Active callings cannot have a release date')
            
        if calling_status == 'RELEASED' and not date_released:
            self.add_error('date_released', 'Released callings must have a release date')
            
        return cleaned_data

class CallingReleaseForm(ModelForm):
    class Meta:
        model = Calling
        fields = ['date_released', 'release_notes']
        widgets = {
            'date_released': DateInput(attrs={'type': 'date'}),
            'release_notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_released'].required = True
        self.fields['release_notes'].required = True

class CustomUserCreationForm(UserCreationForm):
    """
    A form that creates a user, with no privileges, from the given email and
    password. Also requires first and last name.
    """
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email', 'first_name', 'last_name')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        # Make password fields not required for admin add form
        if 'admin' in self.fields:
            self.fields['password1'].required = False
            self.fields['password2'].required = False
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        return user
