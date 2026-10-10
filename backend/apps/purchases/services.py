from decimal import Decimal, ROUND_HALF_UP

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError

from apps.accounts.models import Organization
from apps.inventory.models import IdempotencyRecord, StockBalance, StockMovement
from apps.partners.models import Supplier
from apps.products.models import Product

from .models import Purchase, PurchaseItem, PurchaseReturn, PurchaseReturnItem


class PurchaseConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "purchase_conflict"
    default_detail = "The purchase document cannot be completed in its current state."


def _quantize_amount(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _validate_draft_values(*, organization: Organization, values: dict) -> tuple[Supplier | None, list[dict]]:
    supplier = None
    if supplier_id := values.get("supplier_id"):
        supplier = Supplier.objects.filter(
            id=supplier_id, organization=organization, is_active=True
        ).first()
        if supplier is None:
            raise ValidationError({"supplier_id": ["当前组织中未找到启用的供应商。"]})
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
    return supplier, [
        {
            **item,
            "product": products[item["product_id"]],
            "unit_price": item.get("unit_price", products[item["product_id"]].purchase_price),
        }
        for item in items
    ]


def _validate_return_values(*, organization: Organization, values: dict) -> tuple[Purchase | None, Supplier | None, list[dict]]:
    purchase = None
    if purchase_id := values.get("purchase_id"):
        purchase = (
            Purchase.objects.select_related("supplier")
            .filter(id=purchase_id, organization=organization, status=Purchase.Status.COMPLETED)
            .first()
        )
        if purchase is None:
            raise ValidationError({"purchase_id": ["当前组织中未找到已完成的进货单。"]})
    supplier, items = _validate_draft_values(organization=organization, values=values)
    if purchase is None:
        if any(item.get("purchase_item_id") for item in items):
            raise ValidationError({"items": ["未选择原采购单时，不能关联原采购明细。"]})
        return None, supplier, items
    if supplier is not None and supplier.id != purchase.supplier_id:
        raise ValidationError({"supplier_id": ["供应商必须与原采购单一致。"]})
    supplier = purchase.supplier
    source_item_ids = [item["purchase_item_id"] for item in items]
    if any(source_item_id is None for source_item_id in source_item_ids):
        raise ValidationError({"items": ["选择原采购单后，请从原采购明细中填写退货数量。"]})
    if len(source_item_ids) != len(set(source_item_ids)):
        raise ValidationError({"items": ["同一张退货单中，原采购明细不能重复添加。"]})
    source_items = {
        item.id: item
        for item in PurchaseItem.objects.filter(id__in=source_item_ids, purchase=purchase)
    }
    if len(source_items) != len(source_item_ids):
        raise ValidationError({"items": ["原采购明细不属于所选采购单。"]})
    normalized_items = []
    for item in items:
        source_item = source_items[item["purchase_item_id"]]
        if item["product"].id != source_item.product_id:
            raise ValidationError({"items": ["退货商品必须与原采购明细一致。"]})
        normalized_items.append({**item, "source_item": source_item, "unit_price": source_item.unit_price})
    return purchase, supplier, normalized_items


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
    total_amount = Decimal("0.00")
    document_items = []
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


def _document_no(prefix: str, document_id) -> str:
    return f"{prefix}-{document_id.hex[:12].upper()}"


@transaction.atomic
def create_draft(*, model, item_model, prefix: str, organization: Organization, user, values: dict):
    supplier, items = _validate_draft_values(organization=organization, values=values)
    document = model(
        organization=organization,
        supplier=supplier,
        occurred_on=values["occurred_on"],
        remark=values.get("remark", ""),
        created_by_user=user,
        updated_by_user=user,
    )
    document.document_no = _document_no(prefix, document.id)
    document.save()
    document.total_amount = _replace_items(document=document, item_model=item_model, items=items)
    document.save(update_fields=["total_amount", "updated_at"])
    return document


@transaction.atomic
def update_draft(*, document, item_model, user, values: dict):
    if document.status != document.Status.DRAFT:
        raise PurchaseConflict("已完成的单据不可编辑。")
    merged_values = {
        "supplier_id": values.get("supplier_id", document.supplier_id),
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
    supplier, items = _validate_draft_values(organization=document.organization, values=merged_values)
    document.supplier = supplier
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
        raise PurchaseConflict("该幂等键已用于其他单据。")
    return record


@transaction.atomic
def delete_document(*, model, item_model, document_id, organization: Organization) -> None:
    document = model.objects.select_for_update().filter(id=document_id, organization=organization).first()
    if document is None:
        raise model.DoesNotExist
    if hasattr(document, "returns") and document.returns.exists():
        raise PurchaseConflict("存在关联的退货单，不能删除原进货单。")
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
            raise PurchaseConflict("单据库存流水不完整，不能删除。")
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
                raise PurchaseConflict("删除单据后库存不足，不能删除。")
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
        raise PurchaseConflict()
    document_field = _document_field_name(item_model, document)
    related_fields = ["product"]
    if source_item_field is not None:
        related_fields.append(source_item_field)
    items = list(item_model.objects.select_related(*related_fields).filter(**{document_field: document}))
    if source_item_field is not None:
        source_item_ids = [getattr(item, f"{source_item_field}_id") for item in items]
        if any(source_item_ids):
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
                source_item = source_items[item.purchase_item_id]
                if returned_quantities.get(source_item.id, Decimal("0.0000")) + item.quantity > source_item.quantity:
                    raise PurchaseConflict("退货数量不能超过原采购数量。")
    product_ids = sorted({item.product_id for item in items}, key=str)
    balances = {
        balance.product_id: balance
        for balance in StockBalance.objects.select_for_update().filter(
            organization=organization, product_id__in=product_ids
        ).order_by("product_id")
    }
    if len(balances) != len(product_ids):
        raise PurchaseConflict("商品缺少库存记录，无法完成单据。")
    if movement_type == StockMovement.MovementType.PURCHASE_RETURN:
        for item in items:
            if balances[item.product_id].quantity < item.quantity:
                raise PurchaseConflict("库存不足，无法完成进货退货。")
    quantity_sign = Decimal("1") if movement_type == StockMovement.MovementType.PURCHASE else Decimal("-1")
    for item in items:
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
        raise PurchaseConflict("该幂等键正在被其他请求处理。") from error
    return document


def create_purchase(*, organization: Organization, user, values: dict) -> Purchase:
    return create_draft(model=Purchase, item_model=PurchaseItem, prefix="PO", organization=organization, user=user, values=values)


def update_purchase(*, document: Purchase, user, values: dict) -> Purchase:
    return update_draft(document=document, item_model=PurchaseItem, user=user, values=values)


def complete_purchase(*, document_id, organization: Organization, user, idempotency_key: str) -> Purchase:
    return complete_draft(model=Purchase, item_model=PurchaseItem, movement_type=StockMovement.MovementType.PURCHASE, action="purchase.complete", document_id=document_id, organization=organization, user=user, idempotency_key=idempotency_key)


def delete_purchase(*, document_id, organization: Organization) -> None:
    delete_document(
        model=Purchase,
        item_model=PurchaseItem,
        document_id=document_id,
        organization=organization,
    )


def create_purchase_return(*, organization: Organization, user, values: dict) -> PurchaseReturn:
    purchase, supplier, items = _validate_return_values(organization=organization, values=values)
    document = PurchaseReturn(
        organization=organization,
        purchase=purchase,
        supplier=supplier,
        occurred_on=values["occurred_on"],
        remark=values.get("remark", ""),
        created_by_user=user,
        updated_by_user=user,
    )
    document.document_no = _document_no("PR", document.id)
    document.save()
    document.total_amount = _replace_items(document=document, item_model=PurchaseReturnItem, items=items)
    document.save(update_fields=["total_amount", "updated_at"])
    return document


def update_purchase_return(*, document: PurchaseReturn, user, values: dict) -> PurchaseReturn:
    if document.status != document.Status.DRAFT:
        raise PurchaseConflict("已完成的单据不可编辑。")
    merged_values = {
        "purchase_id": values.get("purchase_id", document.purchase_id),
        "supplier_id": values.get("supplier_id", document.supplier_id),
        "occurred_on": values.get("occurred_on", document.occurred_on),
        "remark": values.get("remark", document.remark),
        "items": values.get(
            "items",
            [
                {
                    "product_id": item.product_id,
                    "purchase_item_id": item.purchase_item_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                }
                for item in document.items.all()
            ],
        ),
    }
    purchase, supplier, items = _validate_return_values(
        organization=document.organization, values=merged_values
    )
    document.purchase = purchase
    document.supplier = supplier
    document.occurred_on = merged_values["occurred_on"]
    document.remark = merged_values["remark"]
    document.updated_by_user = user
    document.total_amount = _replace_items(document=document, item_model=PurchaseReturnItem, items=items)
    document.save()
    return document


def complete_purchase_return(*, document_id, organization: Organization, user, idempotency_key: str) -> PurchaseReturn:
    return complete_draft(
        model=PurchaseReturn,
        item_model=PurchaseReturnItem,
        movement_type=StockMovement.MovementType.PURCHASE_RETURN,
        action="purchase_return.complete",
        document_id=document_id,
        organization=organization,
        user=user,
        idempotency_key=idempotency_key,
        source_item_field="purchase_item",
    )


def delete_purchase_return(*, document_id, organization: Organization) -> None:
    delete_document(
        model=PurchaseReturn,
        item_model=PurchaseReturnItem,
        document_id=document_id,
        organization=organization,
    )