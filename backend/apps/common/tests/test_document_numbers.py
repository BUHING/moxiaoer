from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal
from threading import Barrier
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, close_old_connections, connection
from rest_framework.test import APIClient

from apps.accounts.models import Membership, Organization
from apps.common.document_numbers import save_document_with_number
from apps.inventory.models import StockBalance, StockMovement
from apps.products.models import Product, Unit
from apps.purchases.models import Purchase, PurchaseReturn
from apps.sales.models import SalesOrder, SalesReturn
from apps.sales.services import create_sales_order


FIXED_TIME = datetime(2026, 10, 28, 16, 5, 6, tzinfo=datetime_timezone.utc)
STAMP = "20261029000506"
DOCUMENT_TYPES = [
    ("/api/v1/sales-orders/", "SO", SalesOrder, None, None),
    ("/api/v1/sales-returns/", "SR", SalesReturn, "/api/v1/sales-orders/", "sales_order"),
    ("/api/v1/purchases/", "PO", Purchase, None, None),
    ("/api/v1/purchase-returns/", "PR", PurchaseReturn, "/api/v1/purchases/", "purchase"),
]

pytestmark = pytest.mark.django_db


@pytest.fixture
def context():
    user = get_user_model().objects.create_user(username="document-numbers")
    organization = Organization.objects.create(owner_user=user, name="Number tests")
    Membership.objects.create(user=user, organization=organization, role=Membership.Role.BOSS)
    unit = Unit.objects.create(organization=organization, name="Unit")
    product = Product.objects.create(
        organization=organization,
        name="Numbered product",
        unit=unit,
        created_by_user=user,
        updated_by_user=user,
    )
    StockBalance.objects.create(organization=organization, product=product, quantity=Decimal("100"))
    client = APIClient()
    client.force_authenticate(user)
    return user, organization, product, client


def document_payload(context, source_path, source_field):
    _, _, product, client = context
    payload = {
        "occurred_on": "2020-01-01",
        "items": [{"product_id": str(product.id), "quantity": "1", "unit_price": "12.50"}],
    }
    if source_path:
        source = client.post(source_path, payload, format="json")
        assert source.status_code == 201, source.data
        data = source.data["data"]
        completed = client.post(
            f"{source_path}{data['id']}/complete/",
            HTTP_IDEMPOTENCY_KEY="number-test-source",
        )
        assert completed.status_code == 200, completed.data
        payload[f"{source_field}_id"] = data["id"]
        payload["items"][0][f"{source_field}_item_id"] = data["items"][0]["id"]
    return payload


@pytest.mark.parametrize("path,prefix,model,source_path,source_field", DOCUMENT_TYPES)
def test_time_numbers_cover_all_creation_paths_and_survive_edit_and_completion(
    context, monkeypatch, path, prefix, model, source_path, source_field
):
    _, _, _, client = context
    payload = document_payload(context, source_path, source_field)
    monkeypatch.setattr("apps.common.document_numbers.timezone.now", lambda: FIXED_TIME)
    first = client.post(path, payload, format="json")
    second = client.post(path, payload, format="json")
    assert first.status_code == second.status_code == 201
    assert first.data["data"]["document_no"] == f"{prefix}{STAMP}"
    assert second.data["data"]["document_no"] == f"{prefix}{STAMP}-02"
    first_id = first.data["data"]["id"]
    assert first.data["data"]["occurred_on"] == "2020-01-01"
    assert model.objects.get(pk=first_id).created_at == FIXED_TIME
    edited = client.patch(f"{path}{first_id}/", {"remark": "Changed"}, format="json")
    assert edited.status_code == 200, edited.data
    assert edited.data["data"]["document_no"] == f"{prefix}{STAMP}"
    completed = client.post(
        f"{path}{first_id}/complete/", HTTP_IDEMPOTENCY_KEY=f"number-test-{prefix}"
    )
    assert completed.status_code == 200, completed.data
    assert completed.data["data"]["document_no"] == f"{prefix}{STAMP}"
    assert model.objects.count() == 2


@pytest.mark.parametrize("path,prefix,model,source_path,source_field", DOCUMENT_TYPES)
def test_legacy_numbers_and_existing_data_are_unchanged(
    context, path, prefix, model, source_path, source_field
):
    _, organization, product, client = context
    payload = document_payload(context, source_path, source_field)
    created = client.post(path, payload, format="json")
    assert created.status_code == 201, created.data
    document_id = created.data["data"]["id"]
    legacy_number = f"{prefix}-7BC31BE775C4"
    model.objects.filter(pk=document_id).update(document_no=legacy_number)
    original_items = list(model.objects.get(pk=document_id).items.values())
    old_balance = StockBalance.objects.get(product=product).quantity
    old_movement_count = StockMovement.objects.count()

    edited = client.patch(f"{path}{document_id}/", {"remark": "Legacy edit"}, format="json")
    assert edited.status_code == 200, edited.data
    assert edited.data["data"]["document_no"] == legacy_number
    assert edited.data["data"]["id"] == document_id
    fresh = client.post(path, payload, format="json")
    assert fresh.status_code == 201, fresh.data
    assert model.objects.get(pk=document_id).document_no == legacy_number
    assert list(
        model.objects.get(pk=document_id).items.values(
            *[key for key in original_items[0] if key != "id"]
        )
    ) == [{key: value for key, value in item.items() if key != "id"} for item in original_items]
    assert StockBalance.objects.get(product=product).quantity == old_balance
    assert StockMovement.objects.count() == old_movement_count
    assert Product.objects.filter(pk=product.pk, organization=organization).exists()
    completed = client.post(
        f"{path}{document_id}/complete/", HTTP_IDEMPOTENCY_KEY=f"legacy-{prefix}"
    )
    assert completed.status_code == 200, completed.data
    assert completed.data["data"]["document_no"] == legacy_number
    if source_field:
        assert (
            str(getattr(model.objects.get(pk=document_id), f"{source_field}_id"))
            == payload[f"{source_field}_id"]
        )


def new_order(context, **values):
    user, organization, _, _ = context
    return SalesOrder(
        organization=organization,
        created_by_user=user,
        updated_by_user=user,
        occurred_on="2020-01-01",
        **values,
    )


def test_same_number_can_be_used_by_different_organizations(context, monkeypatch):
    monkeypatch.setattr("apps.common.document_numbers.timezone.now", lambda: FIXED_TIME)
    first = new_order(context)
    save_document_with_number(document=first, prefix="SO")
    other_user = get_user_model().objects.create_user(username="other-number-owner")
    other_org = Organization.objects.create(owner_user=other_user, name="Other")
    second = SalesOrder(
        organization=other_org,
        created_by_user=other_user,
        updated_by_user=other_user,
        occurred_on="2020-01-01",
    )
    save_document_with_number(document=second, prefix="SO")
    assert first.document_no == second.document_no == f"SO{STAMP}"


def test_number_changes_only_on_creation_and_other_constraint_errors_are_not_retried(context):
    order = new_order(context)
    save_document_with_number(document=order, prefix="SO")
    number = order.document_no
    with pytest.raises(ValueError, match="Only new documents"):
        save_document_with_number(document=order, prefix="SO")
    order.refresh_from_db()
    assert order.document_no == number
    with pytest.raises(IntegrityError):
        save_document_with_number(
            document=new_order(context, total_amount=Decimal("-1")), prefix="SO"
        )
    with pytest.raises(IntegrityError):
        save_document_with_number(
            document=new_order(context, id=order.id, remark="Must not overwrite"),
            prefix="SO",
        )
    order.refresh_from_db()
    assert order.document_no == number
    assert order.remark == ""
    assert SalesOrder.objects.count() == 1


def test_suffix_continues_beyond_two_digits_without_changing_existing_documents(
    context, monkeypatch
):
    monkeypatch.setattr("apps.common.document_numbers.timezone.now", lambda: FIXED_TIME)
    orders = [
        new_order(
            context, document_no=f"SO{STAMP}" if sequence == 1 else f"SO{STAMP}-{sequence:02d}"
        )
        for sequence in range(1, 100)
    ]
    SalesOrder.objects.bulk_create(orders)
    original_numbers = dict(SalesOrder.objects.values_list("id", "document_no"))
    order = new_order(context)
    save_document_with_number(document=order, prefix="SO")
    assert order.document_no == f"SO{STAMP}-100"
    assert (
        dict(SalesOrder.objects.filter(id__in=original_numbers).values_list("id", "document_no"))
        == original_numbers
    )
    assert SalesOrder.objects.count() == 100
    assert not StockMovement.objects.exists()


def test_failed_item_creation_rolls_back_number_and_document(context, monkeypatch):
    user, organization, product, _ = context
    monkeypatch.setattr("apps.common.document_numbers.timezone.now", lambda: FIXED_TIME)
    with patch("apps.sales.services._replace_items", side_effect=RuntimeError("item failure")):
        with pytest.raises(RuntimeError, match="item failure"):
            create_sales_order(
                organization=organization,
                user=user,
                values={
                    "occurred_on": "2020-01-01",
                    "items": [
                        {
                            "product_id": product.id,
                            "quantity": Decimal("1"),
                            "unit_price": Decimal("1"),
                        }
                    ],
                },
            )
    assert not SalesOrder.objects.exists()
    order = new_order(context)
    save_document_with_number(document=order, prefix="SO")
    assert order.document_no == f"SO{STAMP}"


@pytest.mark.skipif(connection.vendor != "postgresql", reason="Requires PostgreSQL concurrency")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("path,prefix,model,source_path,source_field", DOCUMENT_TYPES)
def test_concurrent_same_second_creation_is_unique(
    context, monkeypatch, path, prefix, model, source_path, source_field
):
    user, _, _, _ = context
    payload = document_payload(context, source_path, source_field)
    monkeypatch.setattr("apps.common.document_numbers.timezone.now", lambda: FIXED_TIME)
    barrier = Barrier(4)

    def create_document(_):
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(user)
            barrier.wait(timeout=10)
            response = client.post(path, payload, format="json")
            assert response.status_code == 201, response.data
            return response.data["data"]["document_no"]
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=4) as executor:
        numbers = list(executor.map(create_document, range(4)))
    assert sorted(numbers) == [
        f"{prefix}{STAMP}",
        *[f"{prefix}{STAMP}-{sequence:02d}" for sequence in range(2, 5)],
    ]
    assert model.objects.count() == 4
