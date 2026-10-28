import uuid

from django.db import models
from django.db.models.functions import Trim

from apps.accounts.models import Organization, TimestampedModel


CUSTOMER_IDENTITY_FIELDS = ("name", "contact_name", "phone")
SUPPLIER_IDENTITY_FIELDS = ("name", "contact_name", "contact_address", "phone")
CUSTOMER_IDENTITY_CONSTRAINT = "partners_customer_identity_unique"
SUPPLIER_IDENTITY_CONSTRAINT = "partners_supplier_identity_unique"


class PriceLevel(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="price_levels",
    )
    name = models.CharField(max_length=50)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="partners_price_level_organization_name_unique",
            )
        ]
        indexes = [models.Index(fields=["organization", "is_active", "created_at"])]


class Customer(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="customers",
    )
    name = models.CharField(max_length=150)
    contact_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    remark = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                models.F("organization"),
                *(Trim(field) for field in CUSTOMER_IDENTITY_FIELDS),
                name=CUSTOMER_IDENTITY_CONSTRAINT,
            )
        ]
        indexes = [models.Index(fields=["organization", "is_active", "created_at"])]


class Supplier(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="suppliers",
    )
    name = models.CharField(max_length=150)
    contact_name = models.CharField(max_length=100, blank=True)
    contact_address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    remark = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                models.F("organization"),
                *(Trim(field) for field in SUPPLIER_IDENTITY_FIELDS),
                name=SUPPLIER_IDENTITY_CONSTRAINT,
            )
        ]
        indexes = [models.Index(fields=["organization", "is_active", "created_at"])]