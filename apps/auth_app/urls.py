"""
URLs del módulo de autenticación (auth_app).

Define 12 endpoints REST bajo /api/v1/auth/ para:
- Registro y verificación de email
- Login, logout y gestión de sesiones
- Cambio y recuperación de contraseña
- Consulta y actualización de perfil
- Desactivación de cuenta
"""

from django.urls import path

from apps.auth_app.views.register_view import RegisterView
from apps.auth_app.views.verify_view import VerifyEmailView
from apps.auth_app.views.resend_view import ResendVerificationCodeView
from apps.auth_app.views.session_view import SessionInfoView
from apps.auth_app.views.login_view import LoginView
from apps.auth_app.views.logout_view import LogoutView
from apps.auth_app.views.logout_all_view import LogoutAllView
from apps.auth_app.views.user_update_view import UserUpdateView
from apps.auth_app.views.user_get_view import UserGetView

from apps.auth_app.views.password_change_view import PasswordChangeView
from apps.auth_app.views.password_reset_view import PasswordResetRequestView, PasswordResetConfirmView
from apps.auth_app.views.deactivate_view import DeactivateAccountView

app_name = "auth_app"

urlpatterns = [
    # Registro y verificación
    path("register/", RegisterView.as_view(), name="register"),
    path("resend-code/", ResendVerificationCodeView.as_view(), name="resend_code"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),

    # Autenticación
    path("login/", LoginView.as_view(), name="login"),
    path("session/", SessionInfoView.as_view(), name="session"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logout-all/", LogoutAllView.as_view(), name="logout_all"),
    path("user-get/", UserGetView.as_view(), name="user_get"),
    path("user-update/", UserUpdateView.as_view(), name="user_update"),

    # Gestión de contraseña
    path("password-change/", PasswordChangeView.as_view(), name="password_change"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),

    # Gestión de cuenta
    path("deactivate/", DeactivateAccountView.as_view(), name="deactivate"),
]
