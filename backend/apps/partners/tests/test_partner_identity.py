from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier, local
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, close_old_connections, connection, transaction
from rest_framework.test import APIClient

from apps.accounts.models import Membership, Organization
from apps.inventory.models import StockBalance, StockMovement
from apps.partners import services
from apps.partners.models import Customer, Supplier
from apps.partners.services import save_partner
from apps.products.models import Product, Unit


pytestmark = pytest.mark.django_db


@pytest.fixture(
    params=[(Customer, "customers"), (Supplier, "suppliers")], ids=["customer", "supplier"]
)
def partner_type(request):
    return request.param


@pytest.fixture
def owner():
    user = get_user_model().objects.create_user(username="partner-identity-owner")
    organization = Organization.objects.create(owner_user=user, name="Identity tests")
    Membership.objects.create(user=user, organization=organization, role=Membership.Role.BOSS)
    client = APIClient()
    client.force_authenticate(user)
    return organization, user, client


def payload(model):
    values = {"name": "同名店铺", "contact_name": "联系人", "phone": "13800000000"}
    if model is Supplier:
        values["contact_address"] = "示例路 1 号"
    return values


def test_same_name_with_any_different_identity_field_is_allowed(owner, partner_type):
    organization, _, client = owner
    model, path = partner_type
    values = payload(model)
    assert client.post(f"/api/v1/{path}/", values, format="json").status_code == 201
    for field in values:
        changed = {**values, field: values[field] + "2"}
        response = client.post(f"/api/v1/{path}/", changed, format="json")
        assert response.status_code == 201, response.data
    assert model.objects.filter(organization=organization).count() == len(values) + 1


def test_duplicate_create_is_a_chinese_conflict_and_remark_does_not_change_identity(
    owner, partner_type
):
    organization, _, client = owner
    model, path = partner_type
    values = payload(model)
    existing = model.objects.create(organization=organization, **values)
    snapshot = model.objects.filter(pk=existing.pk).values().get()
    response = client.post(
        f"/api/v1/{path}/", {**values, "remark": "另一个备注", "is_active": False}, format="json"
    )
    assert response.status_code == 409
    assert response.data["code"] == f"duplicate_{model._meta.model_name}"
    assert "都相同" in response.data["message"]
    assert "请检查后再保存" in response.data["message"]
    assert "电话" in response.data["message"]
    assert ("联系地址" in response.data["message"]) == (model is Supplier)
    assert model.objects.count() == 1
    existing.refresh_from_db()
    assert model.objects.filter(pk=existing.pk).values().get() == snapshot


def test_partial_edit_excludes_self_and_duplicate_edit_preserves_all_original_fields(
    owner, partner_type
):
    organization, _, client = owner
    model, path = partner_type
    values = payload(model)
    current = model.objects.create(organization=organization, **values, remark="原备注")
    original_id = current.pk
    unchanged = client.patch(f"/api/v1/{path}/{current.pk}/", values, format="json")
    assert unchanged.status_code == 200
    edited = client.patch(
        f"/api/v1/{path}/{current.pk}/", {"remark": "允许修改备注"}, format="json"
    )
    assert edited.status_code == 200
    other = model.objects.create(organization=organization, **{**values, "phone": "13900000000"})
    before = model.objects.filter(pk=current.pk).values().get()
    blocked = client.patch(
        f"/api/v1/{path}/{current.pk}/",
        {"phone": other.phone, "remark": "不能部分保存此备注"},
        format="json",
    )
    assert blocked.status_code == 409
    current.refresh_from_db()
    assert model.objects.filter(pk=current.pk).values().get() == before
    assert current.pk == original_id
    assert model.objects.count() == 2
    allowed = client.patch(f"/api/v1/{path}/{current.pk}/", {"phone": "13700000000"}, format="json")
    assert allowed.status_code == 200


def test_blank_optional_fields_and_front_or_back_spaces_are_compared(owner, partner_type):
    organization, _, client = owner
    model, path = partner_type
    first = client.post(f"/api/v1/{path}/", {"name": "仅名称"}, format="json")
    assert first.status_code == 201
    empty_values = {field: "" for field in payload(model) if field != "name"}
    duplicate = client.post(f"/api/v1/{path}/", {"name": " 仅名称 ", **empty_values}, format="json")
    assert duplicate.status_code == 409
    assert (
        client.post(
            f"/api/v1/{path}/", {"name": "仅名称", "contact_name": "另一个人"}, format="json"
        ).status_code
        == 201
    )

    values = payload(model)
    padded = {field: f" {value} " for field, value in values.items()}
    legacy = model.objects.create(organization=organization, **padded)
    before = model.objects.filter(pk=legacy.pk).values().get()
    assert client.post(f"/api/v1/{path}/", values, format="json").status_code == 409
    legacy.refresh_from_db()
    assert model.objects.filter(pk=legacy.pk).values().get() == before
    with pytest.raises(IntegrityError), transaction.atomic():
        model.objects.create(organization=organization, **values)


def test_disabled_identity_is_still_reserved_and_reported_clearly(owner, partner_type):
    organization, _, client = owner
    model, path = partner_type
    values = payload(model)
    disabled = model.objects.create(organization=organization, **values, is_active=False)
    response = client.post(f"/api/v1/{path}/", values, format="json")
    assert response.status_code == 409
    assert "已停用" in response.data["message"]
    assert "仅停用" in response.data["message"]
    other = model.objects.create(organization=organization, **{**values, "phone": "13900000000"})
    response = client.patch(
        f"/api/v1/{path}/{other.pk}/", {"phone": values["phone"]}, format="json"
    )
    assert response.status_code == 409
    assert "已停用" in response.data["message"]
    assert (
        client.patch(
            f"/api/v1/{path}/{disabled.pk}/", {"is_active": True}, format="json"
        ).status_code
        == 200
    )


def test_remark_edit_does_not_normalize_or_change_other_historical_values(owner, partner_type):
    organization, _, client = owner
    model, path = partner_type
    padded = {field: f" {value} " for field, value in payload(model).items()}
    existing = model.objects.create(organization=organization, **padded)
    before = model.objects.filter(pk=existing.pk).values().get()
    response = client.patch(
        f"/api/v1/{path}/{existing.pk}/", {"remark": "只修改备注"}, format="json"
    )
    assert response.status_code == 200
    after = model.objects.filter(pk=existing.pk).values().get()
    assert after["remark"] == "只修改备注"
    for field in before:
        if field not in {"remark", "updated_at"}:
            assert after[field] == before[field]


def test_same_name_pagination_is_stable_and_does_not_omit_or_duplicate_records(owner, partner_type):
    organization, _, client = owner
    model, path = partner_type
    records = model.objects.bulk_create(
        [
            model(organization=organization, **{**payload(model), "phone": f"138{index:08d}"})
            for index in range(205)
        ]
    )
    identifiers = []
    for page in range(1, 4):
        response = client.get(
            f"/api/v1/{path}/", {"page": page, "page_size": 100, "search": "同名店铺"}
        )
        assert response.status_code == 200
        assert response.data["meta"]["total"] == 205
        identifiers.extend(item["id"] for item in response.data["data"])
    assert identifiers == sorted(str(record.id) for record in records)
    assert len(set(identifiers)) == 205


def test_same_name_partners_remain_linked_by_id_and_drafts_do_not_change_stock(owner, partner_type):
    organization, user, client = owner
    model, _ = partner_type
    first = model.objects.create(organization=organization, **payload(model))
    second = model.objects.create(
        organization=organization, **{**payload(model), "phone": "13900000000"}
    )
    unit = Unit.objects.create(organization=organization, name="Unit")
    product = Product.objects.create(
        organization=organization,
        name="Linked product",
        unit=unit,
        supplier=second if model is Supplier else None,
        created_by_user=user,
        updated_by_user=user,
    )
    balance = StockBalance.objects.create(
        organization=organization, product=product, quantity=Decimal("10")
    )
    before = StockBalance.objects.filter(pk=balance.pk).values().get()
    document_path = "sales-orders" if model is Customer else "purchases"
    partner_field = "customer_id" if model is Customer else "supplier_id"
    response = client.post(
        f"/api/v1/{document_path}/",
        {
            partner_field: str(second.id),
            "occurred_on": "2026-10-28",
            "items": [{"product_id": str(product.id), "quantity": "1", "unit_price": "1.00"}],
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    assert response.data["data"][partner_field] == str(second.id)
    assert response.data["data"][partner_field] != str(first.id)
    assert StockBalance.objects.filter(pk=balance.pk).values().get() == before
    assert not StockMovement.objects.exists()
    if model is Supplier:
        product.refresh_from_db()
        assert product.supplier_id == second.id
        assert client.get(f"/api/v1/products/{product.pk}/").data["data"]["supplier_id"] == str(
            second.id
        )


def test_other_organizations_and_partner_types_are_independent(owner, partner_type):
    organization, _, client = owner
    model, path = partner_type
    values = payload(model)
    other_user = get_user_model().objects.create_user(username="other-identity-owner")
    other_org = Organization.objects.create(owner_user=other_user, name="Other")
    other = model.objects.create(organization=other_org, **values)
    response = client.post(f"/api/v1/{path}/", values, format="json")
    assert response.status_code == 201
    assert (
        client.patch(
            f"/api/v1/{path}/{other.pk}/", {"name": "不能跨店铺修改"}, format="json"
        ).status_code
        == 404
    )
    other_model = Supplier if model is Customer else Customer
    other_model.objects.create(organization=organization, **payload(other_model))
    assert model.objects.count() == 2
    assert other_model.objects.count() == 1


def test_phone_punctuation_internal_spaces_and_letter_case_are_not_rewritten(owner, partner_type):
    _, _, client = owner
    model, path = partner_type
    for phone in ("13800000000", "138-00000000", "138 00000000", "+86 13800000000"):
        response = client.post(
            f"/api/v1/{path}/", {**payload(model), "phone": phone}, format="json"
        )
        assert response.status_code == 201
        assert response.data["data"]["phone"] == phone
    for name in ("Shop", "shop", "Shop A", "ShopA"):
        assert (
            client.post(
                f"/api/v1/{path}/", {**payload(model), "name": name}, format="json"
            ).status_code
            == 201
        )


def test_unrelated_integrity_errors_are_not_reported_as_duplicate_partners(owner, partner_type):
    organization, _, _ = owner
    model, _ = partner_type
    with patch.object(model, "save", side_effect=IntegrityError("unrelated failure")):
        with pytest.raises(IntegrityError, match="unrelated failure"):
            save_partner(model=model, organization=organization, values=payload(model))
    assert not model.objects.exists()


@pytest.mark.skipif(connection.vendor != "postgresql", reason="Requires PostgreSQL concurrency")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("operation", ["create", "update"])
def test_concurrent_identity_conflict_is_handled_without_overwriting_records(
    owner, partner_type, operation, monkeypatch
):
    organization, user, _ = owner
    model, path = partner_type
    desired = payload(model)
    originals = []
    if operation == "update":
        originals = [
            model.objects.create(organization=organization, **{**desired, "name": f"原记录{index}"})
            for index in range(2)
        ]
    before = {item.pk: model.objects.filter(pk=item.pk).values().get() for item in originals}
    barrier = Barrier(2)
    thread_state = local()
    find_duplicate = services._find_duplicate

    def synchronized_check(**kwargs):
        result = find_duplicate(**kwargs)
        if not getattr(thread_state, "checked", False):
            thread_state.checked = True
            barrier.wait(timeout=10)
        return result

    monkeypatch.setattr(services, "_find_duplicate", synchronized_check)

    def submit(index):
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(user)
            if operation == "create":
                response = client.post(f"/api/v1/{path}/", desired, format="json")
            else:
                response = client.patch(
                    f"/api/v1/{path}/{originals[index].pk}/", desired, format="json"
                )
            return index, response.status_code, response.data
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(submit, range(2)))
    assert sorted(status for _, status, _ in results) == [
        200 if operation == "update" else 201,
        409,
    ]
    assert model.objects.filter(organization=organization, **desired).count() == 1
    for index, status, data in results:
        if status == 409:
            assert data["code"] == f"duplicate_{model._meta.model_name}"
            if operation == "update":
                assert (
                    model.objects.filter(pk=originals[index].pk).values().get()
                    == before[originals[index].pk]
                )
    assert model.objects.count() == (2 if operation == "update" else 1)
