import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.accounts.models import Organization, TimestampedModel
from apps.partners.models import Customer, PriceLevel
from apps.products.models import Product


class SalesDocument(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        COMPLETED = "COMPLETED", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    document_no = models.CharField(max_length=64)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    occurred_on = models.DateField()
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    remark = models.TextField(blank=True)
    completed_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="completed_%(app_label)s_%(class)s_documents",
        null=True,
        blank=True,
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_%(app_label)s_%(class)s_documents",
    )
    updated_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_%(app_label)s_%(class)s_documents",
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "document_no"],
                name="%(app_label)s_%(class)s_organization_document_no_unique",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="DRAFT", completed_by_user__isnull=True, completed_at__isnull=True)
                    | Q(status="COMPLETED", completed_by_user__isnull=False, completed_at__isnull=False)
                ),
                name="%(app_label)s_%(class)s_completion_state_valid",
            ),
            models.CheckConstraint(
                condition=Q(total_amount__gte=0),
                name="%(app_label)s_%(class)s_total_amount_nonnegative",
            ),
        ]
        indexes = [models.Index(fields=["organization", "status", "-occurred_on"])]


class SalesOrder(SalesDocument):
    pass


class SalesReturn(SalesDocument):
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.PROTECT,
        related_name="returns",
    )


class SalesDocumentItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line_no = models.PositiveIntegerField()
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name_snapshot = models.CharField(max_length=200)
    unit_name_snapshot = models.CharField(max_length=50)
    price_level = models.ForeignKey(PriceLevel, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    line_amount = models.DecimalField(max_digits=18, decimal_places=2)
    unit_cost_snapshot = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    cost_amount = models.DecimalField(max_digits=18, decimal_places=6, default=0)

    class Meta:
        abstract = True
        constraints = [
            models.CheckConstraint(
                condition=Q(line_no__gt=0),
                name="%(app_label)s_%(class)s_line_no_positive",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="%(app_label)s_%(class)s_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="%(app_label)s_%(class)s_unit_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(line_amount__gte=0),
                name="%(app_label)s_%(class)s_line_amount_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(unit_cost_snapshot__gte=0),
                name="%(app_label)s_%(class)s_unit_cost_snapshot_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(cost_amount__gte=0),
                name="%(app_label)s_%(class)s_cost_amount_nonnegative",
            ),
        ]


class SalesOrderItem(SalesDocumentItem):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="items")

    class Meta(SalesDocumentItem.Meta):
        constraints = [
            *SalesDocumentItem.Meta.constraints,
            models.UniqueConstraint(
                fields=["sales_order", "line_no"],
                name="sales_order_item_order_line_no_unique",
            ),
        ]


class SalesReturnItem(SalesDocumentItem):
    sales_return = models.ForeignKey(SalesReturn, on_delete=models.CASCADE, related_name="items")
    sales_order_item = models.ForeignKey(
        SalesOrderItem,
        on_delete=models.PROTECT,
        related_name="return_items",
    )

    class Meta(SalesDocumentItem.Meta):
        constraints = [
            *SalesDocumentItem.Meta.constraints,
            models.UniqueConstraint(
                fields=["sales_return", "line_no"],
                name="sales_return_item_return_line_no_unique",
            ),
        ]