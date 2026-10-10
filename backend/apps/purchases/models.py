import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.accounts.models import Organization, TimestampedModel
from apps.partners.models import Supplier
from apps.products.models import Product


class PurchaseDocument(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        COMPLETED = "COMPLETED", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    document_no = models.CharField(max_length=64)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, null=True, blank=True)
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


class Purchase(PurchaseDocument):
    pass


class PurchaseReturn(PurchaseDocument):
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.PROTECT,
        related_name="returns",
        null=True,
        blank=True,
    )


class PurchaseDocumentItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line_no = models.PositiveIntegerField()
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name_snapshot = models.CharField(max_length=200)
    unit_name_snapshot = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    line_amount = models.DecimalField(max_digits=18, decimal_places=2)

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
        ]


class PurchaseItem(PurchaseDocumentItem):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="items")

    class Meta(PurchaseDocumentItem.Meta):
        constraints = [
            *PurchaseDocumentItem.Meta.constraints,
            models.UniqueConstraint(
                fields=["purchase", "line_no"],
                name="purchases_purchase_item_purchase_line_no_unique",
            ),
        ]


class PurchaseReturnItem(PurchaseDocumentItem):
    purchase_return = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, related_name="items")
    purchase_item = models.ForeignKey(
        PurchaseItem,
        on_delete=models.PROTECT,
        related_name="return_items",
        null=True,
        blank=True,
    )

    class Meta(PurchaseDocumentItem.Meta):
        constraints = [
            *PurchaseDocumentItem.Meta.constraints,
            models.UniqueConstraint(
                fields=["purchase_return", "line_no"],
                name="purchases_purchase_return_item_return_line_no_unique",
            ),
        ]