from django.urls import path

from .views import (
    ApprovePermissionRequestView,
    EmployeeDetailView,
    EmployeeListCreateView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    PermissionRequestListCreateView,
    RegisterView,
    RejectPermissionRequestView,
    ShopProfileView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("employees/", EmployeeListCreateView.as_view(), name="employee-list"),
    path("employees/<uuid:user_id>/", EmployeeDetailView.as_view(), name="employee-detail"),
    path("permission-requests/", PermissionRequestListCreateView.as_view(), name="permission-request-list"),
    path("permission-requests/<uuid:request_id>/approve/", ApprovePermissionRequestView.as_view(), name="permission-request-approve"),
    path("permission-requests/<uuid:request_id>/reject/", RejectPermissionRequestView.as_view(), name="permission-request-reject"),
    path("shop-profile/", ShopProfileView.as_view(), name="shop-profile"),
]