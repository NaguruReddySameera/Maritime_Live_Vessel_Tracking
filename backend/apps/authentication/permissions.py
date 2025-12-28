"""
Custom permission classes for role-based access control
"""

from rest_framework import permissions


class IsOperator(permissions.BasePermission):
    """
    Permission class for Operator role
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['operator', 'analyst', 'admin']


class IsAnalyst(permissions.BasePermission):
    """
    Permission class for Analyst role and above
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['analyst', 'admin']


class IsAdmin(permissions.BasePermission):
    """
    Permission class for Admin role only
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class HasPermission(permissions.BasePermission):
    """
    Generic permission class that checks user has specific permission
    Usage: permission_classes = [HasPermission]
    permission_required = 'view_vessels'
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        permission = getattr(view, 'permission_required', None)
        if not permission:
            return True
        
        return request.user.has_permission(permission)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class to allow owners or admins to edit objects
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner or admin
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user or request.user.role == 'admin'
        
        return request.user.role == 'admin'
