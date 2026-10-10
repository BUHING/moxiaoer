import uuid

from django.db import models

from apps.accounts.models import Organization, TimestampedModel


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
                fields=["organization", "name"],
                name="partners_customer_organization_name_unique",
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
                fields=["organization", "name"],
                name="partners_supplier_organization_name_unique",
            )
        ]
        indexes = [models.Index(fields=["organization", "is_active", "created_at"])]