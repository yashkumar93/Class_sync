"""
Custom DRF permission classes for ClassSync REST API.
"""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow only users with the 'admin' role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsFaculty(BasePermission):
    """Allow only users with the 'faculty' role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "faculty"
        )


class IsStudent(BasePermission):
    """Allow only users with the 'student' role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "student"
        )


class IsFacultyOrAdmin(BasePermission):
    """Allow users with 'faculty' or 'admin' role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("faculty", "admin")
        )
