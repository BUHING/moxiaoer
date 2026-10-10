import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Organization
from apps.partners.models import Supplier
from apps.purchases.models import Purchase


PASSWORD = "NotACommonPassword123!"


def register_and_login(client: APIClient, username: str) -> None:
    assert client.post(
        "/api/v1/auth/register/", {"username": username, "password": PASSWORD}, format="json"
    ).status_code == 201
    response = client.post(
        "/api/v1/auth/token/", {"username": username, "password": PASSWORD}, format="json"
    )
    assert response.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['access']}")


@pytest.mark.django_db
def test_supplier_crud_deactivation_and_organization_isolation() -> None:
    client = APIClient()
    register_and_login(client, "supplier-boss-a")

    created = client.post(
        "/api/v1/suppliers/",
        {
            "name": "供应商 A",
            "contact_name": "李四",
            "contact_address": "上海市浦东新区示例路 1 号",
            "phone": "13900000000",
            "remark": "优先联系",
        },
        format="json",
    )
    assert created.status_code == 201
    supplier_id = created.data["data"]["id"]
    assert created.data["data"]["contact_address"] == "上海市浦东新区示例路 1 号"

    updated = client.patch(
        f"/api/v1/suppliers/{supplier_id}/", {"remark": "更新备注"}, format="json"
    )
    assert updated.status_code == 200
    assert updated.data["data"]["remark"] == "更新备注"

    deactivated = client.post(f"/api/v1/suppliers/{supplier_id}/deactivate/")
    assert deactivated.status_code == 200
    assert deactivated.data["data"] == {"id": supplier_id, "is_active": False}
    assert [item["id"] for item in client.get("/api/v1/suppliers/?is_active=false").data["data"]] == [
        supplier_id
    ]

    other_client = APIClient()
    register_and_login(other_client, "supplier-boss-b")
    assert other_client.get(f"/api/v1/suppliers/{supplier_id}/").status_code == 404

    assert client.delete(f"/api/v1/suppliers/{supplier_id}/").status_code == 204


@pytest.mark.django_db
def test_supplier_management_requires_permission_and_referenced_supplier_cannot_delete() -> None:
    boss_client = APIClient()
    register_and_login(boss_client, "supplier-boss-a")
    organization = Organization.objects.get(owner_user__username="supplier-boss-a")
    supplier = Supplier.objects.create(organization=organization, name="已引用供应商")
    Purchase.objects.create(
        organization=organization,
        document_no="PO-SUPPLIER-001",
        supplier=supplier,
        occurred_on="2026-09-08",
        created_by_user=organization.owner_user,
        updated_by_user=organization.owner_user,
    )

    employee_response = boss_client.post(
        "/api/v1/employees/",
        {"username": "supplier-employee", "display_name": "供应商员工", "password": PASSWORD},
        format="json",
    )
    assert employee_response.status_code == 201
    employee_client = APIClient()
    login_response = employee_client.post(
        "/api/v1/auth/token/", {"username": "supplier-employee", "password": PASSWORD}, format="json"
    )
    employee_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['data']['access']}")

    assert employee_client.get("/api/v1/suppliers/").status_code == 200
    assert employee_client.post("/api/v1/suppliers/", {"name": "无权供应商"}, format="json").status_code == 403
    deleted = boss_client.delete(f"/api/v1/suppliers/{supplier.id}/")
    assert deleted.status_code == 409
    assert deleted.data["code"] == "resource_in_use"