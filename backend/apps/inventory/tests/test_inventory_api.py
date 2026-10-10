from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.inventory.models import StockBalance, StockMovement
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


def create_product_with_stock(username: str, name: str, quantity: str) -> Product:
    unit = Unit.objects.get(organization__owner_user__username=username, name="个")
    product = Product.objects.create(
        organization=unit.organization,
        name=name,
        unit=unit,
        created_by_user=unit.organization.owner_user,
        updated_by_user=unit.organization.owner_user,
    )
    StockBalance.objects.create(
        organization=unit.organization,
        product=product,
        quantity=Decimal(quantity),
    )
    if Decimal(quantity) != 0:
        StockMovement.objects.create(
            organization=unit.organization,
            product=product,
            movement_type=StockMovement.MovementType.INITIAL,
            quantity_delta=Decimal(quantity),
            source_type="PRODUCT",
            source_id=product.id,
            operator_user=unit.organization.owner_user,
        )
    return product


def test_inventory_lists_are_read_only_paginated_and_organization_scoped() -> None:
    boss_a = APIClient()
    register_and_login(boss_a, "inventory-boss-a")
    product_a = create_product_with_stock("inventory-boss-a", "咖啡豆", "12.5000")
    create_product_with_stock("inventory-boss-a", "滤纸", "0.0000")

    boss_b = APIClient()
    register_and_login(boss_b, "inventory-boss-b")
    create_product_with_stock("inventory-boss-b", "其他组织商品", "99.0000")

    balances = boss_a.get("/api/v1/inventory/balances/?search=咖啡&page_size=1")
    assert balances.status_code == 200
    assert balances.data["meta"] == {"page": 1, "page_size": 1, "total": 1}
    assert balances.data["data"][0]["product_id"] == str(product_a.id)
    assert balances.data["data"][0]["quantity"] == "12.5000"

    movements = boss_a.get(
        f"/api/v1/inventory/movements/?product_id={product_a.id}&movement_type=INITIAL"
        f"&date_from={timezone.localdate().isoformat()}&date_to={timezone.localdate().isoformat()}"
    )
    assert movements.status_code == 200
    assert movements.data["meta"]["total"] == 1
    assert movements.data["data"][0]["quantity_delta"] == "12.5000"
    assert movements.data["data"][0]["operator_name"] == "inventory-boss-a"

    assert boss_a.post("/api/v1/inventory/balances/", {}, format="json").status_code == 405
    assert boss_a.post("/api/v1/inventory/movements/", {}, format="json").status_code == 405

    report = boss_a.get("/api/v1/reports/inventory/")
    assert report.status_code == 200
    assert report.data["data"] == {
        "product_count": 2,
        "in_stock_product_count": 1,
        "out_of_stock_product_count": 1,
        "total_quantity": "12.5000",
    }


def test_inventory_requires_authentication_and_supports_employee_view_permission() -> None:
    anonymous = APIClient()
    assert anonymous.get("/api/v1/inventory/balances/").status_code == 401

    boss = APIClient()
    register_and_login(boss, "inventory-permission-boss")
    create_product_with_stock("inventory-permission-boss", "员工可见商品", "3.0000")
    employee_response = boss.post(
        "/api/v1/employees/",
        {
            "username": "inventory-employee",
            "display_name": "库存员工",
            "password": PASSWORD,
        },
        format="json",
    )
    assert employee_response.status_code == 201

    employee = APIClient()
    login_response = employee.post(
        "/api/v1/auth/token/",
        {"username": "inventory-employee", "password": PASSWORD},
        format="json",
    )
    employee.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['data']['access']}")
    response = employee.get("/api/v1/inventory/balances/")
    assert response.status_code == 200
    assert response.data["meta"]["total"] == 1


def test_inventory_rejects_invalid_filters() -> None:
    client = APIClient()
    register_and_login(client, "inventory-filter-boss")

    assert client.get("/api/v1/inventory/movements/?movement_type=UNKNOWN").status_code == 400
    assert client.get("/api/v1/inventory/movements/?date_from=not-a-date").status_code == 400
    assert client.get("/api/v1/inventory/movements/?product_id=not-a-uuid").status_code == 400
    assert client.get("/api/v1/inventory/balances/?page=invalid").status_code == 400