import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.accounts.models import Organization
from apps.products.models import Product


class StockBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="stock_balances")
    product = models.OneToOneField(Product, on_delete=models.PROTECT, related_name="stock_balance")
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "product"],
                name="inventory_stock_balance_organization_product_unique",
            )
        ]


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        INITIAL = "INITIAL", "Initial"
        PURCHASE = "PURCHASE", "Purchase"
        PURCHASE_RETURN = "PURCHASE_RETURN", "Purchase return"
        SALE = "SALE", "Sale"
        SALE_RETURN = "SALE_RETURN", "Sale return"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="stock_movements")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_movements")
    movement_type = models.CharField(max_length=24, choices=MovementType.choices)
    quantity_delta = models.DecimalField(max_digits=18, decimal_places=4)
    source_type = models.CharField(max_length=40)
    source_id = models.UUIDField()
    occurred_at = models.DateTimeField(auto_now_add=True)
    operator_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    remark = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity_delta__gt=0) | Q(quantity_delta__lt=0),
                name="inventory_stock_movement_quantity_nonzero",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        movement_type__in=["INITIAL", "PURCHASE", "SALE_RETURN"],
                        quantity_delta__gt=0,
                    )
                    | Q(
                        movement_type__in=["PURCHASE_RETURN", "SALE"],
                        quantity_delta__lt=0,
                    )
                ),
                name="inventory_stock_movement_type_sign_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "product", "-occurred_at"]),
            models.Index(fields=["source_type", "source_id"]),
        ]


class IdempotencyRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="idempotency_records",
    )
    action = models.CharField(max_length=50)
    idempotency_key = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=40)
    resource_id = models.UUIDField()
    response_status = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "action", "idempotency_key"],
                name="inventory_idempotency_organization_action_key_unique",
            )
        ]