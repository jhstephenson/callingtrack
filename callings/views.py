from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView, View
)
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models.functions import TruncMonth
from django.db.models import Count, F, Value, CharField
from django.db.models.functions import Concat
from django.http import HttpResponse, Http404
import os
from django.conf import settings

from .models import Unit, Organization, Position, Calling
from .forms import (
    UnitForm, OrganizationForm, PositionForm, 
    CallingForm, CallingReleaseForm
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

# Mixin to add sortable functionality to list views
class SortableMixin:
    sortable_fields = {}
    default_sort = None
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply sorting
        sort_field = self.request.GET.get('sort')
        sort_order = self.request.GET.get('order', 'asc')
        
        if sort_field and sort_field in self.sortable_fields:
            order_field = self.sortable_fields[sort_field]
            if sort_order == 'desc':
                order_field = f'-{order_field}'
            return queryset.order_by(order_field)
        
        # Apply default sort if specified
        if self.default_sort:
            return queryset.order_by(self.default_sort)
            
        return queryset

# Dashboard View
@login_required
def dashboard(request):
    """
    Dashboard view showing active callings and statistics.
    """
    from django.apps import apps
    
    context = {
        'title': 'Dashboard',
    }
    
    # Get active callings (not COMPLETED, LCR_UPDATED, or CANCELLED)
    active_callings_queryset = Calling.objects.exclude(
        status__in=['COMPLETED', 'LCR_UPDATED', 'CANCELLED']
    ).select_related('position', 'unit', 'organization')
    
    # If user has specific units assigned, filter by those
    if hasattr(request.user, 'units'):
        active_callings_queryset = active_callings_queryset.filter(unit__in=request.user.units.all())
    
    # Get counts for dashboard cards
    context['total_units'] = Unit.objects.count()
    context['total_callings'] = Calling.objects.count()
    context['active_callings_count'] = active_callings_queryset.count()
    
    # Get active callings for display (limit to 15)
    context['active_callings'] = active_callings_queryset.order_by(
        'unit__sort_order', 'unit__name', 'organization__name', 'position__title'
    )[:15]
    
    # Get calling statistics by status
    context['calling_status_stats'] = (
        Calling.objects.values('status')
        .annotate(count=Count('status'))
        .order_by('-count')
    )
    
    # For the chart
    context['calling_status_data'] = list(Calling.objects.values('status')
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

# Documentation Views

class UserGuideView(LoginRequiredMixin, TitleMixin, TemplateView):
    template_name = 'callings/docs/user-guide.html'
    title = 'User Guide'

class AdminGuideView(LoginRequiredMixin, TitleMixin, TemplateView):
    template_name = 'callings/docs/admin-guide.html'
    title = 'Administrator Guide'

class TechnicalGuideView(LoginRequiredMixin, TitleMixin, TemplateView):
    template_name = 'callings/docs/technical-guide.html'
    title = 'Technical Documentation'

# Unit Views
class UnitListView(LoginRequiredMixin, TitleMixin, SortableMixin, ListView):
    model = Unit
    template_name = 'callings/unit/unit_list.html'
    context_object_name = 'units'
    title = 'Units'
    paginate_by = 20
    default_sort = 'sort_order'
    sortable_fields = {
        'name': 'name',
        'unit_type': 'unit_type', 
        'parent_unit': 'parent_unit__name',
        'meeting_time': 'meeting_time',
        'is_active': 'is_active',
        'sort_order': 'sort_order',
    }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['headers'] = ['Name', 'Type', 'Parent Unit', 'Meeting Time', 'Status']
        context['sortable_headers'] = [
            ('name', 'Name'),
            ('unit_type', 'Type'),
            ('parent_unit', 'Parent Unit'),
            ('meeting_time', 'Meeting Time'),
            ('is_active', 'Status'),
        ]
        return context

class UnitDetailView(LoginRequiredMixin, TitleMixin, DetailView):
    model = Unit
    template_name = 'callings/unit/unit_detail.html'
    context_object_name = 'unit'

    def get_title(self):
        return f"Unit: {self.get_object().name}"

class UnitCreateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, CreateView):
    model = Unit
    form_class = UnitForm
    template_name = 'callings/unit/unit_form.html'
    title = 'Create Unit'
    
    def get_success_url(self):
        return reverse_lazy('callings:unit-detail', kwargs={'pk': self.object.pk})

class UnitUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, UpdateView):
    model = Unit
    form_class = UnitForm
    template_name = 'callings/unit/unit_form.html'
    
    def get_title(self):
        return f"Update Unit: {self.get_object().name}"
    
    def get_success_url(self):
        return reverse_lazy('callings:unit-list')

class UnitDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, DeleteView):
    model = Unit
    template_name = 'callings/unit/unit_confirm_delete.html'
    success_url = reverse_lazy('callings:unit-list')
    
    def get_title(self):
        return f"Delete Unit: {self.get_object().name}"

# Organization Views
class OrganizationListView(LoginRequiredMixin, TitleMixin, ListView):
    model = Organization
    template_name = 'callings/organization/organization_list.html'
    context_object_name = 'organizations'
    title = 'Organizations'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['headers'] = ['Name', 'Unit', 'Leader', 'Status']
        return context

class OrganizationDetailView(LoginRequiredMixin, TitleMixin, DetailView):
    model = Organization
    template_name = 'callings/organization/organization_detail.html'
    context_object_name = 'organization'

    def get_title(self):
        return f"Organization: {self.get_object().name}"

class OrganizationCreateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, CreateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'callings/organization/organization_form.html'
    title = 'Create Organization'
    
    def get_success_url(self):
        return reverse_lazy('callings:organization-detail', kwargs={'pk': self.object.pk})

class OrganizationUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, UpdateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'callings/organization/organization_form.html'
    
    def get_title(self):
        return f"Update Organization: {self.get_object().name}"
    
    def get_success_url(self):
        return reverse_lazy('callings:organization-list')

class OrganizationDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, DeleteView):
    model = Organization
    template_name = 'callings/organization/organization_confirm_delete.html'
    success_url = reverse_lazy('callings:organization-list')
    
    def get_title(self):
        return f"Delete Organization: {self.get_object().name}"

# Position Views
class PositionListView(LoginRequiredMixin, TitleMixin, ListView):
    model = Position
    template_name = 'callings/position/position_list.html'
    context_object_name = 'positions'
    title = 'Positions'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['headers'] = ['Title', 'Current Holder', 'Status']
        return context

class PositionDetailView(LoginRequiredMixin, TitleMixin, DetailView):
    model = Position
    template_name = 'callings/position/position_detail.html'
    context_object_name = 'position'

    def get_title(self):
        return f"Position: {self.get_object().title}"

class PositionCreateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, CreateView):
    model = Position
    form_class = PositionForm
    template_name = 'callings/position/position_form.html'
    title = 'Create Position'
    
    def get_success_url(self):
        return reverse_lazy('callings:position-detail', kwargs={'pk': self.object.pk})

class PositionUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, UpdateView):
    model = Position
    form_class = PositionForm
    template_name = 'callings/position/position_form.html'
    
    def get_title(self):
        return f"Update Position: {self.get_object().title}"
    
    def get_success_url(self):
        return reverse_lazy('callings:position-list')

class PositionDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, DeleteView):
    model = Position
    template_name = 'callings/position/position_confirm_delete.html'
    success_url = reverse_lazy('callings:position-list')
    
    def get_title(self):
        return f"Delete Position: {self.get_object().title}"

# Calling Views
class CallingListView(LoginRequiredMixin, TitleMixin, ListView):
    model = Calling
    template_name = 'callings/calling/calling_list.html'
    context_object_name = 'callings'
    title = 'All Callings'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('position', 'organization', 'unit')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(position__title__icontains=search) |
                Q(organization__name__icontains=search) |
                Q(unit__name__icontains=search) |
                Q(proposed_replacement__icontains=search)
            )
        
        # Status filtering
        status_filter = self.request.GET.get('status')
        
        if status_filter == 'pending':
            queryset = queryset.filter(status='PENDING')
        elif status_filter == 'approved':
            queryset = queryset.filter(status='APPROVED')
        elif status_filter == 'completed':
            queryset = queryset.filter(status='COMPLETED')
        elif status_filter == 'lcr_updated':
            queryset = queryset.filter(status='LCR_UPDATED')
        elif status_filter == 'cancelled':
            queryset = queryset.filter(status='CANCELLED')
        elif status_filter == 'on_hold':
            queryset = queryset.filter(status='ON_HOLD')
        elif status_filter == 'active':
            # Active calling is any calling not marked as COMPLETED, LCR_UPDATED, or CANCELLED
            queryset = queryset.exclude(status__in=['COMPLETED', 'LCR_UPDATED', 'CANCELLED'])
        elif status_filter == 'all':
            # Show all callings
            pass
        else:
            # Default: show all callings
            pass
        
        # Apply sorting
        sort_field = self.request.GET.get('sort')
        sort_order = self.request.GET.get('order', 'asc')
        
        if sort_field:
            # Map frontend field names to model fields
            sort_mapping = {
                'unit': 'unit__name',
                'organization': 'organization__name', 
                'position': 'position__title',
                'name': 'name',
                'proposed_replacement': 'proposed_replacement',
                'status': 'status',
                'created_at': 'created_at',
                'date_called': 'date_called',
                'date_sustained': 'date_sustained',
                'date_set_apart': 'date_set_apart',
            }
            
            if sort_field in sort_mapping:
                order_field = sort_mapping[sort_field]
                if sort_order == 'desc':
                    order_field = f'-{order_field}'
                return queryset.order_by(order_field)
        
        # Default ordering
        return queryset.order_by('unit__sort_order', 'unit__name', 'organization__name', 'position__title')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all callings for counts (before filtering)
        all_callings = Calling.objects.select_related('position', 'organization', 'unit')
        
        # Apply search to counts if search is active
        search = self.request.GET.get('search')
        if search:
            all_callings = all_callings.filter(
                Q(name__icontains=search) |
                Q(position__title__icontains=search) |
                Q(organization__name__icontains=search) |
                Q(unit__name__icontains=search) |
                Q(proposed_replacement__icontains=search)
            )
        
        # Status counts
        context['pending_count'] = all_callings.filter(status='PENDING').count()
        context['approved_count'] = all_callings.filter(status='APPROVED').count()
        context['completed_count'] = all_callings.filter(status='COMPLETED').count()
        context['lcr_updated_count'] = all_callings.filter(status='LCR_UPDATED').count()
        context['cancelled_count'] = all_callings.filter(status='CANCELLED').count()
        context['on_hold_count'] = all_callings.filter(status='ON_HOLD').count()
        # Use new Active definition: not COMPLETED, LCR_UPDATED, or CANCELLED
        context['active_count'] = all_callings.exclude(status__in=['COMPLETED', 'LCR_UPDATED', 'CANCELLED']).count()
        context['all_count'] = all_callings.count()
        
        # Current filter for template
        context['current_status'] = self.request.GET.get('status', 'all')
        context['current_search'] = search or ''
        
        context['headers'] = ['Unit', 'Organization', 'Position', 'Currently Serving', 'Proposed Replacement', 'Status']
        return context

class CallingsByUnitView(LoginRequiredMixin, TitleMixin, ListView):
    model = Calling
    template_name = 'callings/calling/callings_by_unit.html'
    context_object_name = 'callings'
    title = 'Callings by Unit'
    paginate_by = None  # Show all for grouping
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('position', 'organization', 'unit')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(position__title__icontains=search) |
                Q(organization__name__icontains=search) |
                Q(unit__name__icontains=search) |
                Q(proposed_replacement__icontains=search)
            )
        
        # Status filtering (same logic as main list)
        status_filter = self.request.GET.get('status')
        
        if status_filter == 'pending':
            queryset = queryset.filter(status='PENDING')
        elif status_filter == 'approved':
            queryset = queryset.filter(status='APPROVED')
        elif status_filter == 'completed':
            queryset = queryset.filter(status='COMPLETED')
        elif status_filter == 'lcr_updated':
            queryset = queryset.filter(status='LCR_UPDATED')
        elif status_filter == 'cancelled':
            queryset = queryset.filter(status='CANCELLED')
        elif status_filter == 'on_hold':
            queryset = queryset.filter(status='ON_HOLD')
        elif status_filter == 'active':
            # Active calling is any calling not marked as COMPLETED, LCR_UPDATED, or CANCELLED
            queryset = queryset.exclude(status__in=['COMPLETED', 'LCR_UPDATED', 'CANCELLED'])
        elif status_filter == 'all':
            pass
        else:
            # Default: show all callings
            pass
        
        # Apply sorting
        sort_field = self.request.GET.get('sort')
        sort_order = self.request.GET.get('order', 'asc')
        
        if sort_field:
            # Map frontend field names to model fields
            sort_mapping = {
                'organization': 'organization__name', 
                'position': 'position__title',
                'name': 'name',
                'proposed_replacement': 'proposed_replacement',
                'status': 'status',
                'created_at': 'created_at',
                'date_called': 'date_called',
                'date_sustained': 'date_sustained',
                'date_set_apart': 'date_set_apart',
            }
            
            if sort_field in sort_mapping:
                order_field = sort_mapping[sort_field]
                if sort_order == 'desc':
                    order_field = f'-{order_field}'
                return queryset.order_by('unit__sort_order', 'unit__name', order_field)
        
        # Default ordering
        return queryset.order_by('unit__sort_order', 'unit__name', 'organization__name', 'position__title')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Group callings by unit
        callings_by_unit = {}
        unit_objects = {}
        for calling in context['callings']:
            unit_name = str(calling.unit)
            if unit_name not in callings_by_unit:
                callings_by_unit[unit_name] = []
                unit_objects[unit_name] = calling.unit
            callings_by_unit[unit_name].append(calling)
        
        # Sort by unit sort_order, then by name
        sorted_units = sorted(unit_objects.items(), key=lambda x: (x[1].sort_order, x[1].name))
        context['callings_by_unit'] = {unit_name: callings_by_unit[unit_name] for unit_name, unit_obj in sorted_units}
        
        # Get counts (reuse logic from CallingListView)
        all_callings = Calling.objects.select_related('position', 'organization', 'unit')
        search = self.request.GET.get('search')
        if search:
            all_callings = all_callings.filter(
                Q(name__icontains=search) |
                Q(position__title__icontains=search) |
                Q(organization__name__icontains=search) |
                Q(unit__name__icontains=search) |
                Q(proposed_replacement__icontains=search)
            )
        
        context['pending_count'] = all_callings.filter(status='PENDING').count()
        context['approved_count'] = all_callings.filter(status='APPROVED').count()
        context['completed_count'] = all_callings.filter(status='COMPLETED').count()
        context['lcr_updated_count'] = all_callings.filter(status='LCR_UPDATED').count()
        context['cancelled_count'] = all_callings.filter(status='CANCELLED').count()
        context['on_hold_count'] = all_callings.filter(status='ON_HOLD').count()
        # Use new Active definition: not COMPLETED, LCR_UPDATED, or CANCELLED
        context['active_count'] = all_callings.exclude(status__in=['COMPLETED', 'LCR_UPDATED', 'CANCELLED']).count()
        context['all_count'] = all_callings.count()
        
        context['current_status'] = self.request.GET.get('status', 'all')
        context['current_search'] = search or ''
        
        return context

class CallingDetailView(LoginRequiredMixin, TitleMixin, DetailView):
    model = Calling
    template_name = 'callings/calling/calling_detail.html'
    context_object_name = 'calling'

    def get_title(self):
        return f"Calling: {self.get_object().position.title}"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['release_form'] = CallingReleaseForm(instance=self.object)
        
        # Preserve filter context from referring page
        context['back_url'] = self.get_back_url()
        
        return context
    
    def get_back_url(self):
        """Generate the URL to go back to the filtered list view"""
        # Check if we came from a specific filter
        referer = self.request.META.get('HTTP_REFERER', '')
        
        # Extract filter parameters from the referer URL
        from django.urls import reverse
        from urllib.parse import quote
        
        base_url = reverse('callings:callings-by-unit')
        
        if 'status=' in referer:
            import re
            status_match = re.search(r'status=([^&]+)', referer)
            if status_match:
                status = status_match.group(1)
                
                # Check if there's also a search parameter
                if 'search=' in referer:
                    search_match = re.search(r'search=([^&]+)', referer)
                    if search_match:
                        search_term = quote(search_match.group(1))
                        return f"{base_url}?status={status}&search={search_term}"
                
                return f"{base_url}?status={status}"
        
        # Check if it includes search parameter alone
        if 'search=' in referer:
            import re
            search_match = re.search(r'search=([^&]+)', referer)
            if search_match:
                search_term = quote(search_match.group(1))
                return f"{base_url}?search={search_term}"
        
        # Default back to all callings (grouped view)
        return base_url

class CallingCreateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, CreateView):
    model = Calling
    form_class = CallingForm
    template_name = 'callings/calling/calling_form.html'
    title = 'Create Calling'
    
    def get_success_url(self):
        # Preserve filter parameters from GET if present
        referer = self.request.META.get('HTTP_REFERER')
        if referer:
            from urllib.parse import urlparse, parse_qs, urlencode
            parsed_url = urlparse(referer)
            query_params = parse_qs(parsed_url.query)
            
            # Check if referer came from a filtered view
            if 'callings/by-unit' in referer or 'callings/callings' in referer:
                base_url = reverse_lazy('callings:callings-by-unit')
                
                # Reconstruct the URL with current GET params
                if query_params:
                    query_string = urlencode({k: v[0] for k, v in query_params.items()})
                    return f'{base_url}?{query_string}'
                return base_url
        
        # Default to calling detail page
        return reverse_lazy('callings:calling-detail', kwargs={'pk': self.object.pk})
        


class CallingUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, UpdateView):
    model = Calling
    form_class = CallingForm
    template_name = 'callings/calling/calling_form.html'
    
    def get_title(self):
        return f"Update Calling: {self.get_object().position.title}"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the referer information to the template
        referer = self.request.META.get('HTTP_REFERER', '')
        context['return_url'] = self.get_return_url(referer)
        return context
    
    def get_return_url(self, referer):
        """Determine the return URL based on the referer"""
        if 'status=active' in referer and 'callings/by-unit' in referer:
            return reverse_lazy('callings:callings-by-unit') + '?status=active'
        elif 'callings/by-unit' in referer:
            # Extract query parameters from referer
            from urllib.parse import urlparse, parse_qs, urlencode
            parsed_url = urlparse(referer)
            query_params = parse_qs(parsed_url.query)
            if query_params:
                query_string = urlencode({k: v[0] for k, v in query_params.items()})
                return reverse_lazy('callings:callings-by-unit') + f'?{query_string}'
            return reverse_lazy('callings:callings-by-unit')
        elif 'callings/calling' in referer:
            # Extract query parameters from referer for list view
            from urllib.parse import urlparse, parse_qs, urlencode
            parsed_url = urlparse(referer)
            query_params = parse_qs(parsed_url.query)
            if query_params:
                query_string = urlencode({k: v[0] for k, v in query_params.items()})
                return reverse_lazy('callings:calling-list') + f'?{query_string}'
            return reverse_lazy('callings:calling-list')
        elif referer and (referer.endswith('/') or 'dashboard' in referer):
            # If coming from dashboard (root URL or dashboard), return to dashboard
            return reverse_lazy('dashboard')
        # Default fallback
        return reverse_lazy('callings:callings-by-unit')
    
    def get_success_url(self):
        # Check if a return URL was provided in the POST data
        return_url = self.request.POST.get('return_url')
        if return_url:
            return return_url
        # Fallback to calling detail page
        return reverse_lazy('callings:calling-detail', kwargs={'pk': self.object.pk})

class CallingDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, DeleteView):
    model = Calling
    template_name = 'callings/calling/calling_confirm_delete.html'
    success_url = reverse_lazy('callings:calling-list')
    
    def get_title(self):
        return f"Delete Calling: {self.get_object().position.title}"

class CallingUpdateStatusView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    def get(self, request, pk, new_status):
        return self.update_status(request, pk, new_status)
    
    def post(self, request, pk, new_status):
        return self.update_status(request, pk, new_status)
    
    def update_status(self, request, pk, new_status):
        # Ensure the new status is valid
        valid_statuses = [choice[0] for choice in Calling.STATUS_CHOICES]
        if new_status not in valid_statuses:
            messages.error(request, 'Invalid status update.')
            return redirect('callings:calling-list')
        
        calling = get_object_or_404(Calling, pk=pk)
        old_status = calling.get_status_display()
        calling.status = new_status
        calling.save()
        
        new_status_display = calling.get_status_display()
        messages.success(request, f'Calling status updated from {old_status} to {new_status_display} successfully.')
        
        # Redirect back to the calling list or detail page based on where the request came from
        return redirect(request.META.get('HTTP_REFERER', 'callings:calling-list'))

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
        # Preserve filter parameters from GET if present
        referer = self.request.META.get('HTTP_REFERER')
        if referer:
            from urllib.parse import urlparse, parse_qs, urlencode
            parsed_url = urlparse(referer)
            query_params = parse_qs(parsed_url.query)
            
            # Check if referer came from a filtered view
            if 'callings/by-unit' in referer or 'callings/callings' in referer:
                base_url = reverse_lazy('callings:callings-by-unit')
                
                # Reconstruct the URL with current GET params
                if query_params:
                    query_string = urlencode({k: v[0] for k, v in query_params.items()})
                    return f'{base_url}?{query_string}'
                return base_url
        
        # Default to calling detail page
        return reverse_lazy('callings:calling-detail', kwargs={'pk': self.object.pk})

class CallingLCRUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, TitleMixin, UpdateView):
    model = Calling
    fields = []  # No form fields needed, just updating status
    
    def get_title(self):
        return f"Update LCR Status: {self.get_object().position.title}"
    
    def post(self, request, *args, **kwargs):
        calling = self.get_object()
        
        # Update the status to LCR_UPDATED
        calling.status = 'LCR_UPDATED'
        calling.lcr_updated = True
        calling.save()
        
        messages.success(request, f'LCR status updated for {calling.position.title} calling.')
        
        # Redirect back to the referring page or calling list
        referer = request.META.get('HTTP_REFERER')
        if referer and ('callings/by-unit' in referer or 'callings/callings' in referer):
            # If we came from a filtered view, preserve that context
            from urllib.parse import urlparse, parse_qs, urlencode
            parsed_url = urlparse(referer)
            query_params = parse_qs(parsed_url.query)
            base_url = reverse_lazy('callings:callings-by-unit')
            
            if query_params:
                query_string = urlencode({k: v[0] for k, v in query_params.items()})
                return redirect(f'{base_url}?{query_string}')
            return redirect(base_url)
        
        next_url = request.POST.get('next', referer or reverse_lazy('callings:calling-list'))
        return redirect(next_url)
    
    def get(self, request, *args, **kwargs):
        # For GET requests, just redirect to calling detail
        calling = self.get_object()
        return redirect('callings:calling-detail', pk=calling.pk)

