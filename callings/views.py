from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView
)
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models.functions import TruncMonth
from django.db.models import Count, F, Value, CharField
from django.db.models.functions import Concat

from .models import Unit, Organization, Position, Member, Calling
from .forms import (
    UnitForm, OrganizationForm, PositionForm, 
    MemberForm, CallingForm, CallingReleaseForm
)

# Mixin to check if user is superuser
class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

# Mixin to add page title to context
class TitleMixin:
    title = None

    def get_title(self):
        return self.title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.get_title()
        return context

# Dashboard View
@login_required
def dashboard(request):
    """
    Dashboard view showing recent callings, statistics, and upcoming events.
    """
    from django.apps import apps
    
    context = {
        'title': 'Dashboard',
    }
    
    # Get recent callings for the current user's unit
    recent_callings = Calling.objects.select_related('member', 'position', 'unit')
    
    # If user has specific units assigned, filter by those
    if hasattr(request.user, 'units'):
        recent_callings = recent_callings.filter(unit__in=request.user.units.all())
    
    # Get counts for dashboard cards
    context['total_units'] = Unit.objects.count()
    context['total_members'] = Member.objects.count()
    context['total_callings'] = Calling.objects.filter(is_active=True).count()
    context['active_callings'] = Calling.objects.filter(calling_status='ACTIVE').count()
    context['recent_callings'] = recent_callings.order_by('-date_called')[:10]
    
    # Get upcoming events (next 30 days)
    today = timezone.now().date()
    thirty_days_later = today + timedelta(days=30)
    
    # Upcoming releases
    context['upcoming_releases'] = Calling.objects.filter(
        date_released__isnull=False,
        date_released__gte=today,
        date_released__lte=thirty_days_later,
        is_active=True
    ).select_related('member', 'position').order_by('date_released')[:10]
    
    # Upcoming callings and other events
    context['upcoming_callings'] = Calling.objects.filter(
        Q(date_called__range=[today, thirty_days_later]) |
        Q(date_sustained__range=[today, thirty_days_later]) |
        Q(date_set_apart__range=[today, thirty_days_later])
    ).select_related('member', 'position', 'unit').order_by('date_called')[:5]
    
    # Get calling statistics by status
    context['calling_status_stats'] = (
        Calling.objects.values('calling_status')
        .annotate(count=Count('calling_status'))
        .order_by('-count')
    )
    
    # For the chart
    context['calling_status_data'] = list(Calling.objects.values('calling_status')
        .annotate(count=Count('id')))
    
    # Get recent activities (last 10 changes)
    if 'callings.CallingHistory' in [model._meta.label for model in apps.get_models()]:
        from .models import CallingHistory
        context['recent_activities'] = (
            CallingHistory.objects
            .select_related('calling', 'changed_by')
            .order_by('-changed_at')[:10]
        )
    
    return render(request, 'callings/dashboard.html', context)

# Unit Views
class UnitListView(LoginRequiredMixin, TitleMixin, ListView):
    model = Unit
    template_name = 'callings/unit_list.html'
    context_object_name = 'units'
    title = 'Units'
    paginate_by = 20

class UnitDetailView(LoginRequiredMixin, TitleMixin, DetailView):
    model = Unit
    template_name = 'callings/unit_detail.html'
    context_object_name = 'unit'

    def get_title(self):
        return f"Unit: {self.get_object().name}"

class UnitCreateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, CreateView):
    model = Unit
    form_class = UnitForm
    template_name = 'callings/unit_form.html'
    title = 'Create Unit'
    success_url = reverse_lazy('unit-list')

class UnitUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, UpdateView):
    model = Unit
    form_class = UnitForm
    template_name = 'callings/unit_form.html'
    
    def get_title(self):
        return f"Update Unit: {self.get_object().name}"
    
    def get_success_url(self):
        return reverse_lazy('unit-detail', kwargs={'pk': self.object.pk})

class UnitDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, DeleteView):
    model = Unit
    template_name = 'callings/unit_confirm_delete.html'
    success_url = reverse_lazy('unit-list')
    
    def get_title(self):
        return f"Delete Unit: {self.get_object().name}"

# Organization Views
class OrganizationListView(LoginRequiredMixin, TitleMixin, ListView):
    model = Organization
    template_name = 'callings/organization_list.html'
    context_object_name = 'organizations'
    title = 'Organizations'
    paginate_by = 20

class OrganizationDetailView(LoginRequiredMixin, TitleMixin, DetailView):
    model = Organization
    template_name = 'callings/organization_detail.html'
    context_object_name = 'organization'

    def get_title(self):
        return f"Organization: {self.get_object().name}"

class OrganizationCreateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, CreateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'callings/organization_form.html'
    title = 'Create Organization'
    success_url = reverse_lazy('organization-list')

class OrganizationUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, UpdateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'callings/organization_form.html'
    
    def get_title(self):
        return f"Update Organization: {self.get_object().name}"
    
    def get_success_url(self):
        return reverse_lazy('organization-detail', kwargs={'pk': self.object.pk})

class OrganizationDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, DeleteView):
    model = Organization
    template_name = 'callings/organization_confirm_delete.html'
    success_url = reverse_lazy('organization-list')
    
    def get_title(self):
        return f"Delete Organization: {self.get_object().name}"

# Position Views
class PositionListView(LoginRequiredMixin, TitleMixin, ListView):
    model = Position
    template_name = 'callings/position_list.html'
    context_object_name = 'positions'
    title = 'Positions'
    paginate_by = 20

class PositionDetailView(LoginRequiredMixin, TitleMixin, DetailView):
    model = Position
    template_name = 'callings/position_detail.html'
    context_object_name = 'position'

    def get_title(self):
        return f"Position: {self.get_object().title}"

class PositionCreateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, CreateView):
    model = Position
    form_class = PositionForm
    template_name = 'callings/position_form.html'
    title = 'Create Position'
    success_url = reverse_lazy('position-list')

class PositionUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, UpdateView):
    model = Position
    form_class = PositionForm
    template_name = 'callings/position_form.html'
    
    def get_title(self):
        return f"Update Position: {self.get_object().title}"
    
    def get_success_url(self):
        return reverse_lazy('position-detail', kwargs={'pk': self.object.pk})

class PositionDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, DeleteView):
    model = Position
    template_name = 'callings/position_confirm_delete.html'
    success_url = reverse_lazy('position-list')
    
    def get_title(self):
        return f"Delete Position: {self.get_object().title}"

# Member Views
class MemberListView(LoginRequiredMixin, TitleMixin, ListView):
    model = Member
    template_name = 'callings/member_list.html'
    context_object_name = 'members'
    title = 'Members'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            return queryset.filter(
                Q(name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query)
            )
        return queryset

class MemberDetailView(LoginRequiredMixin, TitleMixin, DetailView):
    model = Member
    template_name = 'callings/member_detail.html'
    context_object_name = 'member'

    def get_title(self):
        return f"Member: {self.get_object().name}"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_callings'] = self.object.callings.filter(calling_status='ACTIVE')
        context['past_callings'] = self.object.callings.exclude(calling_status='ACTIVE')
        return context

class MemberCreateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, CreateView):
    model = Member
    form_class = MemberForm
    template_name = 'callings/member_form.html'
    title = 'Create Member'
    success_url = reverse_lazy('member-list')

class MemberUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, UpdateView):
    model = Member
    form_class = MemberForm
    template_name = 'callings/member_form.html'
    
    def get_title(self):
        return f"Update Member: {self.get_object().name}"
    
    def get_success_url(self):
        return reverse_lazy('member-detail', kwargs={'pk': self.object.pk})

class MemberDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, DeleteView):
    model = Member
    template_name = 'callings/member_confirm_delete.html'
    success_url = reverse_lazy('member-list')
    
    def get_title(self):
        return f"Delete Member: {self.get_object().name}"

# Calling Views
class CallingListView(LoginRequiredMixin, TitleMixin, ListView):
    model = Calling
    template_name = 'callings/calling_list.html'
    context_object_name = 'callings'
    title = 'Callings'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('member', 'position', 'unit')
        status = self.request.GET.get('status')
        
        if status == 'active':
            queryset = queryset.filter(calling_status='ACTIVE')
        elif status == 'released':
            queryset = queryset.filter(calling_status='RELEASED')
        elif status == 'pending':
            queryset = queryset.filter(calling_status='PENDING')
        
        return queryset.order_by('-date_called')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_count'] = self.get_queryset().filter(calling_status='ACTIVE').count()
        context['released_count'] = self.get_queryset().filter(calling_status='RELEASED').count()
        context['pending_count'] = self.get_queryset().filter(calling_status='PENDING').count()
        return context

class CallingDetailView(LoginRequiredMixin, TitleMixin, DetailView):
    model = Calling
    template_name = 'callings/calling_detail.html'
    context_object_name = 'calling'

    def get_title(self):
        return f"Calling: {self.get_object().position.title}"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['release_form'] = CallingReleaseForm(instance=self.object)
        return context

class CallingCreateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, CreateView):
    model = Calling
    form_class = CallingForm
    template_name = 'callings/calling_form.html'
    title = 'Create Calling'
    success_url = reverse_lazy('calling-list')

class CallingUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, UpdateView):
    model = Calling
    form_class = CallingForm
    template_name = 'callings/calling_form.html'
    
    def get_title(self):
        return f"Update Calling: {self.get_object().position.title}"
    
    def get_success_url(self):
        return reverse_lazy('calling-detail', kwargs={'pk': self.object.pk})

class CallingDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, DeleteView):
    model = Calling
    template_name = 'callings/calling_confirm_delete.html'
    success_url = reverse_lazy('calling-list')
    
    def get_title(self):
        return f"Delete Calling: {self.get_object().position.title}"

class CallingReleaseView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, UpdateView):
    model = Calling
    form_class = CallingReleaseForm
    template_name = 'callings/calling_release.html'
    
    def get_title(self):
        return f"Release Calling: {self.get_object().position.title}"
    
    def form_valid(self, form):
        form.instance.calling_status = 'RELEASED'
        form.instance.date_released = timezone.now().date()
        messages.success(self.request, 'Calling has been released successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('calling-detail', kwargs={'pk': self.object.pk})

# Profile View
@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, 
            request.FILES, 
            instance=request.user.profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    
    return render(request, 'callings/profile.html', context)
