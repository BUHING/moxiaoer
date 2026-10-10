from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.inventory.models import StockBalance, StockMovement
from apps.partners.models import Supplier
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


def create_supplier_and_product(username: str) -> tuple[Supplier, Product]:
    unit = Unit.objects.get(organization__owner_user__username=username, name="个")
    product = Product.objects.create(
        organization=unit.organization,
        name=f"{username} 商品",
        unit=unit,
        created_by_user=unit.organization.owner_user,
        updated_by_user=unit.organization.owner_user,
    )
    StockBalance.objects.create(organization=unit.organization, product=product, quantity=Decimal("0.0000"))
    return Supplier.objects.create(organization=unit.organization, name=f"{username} 供应商"), product


def purchase_payload(supplier: Supplier, product: Product, quantity: str = "2.0000") -> dict:
    return {
        "supplier_id": str(supplier.id),
        "occurred_on": "2026-09-07",
        "remark": "进货备注 B-01",
        "items": [{"product_id": str(product.id), "quantity": quantity, "unit_price": "12.50"}],
    }

def purchase_return_payload(purchase_data: dict, supplier: Supplier, product: Product, quantity: str) -> dict:
    return {
        **purchase_payload(supplier, product, quantity),
        "purchase_id": purchase_data["id"],
        "items": [
            {
                "product_id": str(product.id),
                "purchase_item_id": purchase_data["items"][0]["id"],
                "quantity": quantity,
                "unit_price": "0.00",
            }
        ],
    }


def test_purchase_completion_updates_stock_once_and_completed_draft_is_read_only() -> None:
    client = APIClient()
    register_and_login(client, "purchase-boss-a")
    supplier, product = create_supplier_and_product("purchase-boss-a")

    created = client.post("/api/v1/purchases/", purchase_payload(supplier, product), format="json")
    assert created.status_code == 201, created.content
    purchase_id = created.data["data"]["id"]
    assert created.data["data"]["total_amount"] == "25.00"
    assert created.data["data"]["remark"] == "进货备注 B-01"

    assert client.get("/api/v1/purchases/?supplier_id=invalid").status_code == 400
    assert client.post(
        f"/api/v1/purchases/{purchase_id}/complete/",
        HTTP_IDEMPOTENCY_KEY="x" * 256,
    ).status_code == 400

    completed = client.post(
        f"/api/v1/purchases/{purchase_id}/complete/",
        HTTP_IDEMPOTENCY_KEY="purchase-1",
    )
    assert completed.status_code == 200, completed.content
    assert completed.data["data"]["status"] == "COMPLETED"
    assert StockBalance.objects.get(product=product).quantity == Decimal("2.0000")
    movement = StockMovement.objects.get(product=product)
    assert movement.movement_type == StockMovement.MovementType.PURCHASE
    assert movement.quantity_delta == Decimal("2.0000")

    replayed = client.post(
        f"/api/v1/purchases/{purchase_id}/complete/",
        HTTP_IDEMPOTENCY_KEY="purchase-1",
    )
    assert replayed.status_code == 200
    assert replayed.data == completed.data
    assert StockMovement.objects.filter(product=product).count() == 1

    patched = client.patch(
        f"/api/v1/purchases/{purchase_id}/",
        {"items": [{"product_id": str(product.id), "quantity": "1.0000", "unit_price": "12.50"}]},
        format="json",
    )
    assert patched.status_code == 409
    assert StockBalance.objects.get(product=product).quantity == Decimal("2.0000")


def test_deleting_completed_purchase_documents_reverses_stock_and_removes_movements() -> None:
    client = APIClient()
    register_and_login(client, "boss-delete-purchase")
    supplier, product = create_supplier_and_product("boss-delete-purchase")
    created = client.post("/api/v1/purchases/", purchase_payload(supplier, product), format="json")
    purchase_id = created.data["data"]["id"]
    assert client.post(
        f"/api/v1/purchases/{purchase_id}/complete/",
        HTTP_IDEMPOTENCY_KEY="delete-completed-purchase",
    ).status_code == 200

    deleted = client.delete(f"/api/v1/purchases/{purchase_id}/")
    assert deleted.status_code == 204, deleted.content
    assert client.get(f"/api/v1/purchases/{purchase_id}/").status_code == 404
    assert StockBalance.objects.get(product=product).quantity == Decimal("0.0000")
    assert StockMovement.objects.filter(product=product).count() == 0


def test_purchase_return_decreases_stock_and_requires_idempotency_key() -> None:
    client = APIClient()
    register_and_login(client, "purchase-boss-a")
    supplier, product = create_supplier_and_product("purchase-boss-a")
    purchase = client.post("/api/v1/purchases/", purchase_payload(supplier, product), format="json")
    assert client.post(
        f"/api/v1/purchases/{purchase.data['data']['id']}/complete/",
        HTTP_IDEMPOTENCY_KEY="purchase-return-source",
    ).status_code == 200

    returned = client.post("/api/v1/purchase-returns/", purchase_return_payload(purchase.data["data"], supplier, product, "2.0000"), format="json")
    return_id = returned.data["data"]["id"]
    missing_key = client.post(f"/api/v1/purchase-returns/{return_id}/complete/")
    assert missing_key.status_code == 400
    completed_return = client.post(
        f"/api/v1/purchase-returns/{return_id}/complete/",
        HTTP_IDEMPOTENCY_KEY="purchase-return-1",
    )
    assert completed_return.status_code == 200
    assert StockBalance.objects.get(product=product).quantity == Decimal("0.0000")
    movement = StockMovement.objects.filter(product=product).order_by("occurred_at").last()
    assert movement.movement_type == StockMovement.MovementType.PURCHASE_RETURN
    assert movement.quantity_delta == Decimal("-2.0000")


def test_purchase_and_direct_purchase_return_allow_an_empty_supplier_and_use_product_purchase_price() -> None:
    client = APIClient()
    register_and_login(client, "purchase-direct-return")
    _, product = create_supplier_and_product("purchase-direct-return")
    product.purchase_price = Decimal("7.25")
    product.save(update_fields=["purchase_price"])
    StockBalance.objects.filter(product=product).update(quantity=Decimal("3.0000"))

    purchase = client.post(
        "/api/v1/purchases/",
        {
            "occurred_on": "2026-09-07",
            "items": [{"product_id": str(product.id), "quantity": "2.0000"}],
        },
        format="json",
    )
    assert purchase.status_code == 201, purchase.content
    assert purchase.data["data"]["supplier_id"] is None
    assert purchase.data["data"]["items"][0]["unit_price"] == "7.25"

    direct_return = client.post(
        "/api/v1/purchase-returns/",
        {
            "occurred_on": "2026-09-07",
            "items": [{"product_id": str(product.id), "quantity": "2.0000"}],
        },
        format="json",
    )
    assert direct_return.status_code == 201, direct_return.content
    assert direct_return.data["data"]["purchase_id"] is None
    assert direct_return.data["data"]["supplier_id"] is None
    assert direct_return.data["data"]["items"][0]["unit_price"] == "7.25"

    completed_return = client.post(
        f"/api/v1/purchase-returns/{direct_return.data['data']['id']}/complete/",
        HTTP_IDEMPOTENCY_KEY="purchase-direct-return-1",
    )
    assert completed_return.status_code == 200, completed_return.content
    assert StockBalance.objects.get(product=product).quantity == Decimal("1.0000")
    assert StockMovement.objects.order_by("occurred_at").last().quantity_delta == Decimal("-2.0000")


def test_purchase_permissions_and_organization_isolation() -> None:
    boss_a = APIClient()
    register_and_login(boss_a, "purchase-boss-a")
    supplier, product = create_supplier_and_product("purchase-boss-a")
    created = boss_a.post("/api/v1/purchases/", purchase_payload(supplier, product), format="json")
    purchase_id = created.data["data"]["id"]

    employee_response = boss_a.post(
        "/api/v1/employees/",
        {"username": "purchase-employee-a", "display_name": "采购员工", "password": PASSWORD},
        format="json",
    )
    assert employee_response.status_code == 201
    employee = APIClient()
    login_response = employee.post(
        "/api/v1/auth/token/", {"username": "purchase-employee-a", "password": PASSWORD}, format="json"
    )
    employee.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['data']['access']}")
    assert employee.post("/api/v1/purchases/", purchase_payload(supplier, product), format="json").status_code == 201
    assert employee.post("/api/v1/purchase-returns/", purchase_payload(supplier, product), format="json").status_code == 403

    boss_b = APIClient()
    register_and_login(boss_b, "purchase-boss-b")
    assert boss_b.get(f"/api/v1/purchases/{purchase_id}/").status_code == 404


def test_purchase_report_uses_completed_purchases_and_returns() -> None:
    client = APIClient()
    register_and_login(client, "purchase-report-boss")
    supplier, product = create_supplier_and_product("purchase-report-boss")

    purchase = client.post(
        "/api/v1/purchases/", purchase_payload(supplier, product, "3.0000"), format="json"
    )
    assert client.post(
        f"/api/v1/purchases/{purchase.data['data']['id']}/complete/",
        HTTP_IDEMPOTENCY_KEY="purchase-report-purchase",
    ).status_code == 200
    returned = client.post(
        "/api/v1/purchase-returns/",
        purchase_return_payload(purchase.data["data"], supplier, product, "1.0000"),
        format="json",
    )
    assert returned.status_code == 201, returned.content
    assert client.post(
        f"/api/v1/purchase-returns/{returned.data['data']['id']}/complete/",
        HTTP_IDEMPOTENCY_KEY="purchase-report-return",
    ).status_code == 200

    report = client.get("/api/v1/reports/purchases/?date_from=2026-09-07&date_to=2026-09-07")
    assert report.status_code == 200
    assert report.data["data"] == {
        "purchase_count": 1,
        "purchase_quantity": "3.0000",
        "purchase_amount": "37.50",
        "purchase_return_quantity": "1.0000",
        "purchase_return_amount": "12.50",
        "net_purchase_quantity": "2.0000",
        "net_purchase_amount": "25.00",
    }