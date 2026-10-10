import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.accounts.models import Organization, TimestampedModel
from apps.partners.models import PriceLevel, Supplier


class Unit(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="units")
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="products_unit_organization_name_unique",
            )
        ]
        indexes = [models.Index(fields=["organization", "is_active", "created_at"])]


class Specification(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="specifications",
    )
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="products_specification_organization_name_unique",
            )
        ]
        indexes = [models.Index(fields=["organization", "is_active", "created_at"])]


class ProductAttribute(TimestampedModel):
    class InputType(models.TextChoices):
        TEXT = "TEXT", "Text"
        SELECT = "SELECT", "Select"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="product_attributes",
    )
    name = models.CharField(max_length=50)
    input_type = models.CharField(max_length=16, choices=InputType.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="products_attribute_organization_name_unique",
            )
        ]
        indexes = [models.Index(fields=["organization", "is_active", "created_at"])]


class AttributeOption(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.PROTECT,
        related_name="options",
    )
    value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["attribute", "value"],
                name="products_attribute_option_attribute_value_unique",
            )
        ]


class Product(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="products")
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    purchase_price = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    specification = models.CharField(max_length=100, blank=True)
    remark = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_products",
    )
    updated_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_products",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(purchase_price__gte=0),
                name="products_product_purchase_price_nonnegative",
            ),
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="products_product_organization_name_unique",
            )
        ]
        indexes = [models.Index(fields=["organization", "is_active", "created_at"])]


class ProductSpecificationValue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specification_values")
    specification = models.ForeignKey(
        Specification,
        on_delete=models.PROTECT,
        related_name="product_values",
    )
    value = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "specification"],
                name="products_product_specification_value_unique",
            )
        ]


class ProductAttributeValue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attribute_values")
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.PROTECT,
        related_name="product_values",
    )
    text_value = models.CharField(max_length=500, null=True, blank=True)
    option = models.ForeignKey(
        AttributeOption,
        on_delete=models.PROTECT,
        related_name="product_values",
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "attribute"],
                name="products_product_attribute_value_unique",
            ),
            models.CheckConstraint(
                condition=(
                    Q(text_value__isnull=False, option__isnull=True)
                    | Q(text_value__isnull=True, option__isnull=False)
                ),
                name="products_product_attribute_value_value_kind_valid",
            ),
        ]


class ProductPrice(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="prices")
    price_level = models.ForeignKey(PriceLevel, on_delete=models.PROTECT, related_name="product_prices")
    amount = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "price_level"],
                name="products_product_price_product_level_unique",
            ),
            models.CheckConstraint(
                condition=Q(amount__gte=0),
                name="products_product_price_amount_nonnegative",
            ),
        ]