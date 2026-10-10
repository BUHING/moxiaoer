from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Membership
from apps.inventory.models import StockBalance
from apps.products.models import Product, Unit


PASSWORD = "NotACommonPassword123!"

pytestmark = pytest.mark.django_db


def login(client: APIClient, username: str) -> None:
    response = client.post("/api/v1/auth/token/", {"username": username, "password": PASSWORD}, format="json")
    assert response.status_code == 200, response.content
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['data']['access']}")


def test_dashboard_requires_authentication() -> None:
    response = APIClient().get("/api/v1/dashboard/")

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


def test_dashboard_returns_empty_metrics_for_boss_and_default_employee() -> None:
    boss_client = APIClient()
    register_response = boss_client.post(
        "/api/v1/auth/register/",
        {"username": "boss-a", "password": PASSWORD},
        format="json",
    )
    assert register_response.status_code == 201, register_response.content
    login(boss_client, "boss-a")

    employee_response = boss_client.post(
        "/api/v1/employees/",
        {"username": "employee-a", "display_name": "Employee A", "password": PASSWORD},
        format="json",
    )
    assert employee_response.status_code == 201, employee_response.content

    boss_response = boss_client.get("/api/v1/dashboard/")
    assert boss_response.status_code == 200, boss_response.content
    assert boss_response.json()["data"] == {
        "today": {"sales_order_count": 0, "sales_amount": "0.00", "gross_profit": "0.000000"},
        "week": {"sales_order_count": 0, "sales_amount": "0.00", "gross_profit": "0.000000"},
        "month": {"sales_order_count": 0, "sales_amount": "0.00", "gross_profit": "0.000000"},
        "last_month": {"sales_order_count": 0, "sales_amount": "0.00", "gross_profit": "0.000000"},
    }

    employee_client = APIClient()
    login(employee_client, "employee-a")
    assert employee_client.get("/api/v1/dashboard/").status_code == 200


def test_reports_require_authentication() -> None:
    client = APIClient()

    assert client.get("/api/v1/reports/purchases/?date_from=2026-01-01&date_to=2026-01-31").status_code == 401
    assert client.get("/api/v1/reports/inventory/").status_code == 401


def test_purchase_and_inventory_reports_return_empty_metrics() -> None:
    client = APIClient()
    register_response = client.post(
        "/api/v1/auth/register/",
        {"username": "reports-boss", "password": PASSWORD},
        format="json",
    )
    assert register_response.status_code == 201, register_response.content
    login(client, "reports-boss")

    purchase_response = client.get(
        "/api/v1/reports/purchases/?date_from=2026-01-01&date_to=2026-01-31"
    )
    assert purchase_response.status_code == 200, purchase_response.content
    assert purchase_response.json()["data"] == {
        "purchase_count": 0,
        "purchase_quantity": "0.0000",
        "purchase_amount": "0.00",
        "purchase_return_quantity": "0.0000",
        "purchase_return_amount": "0.00",
        "net_purchase_quantity": "0.0000",
        "net_purchase_amount": "0.00",
    }

    inventory_response = client.get("/api/v1/reports/inventory/")
    assert inventory_response.status_code == 200, inventory_response.content
    assert inventory_response.json()["data"] == {
        "product_count": 0,
        "in_stock_product_count": 0,
        "out_of_stock_product_count": 0,
        "total_quantity": "0.0000",
        "total_amount": "0.000000",
    }


def test_inventory_report_sums_current_stock_at_product_purchase_prices() -> None:
    client = APIClient()
    assert client.post(
        "/api/v1/auth/register/",
        {"username": "stock-value-boss", "password": PASSWORD},
        format="json",
    ).status_code == 201
    login(client, "stock-value-boss")

    unit = Unit.objects.get(organization__owner_user__username="stock-value-boss", name="个")
    for name, quantity, price in [
        ("咖啡豆", "12.5000", "40.25"),
        ("滤纸", "2.0000", "3.10"),
        ("空库存", "0.0000", "99.00"),
    ]:
        product = Product.objects.create(
            organization=unit.organization,
            name=name,
            unit=unit,
            purchase_price=Decimal(price),
            created_by_user=unit.organization.owner_user,
            updated_by_user=unit.organization.owner_user,
        )
        StockBalance.objects.create(
            organization=unit.organization, product=product, quantity=Decimal(quantity)
        )

    response = client.get("/api/v1/reports/inventory/")
    assert response.status_code == 200, response.content
    assert response.json()["data"] == {
        "product_count": 3,
        "in_stock_product_count": 2,
        "out_of_stock_product_count": 1,
        "total_quantity": "14.5000",
        "total_amount": "509.325000",
    }


def test_reports_reject_invalid_dates_and_inactive_membership() -> None:
    client = APIClient()
    register_response = client.post(
        "/api/v1/auth/register/",
        {"username": "restricted-reports-boss", "password": PASSWORD},
        format="json",
    )
    assert register_response.status_code == 201, register_response.content
    login(client, "restricted-reports-boss")

    invalid_range = client.get(
        "/api/v1/reports/sales/?date_from=2026-02-01&date_to=2026-01-01"
    )
    assert invalid_range.status_code == 400
    assert "date" in invalid_range.json()["errors"]

    Membership.objects.filter(user__username="restricted-reports-boss").update(is_active=False)
    forbidden = client.get(
        "/api/v1/reports/purchases/?date_from=2026-01-01&date_to=2026-01-31"
    )
    assert forbidden.status_code == 403