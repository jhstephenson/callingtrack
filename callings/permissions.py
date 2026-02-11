"""
Custom permissions and decorators for CallingTrack.

This module defines custom permissions for role-based access control
and provides decorators/mixins for view protection.
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps


# Permission group names
STAKE_PRESIDENT_GROUP = 'Stake President'
BISHOP_GROUP = 'Bishop'
CLERK_GROUP = 'Clerk'
STAKE_CLERK_GROUP = 'Stake Clerk'
LEADERSHIP_GROUP = 'Leadership'


def user_in_group(user, group_name):
    """Check if user is in a specific group."""
    return user.groups.filter(name=group_name).exists()


def is_stake_president(user):
    """Check if user is a stake president."""
    return user.is_superuser or user_in_group(user, STAKE_PRESIDENT_GROUP)


def is_bishop(user):
    """Check if user is a bishop."""
    return user.is_superuser or user_in_group(user, BISHOP_GROUP)


def is_clerk(user):
    """Check if user is any kind of clerk."""
    return (
        user.is_superuser or 
        user_in_group(user, CLERK_GROUP) or 
        user_in_group(user, STAKE_CLERK_GROUP)
    )


def is_leadership(user):
    """Check if user is in any leadership position."""
    return (
        user.is_superuser or
        user_in_group(user, STAKE_PRESIDENT_GROUP) or
        user_in_group(user, BISHOP_GROUP) or
        user_in_group(user, LEADERSHIP_GROUP)
    )


def can_edit_calling(user):
    """Check if user can edit callings."""
    return is_leadership(user) or is_clerk(user)


def can_approve_calling(user):
    """Check if user can approve callings."""
    return is_stake_president(user) or is_bishop(user)


def can_delete_calling(user):
    """Check if user can delete callings."""
    return user.is_superuser or is_stake_president(user)


def can_manage_units(user):
    """Check if user can manage organizational units."""
    return user.is_superuser or is_stake_president(user) or is_clerk(user)


# Decorators for function-based views
def stake_president_required(view_func):
    """Decorator to require stake president role."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_stake_president(request.user):
            raise PermissionDenied("Only Stake Presidents can access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper


def bishop_required(view_func):
    """Decorator to require bishop role."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_bishop(request.user):
            raise PermissionDenied("Only Bishops can access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper


def leadership_required(view_func):
    """Decorator to require any leadership role."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_leadership(request.user):
            raise PermissionDenied("Leadership access required.")
        return view_func(request, *args, **kwargs)
    return wrapper


def clerk_required(view_func):
    """Decorator to require clerk role."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_clerk(request.user):
            raise PermissionDenied("Clerk access required.")
        return view_func(request, *args, **kwargs)
    return wrapper


def can_edit_required(view_func):
    """Decorator to require calling edit permission."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not can_edit_calling(request.user):
            raise PermissionDenied("You don't have permission to edit callings.")
        return view_func(request, *args, **kwargs)
    return wrapper


# Mixins for class-based views
class StakePresidentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require stake president role for class-based views."""
    
    def test_func(self):
        return is_stake_president(self.request.user)
    
    def handle_no_permission(self):
        raise PermissionDenied("Only Stake Presidents can access this page.")


class BishopRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require bishop role for class-based views."""
    
    def test_func(self):
        return is_bishop(self.request.user)
    
    def handle_no_permission(self):
        raise PermissionDenied("Only Bishops can access this page.")


class LeadershipRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require any leadership role for class-based views."""
    
    def test_func(self):
        return is_leadership(self.request.user)
    
    def handle_no_permission(self):
        raise PermissionDenied("Leadership access required.")


class ClerkRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require clerk role for class-based views."""
    
    def test_func(self):
        return is_clerk(self.request.user)
    
    def handle_no_permission(self):
        raise PermissionDenied("Clerk access required.")


class CanEditCallingMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require calling edit permission for class-based views."""
    
    def test_func(self):
        return can_edit_calling(self.request.user)
    
    def handle_no_permission(self):
        raise PermissionDenied("You don't have permission to edit callings.")


class CanApproveCallingMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require calling approval permission for class-based views."""
    
    def test_func(self):
        return can_approve_calling(self.request.user)
    
    def handle_no_permission(self):
        raise PermissionDenied("You don't have permission to approve callings.")


class CanDeleteCallingMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require calling delete permission for class-based views."""
    
    def test_func(self):
        return can_delete_calling(self.request.user)
    
    def handle_no_permission(self):
        raise PermissionDenied("You don't have permission to delete callings.")


class CanManageUnitsMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require unit management permission for class-based views."""
    
    def test_func(self):
        return can_manage_units(self.request.user)
    
    def handle_no_permission(self):
        raise PermissionDenied("You don't have permission to manage units.")
