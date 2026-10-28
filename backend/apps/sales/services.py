from decimal import Decimal, ROUND_HALF_UP

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError

from apps.accounts.models import Organization
from apps.common.document_numbers import save_document_with_number
from apps.inventory.models import IdempotencyRecord, StockBalance, StockMovement
from apps.partners.models import Customer
from apps.products.models import Product

from .models import SalesOrder, SalesOrderItem, SalesReturn, SalesReturnItem


class SalesConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "sales_conflict"
    default_detail = "The sales document cannot be completed in its current state."


class InsufficientStock(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "insufficient_stock"
    default_detail = "库存不足，无法完成销售单。"


def _quantize_amount(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _quantize_cost(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _validate_draft_values(*, organization: Organization, values: dict) -> tuple[Customer | None, list[dict]]:
    customer = None
    if customer_id := values.get("customer_id"):
        customer = Customer.objects.filter(
            id=customer_id, organization=organization, is_active=True
        ).first()
        if customer is None:
            raise ValidationError({"customer_id": ["当前组织中未找到启用的客户。"]})

    items = values["items"]
    product_ids = [item["product_id"] for item in items]
    if len(product_ids) != len(set(product_ids)):
        raise ValidationError({"items": ["同一单据中商品不能重复添加。"]})
    products = {
        product.id: product
        for product in Product.objects.select_related("unit").filter(
            id__in=product_ids, organization=organization, is_active=True
        )
    }
    if len(products) != len(product_ids):
        raise ValidationError({"items": ["当前组织中未找到商品，或商品已停用。"]})
    return customer, [{**item, "product": products[item["product_id"]]} for item in items]


def _validate_return_values(*, organization: Organization, values: dict) -> tuple[SalesOrder, Customer | None, list[dict]]:
    sales_order = (
        SalesOrder.objects.select_related("customer")
        .filter(id=values["sales_order_id"], organization=organization, status=SalesOrder.Status.COMPLETED)
        .first()
    )
    if sales_order is None:
        raise ValidationError({"sales_order_id": ["当前组织中未找到已完成的销售单。"]})
    customer, items = _validate_draft_values(organization=organization, values=values)
    if customer is not None and customer.id != sales_order.customer_id:
        raise ValidationError({"customer_id": ["客户必须与原销售单一致。"]})
    customer = sales_order.customer
    source_item_ids = [item["sales_order_item_id"] for item in items]
    if len(source_item_ids) != len(set(source_item_ids)):
        raise ValidationError({"items": ["同一张退货单中，原销售明细不能重复添加。"]})
    source_items = {
        item.id: item
        for item in SalesOrderItem.objects.filter(id__in=source_item_ids, sales_order=sales_order)
    }
    if len(source_items) != len(source_item_ids):
        raise ValidationError({"items": ["原销售明细不属于所选销售单。"]})
    normalized_items = []
    for item in items:
        source_item = source_items[item["sales_order_item_id"]]
        if item["product"].id != source_item.product_id:
            raise ValidationError({"items": ["退货商品必须与原销售明细一致。"]})
        normalized_items.append({**item, "source_item": source_item, "unit_price": source_item.unit_price})
    return sales_order, customer, normalized_items


def _document_field_name(item_model, document) -> str:
    return next(
        field.name
        for field in item_model._meta.fields
        if getattr(field.remote_field, "model", None) is document.__class__
    )


def _replace_items(*, document, item_model, items: list[dict]) -> Decimal:
    document_field = _document_field_name(item_model, document)
    source_item_field = next(
        (field.name for field in item_model._meta.fields if field.name.endswith("_item")),
        None,
    )
    item_model.objects.filter(**{document_field: document}).delete()
    document_items = []
    total_amount = Decimal("0.00")
    for line_no, item in enumerate(items, start=1):
        product = item["product"]
        line_amount = _quantize_amount(item["quantity"] * item["unit_price"])
        total_amount += line_amount
        item_values = {
            document_field: document,
            "line_no": line_no,
            "product": product,
            "product_name_snapshot": product.name,
            "unit_name_snapshot": product.unit.name,
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "line_amount": line_amount,
        }
        if source_item_field is not None and "source_item" in item:
            item_values[source_item_field] = item["source_item"]
        document_items.append(item_model(**item_values))
    item_model.objects.bulk_create(document_items)
    return _quantize_amount(total_amount)


@transaction.atomic
def create_draft(*, model, item_model, prefix: str, organization: Organization, user, values: dict):
    customer, items = _validate_draft_values(organization=organization, values=values)
    document = model(
        organization=organization,
        customer=customer,
        occurred_on=values["occurred_on"],
        remark=values.get("remark", ""),
        created_by_user=user,
        updated_by_user=user,
    )
    save_document_with_number(document=document, prefix=prefix)
    document.total_amount = _replace_items(document=document, item_model=item_model, items=items)
    document.save(update_fields=["total_amount", "updated_at"])
    return document


@transaction.atomic
def update_draft(*, document, item_model, user, values: dict):
    if document.status != document.Status.DRAFT:
        raise SalesConflict("已完成的单据不可编辑。")
    merged_values = {
        "customer_id": values.get("customer_id", document.customer_id),
        "occurred_on": values.get("occurred_on", document.occurred_on),
        "remark": values.get("remark", document.remark),
        "items": values.get(
            "items",
            [
                {"product_id": item.product_id, "quantity": item.quantity, "unit_price": item.unit_price}
                for item in document.items.all()
            ],
        ),
    }
    customer, items = _validate_draft_values(organization=document.organization, values=merged_values)
    document.customer = customer
    document.occurred_on = merged_values["occurred_on"]
    document.remark = merged_values["remark"]
    document.updated_by_user = user
    document.total_amount = _replace_items(document=document, item_model=item_model, items=items)
    document.save()
    return document


def _existing_idempotent_document(*, organization: Organization, action: str, idempotency_key: str, resource_id):
    record = IdempotencyRecord.objects.select_for_update().filter(
        organization=organization, action=action, idempotency_key=idempotency_key
    ).first()
    if record is None:
        return None
    if record.resource_id != resource_id:
        raise SalesConflict("该幂等键已用于其他单据。")
    return record


@transaction.atomic
def delete_document(*, model, item_model, document_id, organization: Organization) -> None:
    document = model.objects.select_for_update().filter(id=document_id, organization=organization).first()
    if document is None:
        raise model.DoesNotExist
    if hasattr(document, "returns") and document.returns.exists():
        raise SalesConflict("存在关联的退货单，不能删除原销售单。")
    if document.status == document.Status.COMPLETED:
        document_field = _document_field_name(item_model, document)
        items = list(item_model.objects.filter(**{document_field: document}))
        movements = list(
            StockMovement.objects.filter(
                organization=organization,
                source_type=model._meta.label,
                source_id=document.id,
            ).order_by("id")
        )
        if len(movements) != len(items):
            raise SalesConflict("单据库存流水不完整，不能删除。")
        balances = {
            balance.product_id: balance
            for balance in StockBalance.objects.select_for_update().filter(
                organization=organization,
                product_id__in={item.product_id for item in items},
            )
        }
        for movement in movements:
            balance = balances.get(movement.product_id)
            if balance is None or balance.quantity - movement.quantity_delta < 0:
                raise SalesConflict("删除单据后库存不足，不能删除。")
            balance.quantity -= movement.quantity_delta
            balance.save(update_fields=["quantity", "updated_at"])
        StockMovement.objects.filter(id__in=[movement.id for movement in movements]).delete()
        IdempotencyRecord.objects.filter(
            organization=organization,
            resource_type=model._meta.label,
            resource_id=document.id,
        ).delete()
    document.delete()


@transaction.atomic
def complete_draft(*, model, item_model, movement_type: str, action: str, document_id, organization: Organization, user, idempotency_key: str, source_item_field: str | None = None):
    document = model.objects.select_for_update().filter(id=document_id, organization=organization).first()
    if document is None:
        raise model.DoesNotExist
    if _existing_idempotent_document(
        organization=organization,
        action=action,
        idempotency_key=idempotency_key,
        resource_id=document.id,
    ):
        return document
    if document.status != document.Status.DRAFT:
        raise SalesConflict()

    document_field = _document_field_name(item_model, document)
    related_fields = ["product"]
    if source_item_field is not None:
        related_fields.append(source_item_field)
    items = list(item_model.objects.select_related(*related_fields).filter(**{document_field: document}))
    if source_item_field is not None:
        source_item_ids = [getattr(item, f"{source_item_field}_id") for item in items]
        source_item_model = item_model._meta.get_field(source_item_field).remote_field.model
        source_items = {
            item.id: item
            for item in source_item_model.objects.select_for_update().filter(id__in=source_item_ids)
        }
        returned_quantities = dict(
            item_model.objects.filter(
                **{
                    f"{source_item_field}_id__in": source_item_ids,
                    f"{document_field}__status": document.Status.COMPLETED,
                }
            )
            .values_list(f"{source_item_field}_id")
            .annotate(total_quantity=Sum("quantity"))
        )
        for item in items:
            source_item = source_items[item.sales_order_item_id]
            if returned_quantities.get(source_item.id, Decimal("0.0000")) + item.quantity > source_item.quantity:
                raise SalesConflict("Return quantity exceeds the original sales item quantity.")
    product_ids = sorted({item.product_id for item in items}, key=str)
    balances = {
        balance.product_id: balance
        for balance in StockBalance.objects.select_for_update().filter(
            organization=organization, product_id__in=product_ids
        ).order_by("product_id")
    }
    if len(balances) != len(product_ids):
        raise SalesConflict("商品缺少库存记录，无法完成单据。")
    products = {
        product.id: product
        for product in Product.objects.select_for_update().filter(
            id__in=product_ids, organization=organization
        ).order_by("id")
    }
    if len(products) != len(product_ids):
        raise SalesConflict("商品不存在，无法完成单据。")
    if movement_type == StockMovement.MovementType.SALE:
        for item in items:
            if balances[item.product_id].quantity < item.quantity:
                raise InsufficientStock()

    quantity_sign = Decimal("-1") if movement_type == StockMovement.MovementType.SALE else Decimal("1")
    for item in items:
        item.unit_cost_snapshot = (
            source_items[item.sales_order_item_id].unit_cost_snapshot
            if source_item_field is not None
            else products[item.product_id].purchase_price
        )
        item.cost_amount = _quantize_cost(item.quantity * item.unit_cost_snapshot)
        item.save(update_fields=["unit_cost_snapshot", "cost_amount"])
        balance = balances[item.product_id]
        balance.quantity += quantity_sign * item.quantity
        balance.save(update_fields=["quantity", "updated_at"])
        StockMovement.objects.create(
            organization=organization,
            product=item.product,
            movement_type=movement_type,
            quantity_delta=quantity_sign * item.quantity,
            source_type=model._meta.label,
            source_id=document.id,
            operator_user=user,
        )
    document.status = document.Status.COMPLETED
    document.completed_by_user = user
    document.completed_at = timezone.now()
    document.updated_by_user = user
    document.save()
    try:
        IdempotencyRecord.objects.create(
            organization=organization,
            action=action,
            idempotency_key=idempotency_key,
            resource_type=model._meta.label,
            resource_id=document.id,
            response_status=status.HTTP_200_OK,
        )
    except IntegrityError as error:
        raise SalesConflict("该幂等键正在被其他请求处理。") from error
    return document


def create_sales_order(*, organization: Organization, user, values: dict) -> SalesOrder:
    return create_draft(
        model=SalesOrder,
        item_model=SalesOrderItem,
        prefix="SO",
        organization=organization,
        user=user,
        values=values,
    )


def update_sales_order(*, document: SalesOrder, user, values: dict) -> SalesOrder:
    return update_draft(document=document, item_model=SalesOrderItem, user=user, values=values)


def complete_sales_order(*, document_id, organization: Organization, user, idempotency_key: str) -> SalesOrder:
    return complete_draft(
        model=SalesOrder,
        item_model=SalesOrderItem,
        movement_type=StockMovement.MovementType.SALE,
        action="sales_order.complete",
        document_id=document_id,
        organization=organization,
        user=user,
        idempotency_key=idempotency_key,
    )


def create_sales_return(*, organization: Organization, user, values: dict) -> SalesReturn:
    sales_order, customer, items = _validate_return_values(organization=organization, values=values)
    document = SalesReturn(
        organization=organization,
        sales_order=sales_order,
        customer=customer,
        occurred_on=values["occurred_on"],
        remark=values.get("remark", ""),
        created_by_user=user,
        updated_by_user=user,
    )
    save_document_with_number(document=document, prefix="SR")
    document.total_amount = _replace_items(document=document, item_model=SalesReturnItem, items=items)
    document.save(update_fields=["total_amount", "updated_at"])
    return document


def update_sales_return(*, document: SalesReturn, user, values: dict) -> SalesReturn:
    if document.status != document.Status.DRAFT:
        raise SalesConflict("已完成的单据不可编辑。")
    if "sales_order_id" in values and values["sales_order_id"] != document.sales_order_id:
        raise ValidationError({"sales_order_id": ["原销售单不可更改。"]})
    merged_values = {
        "sales_order_id": document.sales_order_id,
        "customer_id": values.get("customer_id", document.customer_id),
        "occurred_on": values.get("occurred_on", document.occurred_on),
        "remark": values.get("remark", document.remark),
        "items": values.get(
            "items",
            [
                {
                    "product_id": item.product_id,
                    "sales_order_item_id": item.sales_order_item_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                }
                for item in document.items.all()
            ],
        ),
    }
    sales_order, customer, items = _validate_return_values(
        organization=document.organization, values=merged_values
    )
    document.sales_order = sales_order
    document.customer = customer
    document.occurred_on = merged_values["occurred_on"]
    document.remark = merged_values["remark"]
    document.updated_by_user = user
    document.total_amount = _replace_items(document=document, item_model=SalesReturnItem, items=items)
    document.save()
    return document


def complete_sales_return(*, document_id, organization: Organization, user, idempotency_key: str) -> SalesReturn:
    return complete_draft(
        model=SalesReturn,
        item_model=SalesReturnItem,
        movement_type=StockMovement.MovementType.SALE_RETURN,
        action="sales_return.complete",
        document_id=document_id,
        organization=organization,
        user=user,
        idempotency_key=idempotency_key,
        source_item_field="sales_order_item",
    )


def delete_sales_order(*, document_id, organization: Organization) -> None:
    delete_document(
        model=SalesOrder,
        item_model=SalesOrderItem,
        document_id=document_id,
        organization=organization,
    )


def delete_sales_return(*, document_id, organization: Organization) -> None:
    delete_document(
        model=SalesReturn,
        item_model=SalesReturnItem,
        document_id=document_id,
        organization=organization,
    )