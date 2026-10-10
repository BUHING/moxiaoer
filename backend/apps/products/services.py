from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.accounts.models import Organization
from apps.inventory.models import StockBalance, StockMovement
from apps.partners.models import PriceLevel, Supplier

from .models import (
    AttributeOption,
    Product,
    ProductAttribute,
    ProductAttributeValue,
    ProductPrice,
    ProductSpecificationValue,
    Specification,
    Unit,
)

DEFAULT_UNITS = ("个", "张", "包", "瓶", "盒", "袋", "件", "公斤", "米")
DEFAULT_SPECIFICATIONS = ("尺码", "颜色")
DEFAULT_PRICE_LEVELS = (("零售价", 0), ("批发价", 1))


def initialize_organization_catalog(*, organization: Organization) -> None:
    Unit.objects.bulk_create(
        [Unit(organization=organization, name=name) for name in DEFAULT_UNITS],
        ignore_conflicts=True,
    )
    Specification.objects.bulk_create(
        [Specification(organization=organization, name=name) for name in DEFAULT_SPECIFICATIONS],
        ignore_conflicts=True,
    )
    PriceLevel.objects.bulk_create(
        [
            PriceLevel(organization=organization, name=name, sort_order=sort_order)
            for name, sort_order in DEFAULT_PRICE_LEVELS
        ],
        ignore_conflicts=True,
    )


def _organization_object(model, object_id, organization: Organization, field_name: str):
    instance = model.objects.filter(id=object_id, organization=organization).first()
    if instance is None:
        raise ValidationError({field_name: ["Object was not found in the current organization."]})
    return instance


def _validate_product_values(
    *, organization: Organization, values: dict, require_active_supplier: bool = True
) -> tuple:
    unit = _organization_object(Unit, values["unit_id"], organization, "unit_id")
    if not unit.is_active:
        raise ValidationError({"unit_id": ["Inactive units cannot be selected."]})

    supplier = None
    if supplier_id := values.get("supplier_id"):
        supplier = _organization_object(Supplier, supplier_id, organization, "supplier_id")
        if require_active_supplier and not supplier.is_active:
            raise ValidationError({"supplier_id": ["Inactive suppliers cannot be selected."]})

    specification_values = values.get("specification_values", [])
    specification_ids = [item["specification_id"] for item in specification_values]
    if len(specification_ids) != len(set(specification_ids)):
        raise ValidationError({"specification_values": ["Each specification can be used only once."]})
    specifications = {
        item.id: item
        for item in Specification.objects.filter(id__in=specification_ids, organization=organization)
    }
    if len(specifications) != len(specification_ids):
        raise ValidationError({"specification_values": ["Specification was not found in the current organization."]})

    attribute_values = values.get("attribute_values", [])
    attribute_ids = [item["attribute_id"] for item in attribute_values]
    if len(attribute_ids) != len(set(attribute_ids)):
        raise ValidationError({"attribute_values": ["Each attribute can be used only once."]})
    attributes = {
        item.id: item
        for item in ProductAttribute.objects.filter(id__in=attribute_ids, organization=organization)
    }
    if len(attributes) != len(attribute_ids):
        raise ValidationError({"attribute_values": ["Attribute was not found in the current organization."]})

    options = {}
    for item in attribute_values:
        attribute = attributes[item["attribute_id"]]
        text_value = item.get("text_value")
        option_id = item.get("option_id")
        if attribute.input_type == ProductAttribute.InputType.TEXT:
            if not text_value or option_id:
                raise ValidationError({"attribute_values": ["Text attributes require a text value."]})
        elif not option_id or text_value:
            raise ValidationError({"attribute_values": ["Select attributes require an option."]})
        if option_id:
            option = AttributeOption.objects.filter(id=option_id, attribute=attribute, is_active=True).first()
            if option is None:
                raise ValidationError({"attribute_values": ["Option was not found or is inactive."]})
            options[option.id] = option

    prices = values.get("prices", [])
    price_level_ids = [item["price_level_id"] for item in prices]
    if len(price_level_ids) != len(set(price_level_ids)):
        raise ValidationError({"prices": ["Each price level can be used only once."]})
    price_levels = {
        item.id: item
        for item in PriceLevel.objects.filter(id__in=price_level_ids, organization=organization, is_active=True)
    }
    if len(price_levels) != len(price_level_ids):
        raise ValidationError({"prices": ["Price level was not found or is inactive."]})
    return unit, supplier, specifications, attributes, options, price_levels


def _replace_product_details(*, product: Product, values: dict, validated: tuple) -> None:
    _, _, specifications, attributes, options, price_levels = validated
    ProductSpecificationValue.objects.filter(product=product).delete()
    ProductAttributeValue.objects.filter(product=product).delete()
    ProductPrice.objects.filter(product=product).delete()
    ProductSpecificationValue.objects.bulk_create(
        [
            ProductSpecificationValue(
                product=product,
                specification=specifications[item["specification_id"]],
                value=item["value"],
            )
            for item in values.get("specification_values", [])
        ]
    )
    ProductAttributeValue.objects.bulk_create(
        [
            ProductAttributeValue(
                product=product,
                attribute=attributes[item["attribute_id"]],
                text_value=item.get("text_value"),
                option=options.get(item.get("option_id")),
            )
            for item in values.get("attribute_values", [])
        ]
    )
    ProductPrice.objects.bulk_create(
        [
            ProductPrice(
                product=product,
                price_level=price_levels[item["price_level_id"]],
                amount=item["amount"],
            )
            for item in values.get("prices", [])
        ]
    )


@transaction.atomic
def create_product(*, organization: Organization, user, values: dict) -> Product:
    initial_quantity = values.pop("initial_quantity", Decimal("0"))
    validated = _validate_product_values(organization=organization, values=values)
    product = Product.objects.create(
        organization=organization,
        name=values["name"],
        unit=validated[0],
        supplier=validated[1],
        purchase_price=values.get("purchase_price", Decimal("0.00")),
        specification=values.get("specification", ""),
        remark=values.get("remark", ""),
        created_by_user=user,
        updated_by_user=user,
    )
    _replace_product_details(product=product, values=values, validated=validated)
    StockBalance.objects.create(organization=organization, product=product, quantity=initial_quantity)
    if initial_quantity:
        StockMovement.objects.create(
            organization=organization,
            product=product,
            movement_type=StockMovement.MovementType.INITIAL,
            quantity_delta=initial_quantity,
            source_type="PRODUCT",
            source_id=product.id,
            operator_user=user,
        )
    return product


@transaction.atomic
def update_product(*, product: Product, user, values: dict) -> Product:
    merged_values = {
        "name": values.get("name", product.name),
        "unit_id": values.get("unit_id", product.unit_id),
        "supplier_id": values.get("supplier_id", product.supplier_id),
        "purchase_price": values.get("purchase_price", product.purchase_price),
        "specification": values.get("specification", product.specification),
        "remark": values.get("remark", product.remark),
        "specification_values": values.get(
            "specification_values",
            list(product.specification_values.values("specification_id", "value")),
        ),
        "attribute_values": values.get(
            "attribute_values",
            list(product.attribute_values.values("attribute_id", "text_value", "option_id")),
        ),
        "prices": values.get("prices", list(product.prices.values("price_level_id", "amount"))),
    }
    validated = _validate_product_values(
        organization=product.organization,
        values=merged_values,
        require_active_supplier="supplier_id" in values,
    )
    product.name = merged_values["name"]
    product.unit = validated[0]
    product.supplier = validated[1]
    product.purchase_price = merged_values["purchase_price"]
    product.specification = merged_values["specification"]
    product.remark = merged_values["remark"]
    product.is_active = values.get("is_active", product.is_active)
    product.updated_by_user = user
    product.save()
    _replace_product_details(product=product, values=merged_values, validated=validated)
    return product