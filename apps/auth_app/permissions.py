"""Permisos personalizados para el módulo de autenticación.

Define políticas de acceso para cuentas activas y verificación
de propiedad de recursos (owner/admin).
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAccountActive(BasePermission):
    """Permite acceso solo si la cuenta del usuario está activa.

    Útil para endpoints que requieren una cuenta en estado válido
    (no desactivada ni bloqueada).
    """

    message = "Tu cuenta está inactiva. Contacta soporte para reactivarla."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "is_active", False)


class IsOwnerOrAdmin(BasePermission):
    """Permite acceso si el usuario es propietario del recurso o admin.

    En métodos seguros (GET, HEAD, OPTIONS) permite acceso global.
    En métodos de modificación verifica que el usuario sea el owner o staff.
    """

    message = "No tienes permiso para realizar esta acción."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user and (user.is_staff or user.is_superuser):
            return True
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return owner == user

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return True

