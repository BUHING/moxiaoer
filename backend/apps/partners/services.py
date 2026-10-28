import sqlite3

from django.db import IntegrityError, transaction
from django.db.models.functions import Trim
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound

from apps.accounts.models import Organization

from .models import (
    CUSTOMER_IDENTITY_CONSTRAINT,
    CUSTOMER_IDENTITY_FIELDS,
    SUPPLIER_IDENTITY_CONSTRAINT,
    SUPPLIER_IDENTITY_FIELDS,
    Customer,
    Supplier,
)


class PartnerAlreadyExists(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "partner_already_exists"
    default_detail = "已有完全相同的资料，请检查后再保存。"


def _identity_definition(model) -> tuple[tuple[str, ...], str, str, str]:
    if model is Customer:
        return CUSTOMER_IDENTITY_FIELDS, CUSTOMER_IDENTITY_CONSTRAINT, "客户", "名称、联系人和电话"
    if model is Supplier:
        return (
            SUPPLIER_IDENTITY_FIELDS,
            SUPPLIER_IDENTITY_CONSTRAINT,
            "供应商",
            "名称、联系人、联系地址和电话",
        )
    raise ValueError("Unsupported partner model.")


def _find_duplicate(*, model, organization, identity: dict, instance):
    aliases = {f"_identity_{field}": Trim(field) for field in identity}
    filters = {f"_identity_{field}": value.strip(" ") for field, value in identity.items()}
    queryset = model.objects.alias(**aliases).filter(organization=organization, **filters)
    if instance is not None:
        queryset = queryset.exclude(pk=instance.pk)
    return queryset.only("is_active").first()


def _duplicate_error(model, existing) -> PartnerAlreadyExists:
    _, _, noun, fields = _identity_definition(model)
    if existing is not None and not existing.is_active:
        detail = f"已有一条完全相同的{noun}资料，目前已停用，请切换到“仅停用”查看。"
    else:
        detail = f"已有一条{noun}资料的{fields}都相同，请检查后再保存。"
    return PartnerAlreadyExists(detail, code=f"duplicate_{model._meta.model_name}")


def _is_identity_conflict(error: IntegrityError, constraint_name: str) -> bool:
    cause = error.__cause__
    diagnostic = getattr(cause, "diag", None)
    if diagnostic is not None:
        return diagnostic.constraint_name == constraint_name
    return isinstance(cause, sqlite3.IntegrityError) and str(cause) == (
        f"UNIQUE constraint failed: index '{constraint_name}'"
    )


@transaction.atomic
def save_partner(
    *,
    model,
    organization: Organization,
    values: dict,
    instance: Customer | Supplier | None = None,
) -> Customer | Supplier:
    fields, constraint_name, _, _ = _identity_definition(model)
    if instance is not None:
        try:
            instance = model.objects.select_for_update().get(
                pk=instance.pk, organization=organization
            )
        except model.DoesNotExist as error:
            raise NotFound("Partner was not found.") from error

    values = values.copy()
    for field in fields:
        if field in values:
            values[field] = values[field].strip()
    identity = {
        field: values[field] if field in values else getattr(instance, field, "")
        for field in fields
    }
    existing = _find_duplicate(
        model=model, organization=organization, identity=identity, instance=instance
    )
    if existing is not None:
        raise _duplicate_error(model, existing)

    try:
        # A savepoint allows a concurrent identity conflict to become a normal API error.
        with transaction.atomic():
            if instance is None:
                instance = model.objects.create(organization=organization, **values)
            else:
                for field, value in values.items():
                    setattr(instance, field, value)
                instance.save(update_fields=[*values, "updated_at"])
    except IntegrityError as error:
        if not _is_identity_conflict(error, constraint_name):
            raise
        existing = _find_duplicate(
            model=model, organization=organization, identity=identity, instance=instance
        )
        raise _duplicate_error(model, existing) from error
    return instance
