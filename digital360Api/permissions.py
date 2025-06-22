from rest_framework.permissions import BasePermission

class IsSupervisor(BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == 'supervisor'

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == 'admin'
