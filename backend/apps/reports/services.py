from datetime import date
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce

from apps.inventory.models import StockBalance
from apps.purchases.models import Purchase, PurchaseReturn
from apps.sales.models import SalesOrder, SalesReturn


ZERO_AMOUNT = Decimal("0.00")
ZERO_QUANTITY = Decimal("0.0000")
ZERO_COST = Decimal("0.000000")


def _document_totals(queryset, item_relation: str, include_cost: bool = False) -> dict[str, int | Decimal]:
    documents = queryset.aggregate(
        count=Count("id"),
        amount=Coalesce(Sum("total_amount"), ZERO_AMOUNT),
    )
    quantity = queryset.aggregate(
        quantity=Coalesce(Sum(f"{item_relation}__quantity"), ZERO_QUANTITY)
    )["quantity"]
    cost = ZERO_COST
    if include_cost:
        cost = queryset.aggregate(
            cost=Coalesce(Sum(f"{item_relation}__cost_amount"), ZERO_COST)
        )["cost"]
    return {**documents, "quantity": quantity, "cost": cost}


def sales_report(organization, date_from: date, date_to: date) -> dict[str, int | Decimal]:
    orders = _document_totals(
        SalesOrder.objects.filter(
            organization=organization,
            status=SalesOrder.Status.COMPLETED,
            occurred_on__range=(date_from, date_to),
        ),
        "items",
        include_cost=True,
    )
    returns = _document_totals(
        SalesReturn.objects.filter(
            organization=organization,
            status=SalesReturn.Status.COMPLETED,
            occurred_on__range=(date_from, date_to),
        ),
        "items",
        include_cost=True,
    )
    net_amount = orders["amount"] - returns["amount"]
    net_cost = orders["cost"] - returns["cost"]
    return {
        "sales_order_count": orders["count"],
        "sales_quantity": orders["quantity"],
        "sales_amount": orders["amount"],
        "sales_return_quantity": returns["quantity"],
        "sales_return_amount": returns["amount"],
        "net_sales_quantity": orders["quantity"] - returns["quantity"],
        "net_sales_amount": net_amount,
        "sales_cost": orders["cost"],
        "sales_return_cost": returns["cost"],
        "net_sales_cost": net_cost,
        "gross_profit": net_amount - net_cost,
    }


def purchase_report(organization, date_from: date, date_to: date) -> dict[str, int | Decimal]:
    purchases = _document_totals(
        Purchase.objects.filter(
            organization=organization,
            status=Purchase.Status.COMPLETED,
            occurred_on__range=(date_from, date_to),
        ),
        "items",
    )
    returns = _document_totals(
        PurchaseReturn.objects.filter(
            organization=organization,
            status=PurchaseReturn.Status.COMPLETED,
            occurred_on__range=(date_from, date_to),
        ),
        "items",
    )
    return {
        "purchase_count": purchases["count"],
        "purchase_quantity": purchases["quantity"],
        "purchase_amount": purchases["amount"],
        "purchase_return_quantity": returns["quantity"],
        "purchase_return_amount": returns["amount"],
        "net_purchase_quantity": purchases["quantity"] - returns["quantity"],
        "net_purchase_amount": purchases["amount"] - returns["amount"],
    }


def inventory_report(organization) -> dict[str, int | Decimal]:
    return StockBalance.objects.filter(organization=organization).aggregate(
        product_count=Count("id"),
        in_stock_product_count=Count("id", filter=Q(quantity__gt=0)),
        out_of_stock_product_count=Count("id", filter=Q(quantity__lte=0)),
        total_quantity=Coalesce(Sum("quantity"), ZERO_QUANTITY),
        total_amount=Coalesce(
            Sum(ExpressionWrapper(
                F("quantity") * F("product__purchase_price"),
                output_field=DecimalField(max_digits=38, decimal_places=6),
            )),
            ZERO_COST,
        ),
    )