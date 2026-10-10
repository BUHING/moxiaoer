from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.inventory.models import StockBalance, StockMovement
from apps.partners.models import Customer
from apps.products.models import Product, Unit


PASSWORD = "NotACommonPassword123!"

pytestmark = pytest.mark.django_db


def register_and_login(client: APIClient, username: str) -> None:
    assert client.post(
        "/api/v1/auth/register/", {"username": username, "password": PASSWORD}, format="json"
    ).status_code == 201
    response = client.post(
        "/api/v1/auth/token/", {"username": username, "password": PASSWORD}, format="json"
    )
    assert response.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['access']}")


def create_customer_and_product(username: str, quantity: Decimal = Decimal("8.0000")) -> tuple[Customer, Product]:
    unit = Unit.objects.get(organization__owner_user__username=username, name="个")
    product = Product.objects.create(
        organization=unit.organization,
        name=f"{username} 商品",
        unit=unit,
        created_by_user=unit.organization.owner_user,
        updated_by_user=unit.organization.owner_user,
    )
    StockBalance.objects.create(organization=unit.organization, product=product, quantity=quantity)
    return (
        Customer.objects.create(organization=unit.organization, name=f"{username} 客户"),
        product,
    )


def sales_payload(customer: Customer, product: Product, quantity: str = "2.0000") -> dict:
    return {
        "customer_id": str(customer.id),
        "occurred_on": "2026-09-07",
        "remark": "销售备注 A-01",
        "items": [{"product_id": str(product.id), "quantity": quantity, "unit_price": "12.50"}],
    }

def sales_return_payload(order_data: dict, customer: Customer, product: Product, quantity: str) -> dict:
    return {
        **sales_payload(customer, product, quantity),
        "sales_order_id": order_data["id"],
        "items": [
            {
                "product_id": str(product.id),
                "sales_order_item_id": order_data["items"][0]["id"],
                "quantity": quantity,
                "unit_price": "0.00",
            }
        ],
    }


def test_sales_completion_updates_stock_once_and_completed_draft_is_read_only() -> None:
    client = APIClient()
    register_and_login(client, "boss-a")
    customer, product = create_customer_and_product("boss-a")

    created = client.post("/api/v1/sales-orders/", sales_payload(customer, product), format="json")
    assert created.status_code == 201, created.content
    order_id = created.data["data"]["id"]
    assert created.data["data"]["total_amount"] == "25.00"
    assert created.data["data"]["remark"] == "销售备注 A-01"

    assert client.get("/api/v1/sales-orders/?customer_id=invalid").status_code == 400
    assert client.post(
        f"/api/v1/sales-orders/{order_id}/complete/",
        HTTP_IDEMPOTENCY_KEY="x" * 256,
    ).status_code == 400

    completed = client.post(
        f"/api/v1/sales-orders/{order_id}/complete/",
        HTTP_IDEMPOTENCY_KEY="sales-order-1",
    )
    assert completed.status_code == 200, completed.content
    assert completed.data["data"]["status"] == "COMPLETED"
    assert StockBalance.objects.get(product=product).quantity == Decimal("6.0000")
    movement = StockMovement.objects.get(product=product)
    assert movement.movement_type == StockMovement.MovementType.SALE
    assert movement.quantity_delta == Decimal("-2.0000")

    replayed = client.post(
        f"/api/v1/sales-orders/{order_id}/complete/",
        HTTP_IDEMPOTENCY_KEY="sales-order-1",
    )
    assert replayed.status_code == 200
    assert replayed.data == completed.data
    assert StockMovement.objects.filter(product=product).count() == 1

    patched = client.patch(
        f"/api/v1/sales-orders/{order_id}/",
        {"items": [{"product_id": str(product.id), "quantity": "1.0000", "unit_price": "12.50"}]},
        format="json",
    )
    assert patched.status_code == 409
    assert StockBalance.objects.get(product=product).quantity == Decimal("6.0000")


def test_deleting_completed_sales_documents_reverses_stock_and_removes_movements() -> None:
    client = APIClient()
    register_and_login(client, "boss-delete-sales")
    customer, product = create_customer_and_product("boss-delete-sales")
    created = client.post("/api/v1/sales-orders/", sales_payload(customer, product), format="json")
    order_id = created.data["data"]["id"]
    assert client.post(
        f"/api/v1/sales-orders/{order_id}/complete/",
        HTTP_IDEMPOTENCY_KEY="delete-completed-sales",
    ).status_code == 200

    deleted = client.delete(f"/api/v1/sales-orders/{order_id}/")
    assert deleted.status_code == 204, deleted.content
    assert client.get(f"/api/v1/sales-orders/{order_id}/").status_code == 404
    assert StockBalance.objects.get(product=product).quantity == Decimal("8.0000")
    assert StockMovement.objects.filter(product=product).count() == 0


def test_sales_order_allows_an_empty_customer() -> None:
    client = APIClient()
    register_and_login(client, "sales-without-customer")
    _, product = create_customer_and_product("sales-without-customer")

    created = client.post(
        "/api/v1/sales-orders/",
        {
            "occurred_on": "2026-09-07",
            "items": [{"product_id": str(product.id), "quantity": "2.0000", "unit_price": "12.50"}],
        },
        format="json",
    )
    assert created.status_code == 201, created.content
    assert created.data["data"]["customer_id"] is None
    assert created.data["data"]["customer_name"] is None

    completed = client.post(
        f"/api/v1/sales-orders/{created.data['data']['id']}/complete/",
        HTTP_IDEMPOTENCY_KEY="sales-without-customer-1",
    )
    assert completed.status_code == 200, completed.content
    assert StockBalance.objects.get(product=product).quantity == Decimal("6.0000")


def test_sales_insufficient_stock_rolls_back_and_sales_return_increases_stock() -> None:
    client = APIClient()
    register_and_login(client, "boss-a")
    customer, product = create_customer_and_product("boss-a", Decimal("1.0000"))

    insufficient = client.post("/api/v1/sales-orders/", sales_payload(customer, product, "2.0000"), format="json")
    order_id = insufficient.data["data"]["id"]
    rejected = client.post(
        f"/api/v1/sales-orders/{order_id}/complete/",
        HTTP_IDEMPOTENCY_KEY="sales-order-insufficient",
    )
    assert rejected.status_code == 409
    assert rejected.data["code"] == "insufficient_stock"
    assert StockBalance.objects.get(product=product).quantity == Decimal("1.0000")
    assert StockMovement.objects.filter(product=product).count() == 0

    source_order = client.post(
        "/api/v1/sales-orders/", sales_payload(customer, product, "1.0000"), format="json"
    )
    assert client.post(
        f"/api/v1/sales-orders/{source_order.data['data']['id']}/complete/",
        HTTP_IDEMPOTENCY_KEY="sales-return-source",
    ).status_code == 200
    returned = client.post(
        "/api/v1/sales-returns/",
        sales_return_payload(source_order.data["data"], customer, product, "1.0000"),
        format="json",
    )
    assert returned.status_code == 201, returned.content
    return_id = returned.data["data"]["id"]
    completed_return = client.post(
        f"/api/v1/sales-returns/{return_id}/complete/",
        HTTP_IDEMPOTENCY_KEY="sales-return-1",
    )
    assert completed_return.status_code == 200
    assert StockBalance.objects.get(product=product).quantity == Decimal("1.0000")
    assert StockMovement.objects.order_by("occurred_at").last().movement_type == StockMovement.MovementType.SALE_RETURN


def test_sales_permissions_and_organization_isolation() -> None:
    boss_a = APIClient()
    register_and_login(boss_a, "boss-a")
    customer, product = create_customer_and_product("boss-a")
    created = boss_a.post("/api/v1/sales-orders/", sales_payload(customer, product), format="json")
    order_id = created.data["data"]["id"]

    employee_response = boss_a.post(
        "/api/v1/employees/",
        {"username": "employee-a", "display_name": "员工 A", "password": PASSWORD},
        format="json",
    )
    assert employee_response.status_code == 201
    employee = APIClient()
    login_response = employee.post(
        "/api/v1/auth/token/", {"username": "employee-a", "password": PASSWORD}, format="json"
    )
    employee.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['data']['access']}")
    assert employee.post("/api/v1/sales-orders/", sales_payload(customer, product), format="json").status_code == 201
    assert employee.post("/api/v1/sales-returns/", sales_payload(customer, product), format="json").status_code == 403

    boss_b = APIClient()
    register_and_login(boss_b, "boss-b")
    assert boss_b.get(f"/api/v1/sales-orders/{order_id}/").status_code == 404


def test_sales_report_uses_completed_orders_and_returns_to_calculate_net_amount() -> None:
    client = APIClient()
    register_and_login(client, "boss-a")
    customer, product = create_customer_and_product("boss-a")

    order = client.post("/api/v1/sales-orders/", sales_payload(customer, product), format="json")
    assert client.post(
        f"/api/v1/sales-orders/{order.data['data']['id']}/complete/",
        HTTP_IDEMPOTENCY_KEY="sales-report-order",
    ).status_code == 200
    sales_return = client.post(
        "/api/v1/sales-returns/",
        sales_return_payload(order.data["data"], customer, product, "1.0000"),
        format="json",
    )
    assert sales_return.status_code == 201, sales_return.content
    assert client.post(
        f"/api/v1/sales-returns/{sales_return.data['data']['id']}/complete/",
        HTTP_IDEMPOTENCY_KEY="sales-report-return",
    ).status_code == 200

    report = client.get("/api/v1/reports/sales/?date_from=2026-09-07&date_to=2026-09-07")
    assert report.status_code == 200
    assert report.data["data"] == {
        "sales_order_count": 1,
        "sales_quantity": "2.0000",
        "sales_amount": "25.00",
        "sales_return_quantity": "1.0000",
        "sales_return_amount": "12.50",
        "net_sales_quantity": "1.0000",
        "net_sales_amount": "12.50",
        "sales_cost": "0.000000",
        "sales_return_cost": "0.000000",
        "net_sales_cost": "0.000000",
        "gross_profit": "12.500000",
    }


def test_sales_profit_uses_cost_snapshot_from_completion() -> None:
    client = APIClient()
    register_and_login(client, "boss-profit")
    customer, product = create_customer_and_product("boss-profit")
    product.purchase_price = Decimal("5.10")
    product.save(update_fields=["purchase_price"])

    order = client.post(
        "/api/v1/sales-orders/",
        sales_payload(customer, product, "1.3333"),
        format="json",
    )
    completed = client.post(
        f"/api/v1/sales-orders/{order.data['data']['id']}/complete/",
        HTTP_IDEMPOTENCY_KEY="sales-profit-order",
    )
    assert completed.status_code == 200
    assert completed.data["data"]["items"][0]["unit_cost_snapshot"] == "5.10"
    assert completed.data["data"]["items"][0]["cost_amount"] == "6.799830"

    product.purchase_price = Decimal("9.00")
    product.save(update_fields=["purchase_price"])
    report = client.get("/api/v1/reports/sales/?date_from=2026-09-07&date_to=2026-09-07")

    assert report.status_code == 200
    assert report.data["data"]["sales_cost"] == "6.799830"
    assert report.data["data"]["gross_profit"] == "9.870170"