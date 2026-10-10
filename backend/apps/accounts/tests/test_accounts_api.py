import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from apps.accounts.models import Membership, Organization, PermissionGrant, PermissionRequest, ShopProfile, User
from apps.accounts.services import DEFAULT_EMPLOYEE_PERMISSIONS


PASSWORD = "NotACommonPassword123!"

pytestmark = pytest.mark.django_db


def register_boss(client: APIClient, username: str) -> None:
    response = client.post("/api/v1/auth/register/", {"username": username, "password": PASSWORD}, format="json")
    assert response.status_code == 201, response.content


def login(client: APIClient, username: str) -> None:
    response = client.post("/api/v1/auth/token/", {"username": username, "password": PASSWORD}, format="json")
    assert response.status_code == 200, response.content
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['data']['access']}")


def test_register_creates_boss_organization_membership_and_shop_profile() -> None:
    client = APIClient()

    register_boss(client, "boss-a")

    user = User.objects.get(username="boss-a")
    organization = Organization.objects.get(owner_user=user)
    membership = Membership.objects.get(user=user)
    assert membership.organization == organization
    assert membership.role == Membership.Role.BOSS
    assert ShopProfile.objects.get(organization=organization).shop_name == "boss-a"


def test_protected_endpoint_and_invalid_registration_return_standard_errors() -> None:
    client = APIClient()

    unauthenticated_response = client.get("/api/v1/auth/me/")
    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json()["code"] == "not_authenticated"

    invalid_response = client.post("/api/v1/auth/register/", {"username": "boss-a"}, format="json")
    assert invalid_response.status_code == 400
    assert invalid_response.json()["errors"]["password"]


def test_authentication_reports_duplicate_username_missing_user_and_wrong_password() -> None:
    client = APIClient()
    register_boss(client, "boss-a")

    duplicate_response = client.post(
        "/api/v1/auth/register/", {"username": "boss-a", "password": PASSWORD}, format="json"
    )
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["errors"]["username"] == ["用户名已被使用"]

    missing_user_response = client.post(
        "/api/v1/auth/token/", {"username": "missing", "password": PASSWORD}, format="json"
    )
    assert missing_user_response.status_code == 400
    assert missing_user_response.json()["errors"]["username"] == ["用户不存在"]

    wrong_password_response = client.post(
        "/api/v1/auth/token/", {"username": "boss-a", "password": "WrongPassword123!"}, format="json"
    )
    assert wrong_password_response.status_code == 400
    assert wrong_password_response.json()["errors"]["password"] == ["密码错误"]


def test_employee_gets_default_permissions_and_cannot_read_another_boss_employee() -> None:
    boss_client = APIClient()
    register_boss(boss_client, "boss-a")
    login(boss_client, "boss-a")
    create_response = boss_client.post(
        "/api/v1/employees/",
        {"username": "employee-a", "display_name": "Employee A", "password": PASSWORD},
        format="json",
    )
    assert create_response.status_code == 201, create_response.content

    employee_client = APIClient()
    login(employee_client, "employee-a")
    me_response = employee_client.get("/api/v1/auth/me/")
    assert me_response.status_code == 200
    assert set(me_response.json()["data"]["permissions"]) == DEFAULT_EMPLOYEE_PERMISSIONS

    other_boss_client = APIClient()
    register_boss(other_boss_client, "boss-b")
    login(other_boss_client, "boss-b")
    employee_id = create_response.json()["data"]["id"]
    response = other_boss_client.get(f"/api/v1/employees/{employee_id}/")
    assert response.status_code == 404


def test_permission_request_approval_creates_grant_once() -> None:
    boss_client = APIClient()
    register_boss(boss_client, "boss-a")
    login(boss_client, "boss-a")
    create_response = boss_client.post(
        "/api/v1/employees/",
        {"username": "employee-a", "display_name": "Employee A", "password": PASSWORD},
        format="json",
    )
    employee_id = create_response.json()["data"]["id"]

    employee_client = APIClient()
    login(employee_client, "employee-a")
    request_response = employee_client.post(
        "/api/v1/permission-requests/",
        {"permission_code": "products.manage"},
        format="json",
    )
    assert request_response.status_code == 201, request_response.content

    request_id = request_response.json()["data"]["id"]
    approve_response = boss_client.post(f"/api/v1/permission-requests/{request_id}/approve/")
    assert approve_response.status_code == 200, approve_response.content
    assert approve_response.json()["data"]["status"] == PermissionRequest.Status.APPROVED
    assert PermissionGrant.objects.filter(
        membership__user_id=employee_id,
        permission_code="products.manage",
    ).count() == 1

    replay_response = boss_client.post(f"/api/v1/permission-requests/{request_id}/approve/")
    assert replay_response.status_code == 400
    assert PermissionGrant.objects.filter(
        membership__user_id=employee_id,
        permission_code="products.manage",
    ).count() == 1


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_password_reset_sends_a_link_and_sets_a_new_password() -> None:
    client = APIClient()
    register_boss(client, "boss-a")
    user = User.objects.get(username="boss-a")
    user.email = "boss@example.com"
    user.save(update_fields=["email"])

    response = client.post("/api/v1/auth/password-reset/", {"email": user.email}, format="json")
    assert response.status_code == 204
    assert len(mail.outbox) == 1

    response = client.post(
        "/api/v1/auth/password-reset/confirm/",
        {
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
            "password": "NewSecurePassword123!",
        },
        format="json",
    )
    assert response.status_code == 204, response.content
    user.refresh_from_db()
    assert user.check_password("NewSecurePassword123!")


def test_authentication_requires_an_organization_membership() -> None:
    User.objects.create_user("unaffiliated-user", password=PASSWORD)
    client = APIClient()

    login(client, "unaffiliated-user")

    response = client.get("/api/v1/auth/me/")
    assert response.status_code == 403


def test_superuser_creation_is_disabled() -> None:
    with pytest.raises(ValueError, match="Superuser accounts are not supported"):
        User.objects.create_superuser("system-admin", "admin@example.com", PASSWORD)