from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Membership, Organization, PermissionGrant, PermissionRequest, ShopProfile

DEFAULT_EMPLOYEE_PERMISSIONS = frozenset(
    {
        "sales.create",
        "purchases.create",
        "dashboard.view",
        "products.view",
        "partners.view",
        "inventory.view",
        "reports.view",
    }
)
MANAGEABLE_PERMISSION_CODES = frozenset(
    {
        "products.manage",
        "partners.manage",
        "sales.returns.manage",
        "purchases.returns.manage",
        "employees.manage",
        "shop.manage",
    }
)


def validate_permission_code(permission_code: str) -> str:
    if permission_code not in MANAGEABLE_PERMISSION_CODES:
        raise ValidationError({"permission_code": ["Unsupported permission code."]})
    return permission_code


@transaction.atomic
def register_boss(*, username: str, password: str, email: str = "") -> Membership:
    user_model = get_user_model()
    try:
        validate_password(password)
    except DjangoValidationError as error:
        raise ValidationError({"password": list(error.messages)}) from error

    try:
        user = user_model.objects.create_user(username=username, password=password, email=email)
    except IntegrityError as error:
        raise ValidationError({"username": ["A user with that username already exists."]}) from error

    organization = Organization.objects.create(owner_user=user, name=username)
    from apps.products.services import initialize_organization_catalog
    from apps.warehouses.services import ensure_default_warehouse

    initialize_organization_catalog(organization=organization)
    ensure_default_warehouse(organization=organization)
    membership = Membership.objects.create(
        organization=organization,
        user=user,
        role=Membership.Role.BOSS,
    )
    ShopProfile.objects.create(organization=organization, shop_name=username)
    return membership


@transaction.atomic
def create_employee(
    *, boss_membership: Membership, username: str, display_name: str, password: str, email: str = ""
) -> Membership:
    if boss_membership.role != Membership.Role.BOSS:
        raise ValidationError("Only a boss can create employees.")
    user_model = get_user_model()
    try:
        validate_password(password)
    except DjangoValidationError as error:
        raise ValidationError({"password": list(error.messages)}) from error
    try:
        user = user_model.objects.create_user(
            username=username,
            password=password,
            display_name=display_name,
            email=email,
        )
    except IntegrityError as error:
        raise ValidationError({"username": ["A user with that username already exists."]}) from error
    return Membership.objects.create(
        organization=boss_membership.organization,
        user=user,
        role=Membership.Role.EMPLOYEE,
    )


@transaction.atomic
def grant_permission(*, employee_membership: Membership, permission_code: str, granted_by_user) -> PermissionGrant:
    validate_permission_code(permission_code)
    if employee_membership.role != Membership.Role.EMPLOYEE:
        raise ValidationError({"permission_code": ["Permissions can only be granted to employees."]})
    grant, _ = PermissionGrant.objects.get_or_create(
        membership=employee_membership,
        permission_code=permission_code,
        defaults={"granted_by_user": granted_by_user},
    )
    return grant


@transaction.atomic
def review_permission_request(*, request_id, organization: Organization, reviewer, approved: bool) -> PermissionRequest:
    permission_request = (
        PermissionRequest.objects.select_for_update()
        .select_related("membership")
        .filter(id=request_id, membership__organization=organization)
        .first()
    )
    if permission_request is None:
        raise PermissionRequest.DoesNotExist
    if permission_request.status != PermissionRequest.Status.PENDING:
        raise ValidationError({"status": ["Only pending requests can be reviewed."]})

    permission_request.status = (
        PermissionRequest.Status.APPROVED if approved else PermissionRequest.Status.REJECTED
    )
    permission_request.reviewed_by_user = reviewer
    permission_request.reviewed_at = timezone.now()
    permission_request.save()
    if approved:
        grant_permission(
            employee_membership=permission_request.membership,
            permission_code=permission_request.permission_code,
            granted_by_user=reviewer,
        )
    return permission_request


def effective_permissions(membership: Membership) -> set[str]:
    if membership.role == Membership.Role.BOSS:
        return {"*"}
    grants = membership.permission_grants.values_list("permission_code", flat=True)
    return set(DEFAULT_EMPLOYEE_PERMISSIONS).union(grants)