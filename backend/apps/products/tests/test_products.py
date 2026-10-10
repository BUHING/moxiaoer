from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.inventory.models import StockBalance, StockMovement
from apps.partners.models import Supplier
from apps.products.models import Product, ProductAttribute, Unit


@pytest.fixture
def client():
    return APIClient()


def register_and_authenticate(client: APIClient, username: str) -> dict:
    response = client.post("/api/v1/auth/register/", {"username": username, "password": "Secure-pass-123"})
    assert response.status_code == 201
    response = client.post("/api/v1/auth/token/", {"username": username, "password": "Secure-pass-123"})
    assert response.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['access']}")
    return response.data["data"]


@pytest.mark.django_db
def test_product_creation_initializes_catalog_and_writes_initial_stock_once(client):
    register_and_authenticate(client, "boss-a")

    units_response = client.get("/api/v1/units/")
    specifications_response = client.get("/api/v1/specifications/")
    price_levels_response = client.get("/api/v1/price-levels/")

    assert units_response.status_code == 200
    assert {item["name"] for item in units_response.data["data"]} >= {"个", "张", "包", "瓶"}
    assert {item["name"] for item in specifications_response.data["data"]} == {"尺码", "颜色"}
    assert [item["name"] for item in price_levels_response.data["data"]] == ["零售价", "批发价"]

    unit_id = units_response.data["data"][0]["id"]
    supplier = Supplier.objects.create(
        organization=Unit.objects.get(id=unit_id).organization,
        name="咖啡供应商",
    )
    size_id = next(item["id"] for item in specifications_response.data["data"] if item["name"] == "尺码")
    retail_id = price_levels_response.data["data"][0]["id"]
    response = client.post(
        "/api/v1/products/",
        {
            "name": "咖啡豆",
            "unit_id": unit_id,
            "supplier_id": str(supplier.id),
            "initial_quantity": "12.5000",
            "purchase_price": "40.25",
            "specification": "500g",
            "remark": "深烘焙 A-01",
            "specification_values": [{"specification_id": size_id, "value": "500g"}],
            "prices": [{"price_level_id": retail_id, "amount": "68.00"}],
        },
        format="json",
    )

    assert response.status_code == 201
    product_id = response.data["data"]["id"]
    assert response.data["data"]["stock_quantity"] == "12.5000"
    assert response.data["data"]["purchase_price"] == "40.25"
    assert response.data["data"]["supplier_id"] == str(supplier.id)
    assert response.data["data"]["supplier_name"] == "咖啡供应商"
    assert response.data["data"]["specification"] == "500g"
    assert response.data["data"]["remark"] == "深烘焙 A-01"
    assert StockBalance.objects.get(product_id=product_id).quantity == Decimal("12.5000")
    movements = StockMovement.objects.filter(product_id=product_id)
    assert movements.count() == 1
    assert movements.get().movement_type == StockMovement.MovementType.INITIAL
    assert movements.get().quantity_delta == Decimal("12.5000")

    assert client.get(f"/api/v1/products/{product_id}/prices/").status_code == 200
    assert client.patch(f"/api/v1/products/{product_id}/prices/", {}, format="json").status_code == 405
    assert client.delete(f"/api/v1/products/{product_id}/prices/").status_code == 405
    assert client.get(f"/api/v1/products/{product_id}/").status_code == 200

    update_response = client.patch(
        f"/api/v1/products/{product_id}/",
        {"initial_quantity": "30.0000"},
        format="json",
    )
    assert update_response.status_code == 400
    assert StockBalance.objects.get(product_id=product_id).quantity == Decimal("12.5000")
    assert StockMovement.objects.filter(product_id=product_id).count() == 1

    price_update_response = client.patch(
        f"/api/v1/products/{product_id}/",
        {"purchase_price": "41.50"},
        format="json",
    )
    assert price_update_response.status_code == 200
    assert price_update_response.data["data"]["purchase_price"] == "41.50"

    assert client.get("/api/v1/products/?unit_id=invalid").status_code == 400
    assert client.get("/api/v1/products/?page=invalid").status_code == 400


@pytest.mark.django_db
def test_product_supplier_must_be_active_and_in_current_organization(client):
    register_and_authenticate(client, "product-supplier-boss-a")
    organization_a_unit = Unit.objects.get(organization__owner_user__username="product-supplier-boss-a", name="个")
    inactive_supplier = Supplier.objects.create(
        organization=organization_a_unit.organization,
        name="停用供应商",
        is_active=False,
    )

    inactive_response = client.post(
        "/api/v1/products/",
        {
            "name": "不能选择停用供应商的商品",
            "unit_id": str(organization_a_unit.id),
            "supplier_id": str(inactive_supplier.id),
        },
        format="json",
    )
    assert inactive_response.status_code == 400
    assert "supplier_id" in inactive_response.data["errors"]

    other_client = APIClient()
    register_and_authenticate(other_client, "product-supplier-boss-b")
    other_supplier = Supplier.objects.create(
        organization=Unit.objects.get(organization__owner_user__username="product-supplier-boss-b", name="个").organization,
        name="其他组织供应商",
    )
    cross_organization_response = client.post(
        "/api/v1/products/",
        {
            "name": "不能选择其他组织供应商的商品",
            "unit_id": str(organization_a_unit.id),
            "supplier_id": str(other_supplier.id),
        },
        format="json",
    )
    assert cross_organization_response.status_code == 400
    assert "supplier_id" in cross_organization_response.data["errors"]


@pytest.mark.django_db
def test_product_without_stock_movement_can_be_deleted(client):
    register_and_authenticate(client, "product-delete-boss")
    unit = Unit.objects.get(organization__owner_user__username="product-delete-boss", name="个")
    created = client.post(
        "/api/v1/products/",
        {"name": "可直接删除的商品", "unit_id": str(unit.id)},
        format="json",
    )
    assert created.status_code == 201, created.content
    product_id = created.data["data"]["id"]
    assert not StockMovement.objects.filter(product_id=product_id).exists()

    deleted = client.delete(f"/api/v1/products/{product_id}/")
    assert deleted.status_code == 204, deleted.content
    assert not Product.objects.filter(id=product_id).exists()


@pytest.mark.django_db
def test_product_attribute_can_be_deleted_and_recreated(client):
    register_and_authenticate(client, "attribute-delete-boss")
    created = client.post(
        "/api/v1/product-attributes/",
        {"name": "品牌", "input_type": "TEXT"},
        format="json",
    )
    assert created.status_code == 201, created.content
    attribute_id = created.data["data"]["id"]

    duplicate = client.post(
        "/api/v1/product-attributes/",
        {"name": "品牌", "input_type": "TEXT"},
        format="json",
    )
    assert duplicate.status_code == 409
    assert duplicate.data["code"] == "resource_already_exists"
    assert duplicate.data["message"] == "名称已存在。"

    deleted = client.delete(f"/api/v1/product-attributes/{attribute_id}/")
    assert deleted.status_code == 204, deleted.content
    assert not ProductAttribute.objects.filter(id=attribute_id).exists()

    recreated = client.post(
        "/api/v1/product-attributes/",
        {"name": "品牌", "input_type": "TEXT"},
        format="json",
    )
    assert recreated.status_code == 201, recreated.content


@pytest.mark.django_db
def test_products_enforce_permissions_and_organization_isolation(client):
    register_and_authenticate(client, "boss-a")
    unit = Unit.objects.get(organization__owner_user__username="boss-a", name="个")
    created = client.post(
        "/api/v1/products/",
        {"name": "组织 A 商品", "unit_id": str(unit.id)},
        format="json",
    )
    assert created.status_code == 201
    product_id = created.data["data"]["id"]

    employee_response = client.post(
        "/api/v1/employees/",
        {"username": "employee-a", "display_name": "员工 A", "password": "Secure-pass-123"},
        format="json",
    )
    assert employee_response.status_code == 201

    employee = APIClient()
    login_response = employee.post(
        "/api/v1/auth/token/",
        {"username": "employee-a", "password": "Secure-pass-123"},
        format="json",
    )
    employee.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['data']['access']}")
    assert employee.get("/api/v1/products/").status_code == 200
    assert employee.post(
        "/api/v1/products/",
        {"name": "无权商品", "unit_id": str(unit.id)},
        format="json",
    ).status_code == 403

    other_client = APIClient()
    register_and_authenticate(other_client, "boss-b")
    assert other_client.get(f"/api/v1/products/{product_id}/").status_code == 404


@pytest.mark.django_db
def test_price_level_limit_applies_to_creation_and_reactivation(client):
    register_and_authenticate(client, "boss-a")
    price_levels = client.get("/api/v1/price-levels/").data["data"]
    first_price_level_id = price_levels[0]["id"]

    for index in range(4):
        response = client.post(
            "/api/v1/price-levels/",
            {"name": f"等级 {index + 1}", "sort_order": index + 2},
            format="json",
        )
        assert response.status_code == 201

    limit_response = client.post(
        "/api/v1/price-levels/",
        {"name": "超额等级", "sort_order": 10},
        format="json",
    )
    assert limit_response.status_code == 409
    assert limit_response.data["code"] == "price_level_limit"

    assert client.post(f"/api/v1/price-levels/{first_price_level_id}/deactivate/").status_code == 200
    assert client.post(
        "/api/v1/price-levels/",
        {"name": "替代等级", "sort_order": 11},
        format="json",
    ).status_code == 201
    reactivation_response = client.patch(
        f"/api/v1/price-levels/{first_price_level_id}/",
        {"is_active": True},
        format="json",
    )
    assert reactivation_response.status_code == 409
    assert reactivation_response.data["code"] == "price_level_limit"