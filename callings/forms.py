from django import forms
from django.forms import ModelForm, DateInput
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Unit, Organization, Position, Calling

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
        fields = ['title', 'description', 'is_active', 'is_leadership', 'requires_setting_apart']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_leadership': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_setting_apart': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CallingForm(ModelForm):
    class Meta:
        model = Calling
        fields = [
            'name', 'unit', 'organization', 'position', 'status', 'date_called',
            'date_sustained', 'date_set_apart', 'date_released',
            'called_by', 'released_by', 'proposed_replacement', 'home_unit',
            'bishop_consulted_by', 'presidency_approved', 'hc_approved',
            'notes', 'is_active'
        ]
        widgets = {
            'date_called': DateInput(attrs={'type': 'date'}),
            'date_sustained': DateInput(attrs={'type': 'date'}),
            'date_set_apart': DateInput(attrs={'type': 'date'}),
            'date_released': DateInput(attrs={'type': 'date'}),
            'presidency_approved': DateInput(attrs={'type': 'date'}),
            'hc_approved': DateInput(attrs={'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['unit'].required = True
        self.fields['organization'].required = True
        self.fields['position'].required = True
        self.fields['date_called'].required = True
        
        # Set initial status if creating a new calling
        if not self.instance.pk:
            self.fields['status'].initial = 'IN_PROGRESS'
            
    def clean(self):
        cleaned_data = super().clean()
        date_called = cleaned_data.get('date_called')
        date_sustained = cleaned_data.get('date_sustained')
        date_set_apart = cleaned_data.get('date_set_apart')
        date_released = cleaned_data.get('date_released')
        
        # Validate date order
        if date_sustained and date_called and date_sustained < date_called:
            self.add_error('date_sustained', 'Sustained date cannot be before called date')
            
        if date_set_apart and date_sustained and date_set_apart < date_sustained:
            self.add_error('date_set_apart', 'Set apart date cannot be before sustained date')
            
        return cleaned_data

class CallingReleaseForm(ModelForm):
    class Meta:
        model = Calling
        fields = ['date_released', 'released_by', 'release_notes']
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
