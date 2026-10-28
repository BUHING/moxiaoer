from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor


pytestmark = pytest.mark.django_db(transaction=True)
OLD_TARGET = ("partners", "0005_supplier_contact_address")
NEW_TARGET = ("partners", "0006_partner_identity_unique")


def migration_state():
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    executor.migrate([OLD_TARGET])
    old_targets = [target for target in latest if target[0] != "partners"] + [OLD_TARGET]
    return executor.loader.project_state(old_targets).apps, latest


def create_owner(apps):
    user = apps.get_model("accounts", "User").objects.create(username="migration-owner")
    organization = apps.get_model("accounts", "Organization").objects.create(
        owner_user=user, name="Existing business"
    )
    return user, organization


def snapshot(apps, labels):
    return {label: list(apps.get_model(*label).objects.order_by("pk").values()) for label in labels}


def test_migration_preserves_existing_business_values_ids_and_foreign_keys():
    apps, latest = migration_state()
    try:
        user, organization = create_owner(apps)
        customer = apps.get_model("partners", "Customer").objects.create(
            organization=organization,
            name=" 原客户 ",
            contact_name=" 联系人 ",
            phone=" 13800000000 ",
            remark="历史客户备注",
            is_active=False,
        )
        supplier = apps.get_model("partners", "Supplier").objects.create(
            organization=organization,
            name=" 原供应商 ",
            contact_name=" 联系人 ",
            contact_address=" 旧地址 ",
            phone=" 13900000000 ",
            remark="历史供应商备注",
        )
        unit = apps.get_model("products", "Unit").objects.create(
            organization=organization, name="Unit"
        )
        product = apps.get_model("products", "Product").objects.create(
            organization=organization,
            name="Existing product",
            unit=unit,
            supplier=supplier,
            created_by_user=user,
            updated_by_user=user,
        )
        apps.get_model("inventory", "StockBalance").objects.create(
            organization=organization, product=product, quantity=Decimal("10")
        )
        apps.get_model("sales", "SalesOrder").objects.create(
            organization=organization,
            customer=customer,
            document_no="SO-LEGACY",
            occurred_on=date(2026, 9, 1),
            created_by_user=user,
            updated_by_user=user,
        )
        apps.get_model("purchases", "Purchase").objects.create(
            organization=organization,
            supplier=supplier,
            document_no="PO-LEGACY",
            occurred_on=date(2026, 9, 1),
            created_by_user=user,
            updated_by_user=user,
        )
        labels = [
            ("partners", "Customer"),
            ("partners", "Supplier"),
            ("products", "Product"),
            ("products", "Unit"),
            ("inventory", "StockBalance"),
            ("inventory", "StockMovement"),
            ("sales", "SalesOrder"),
            ("purchases", "Purchase"),
        ]
        before = snapshot(apps, labels)
        MigrationExecutor(connection).migrate([NEW_TARGET])
        assert snapshot(apps, labels) == before
        for name in ("Customer", "Supplier"):
            model = apps.get_model("partners", name)
            with connection.cursor() as cursor:
                constraints = connection.introspection.get_constraints(cursor, model._meta.db_table)
            assert f"partners_{name.lower()}_organization_name_unique" not in constraints
            assert constraints[f"partners_{name.lower()}_identity_unique"]["unique"]
            original = customer if name == "Customer" else supplier
            model.objects.create(
                organization=organization, name=original.name, contact_name="不同联系人"
            )
            values = {
                field: getattr(original, field).strip()
                for field in ("name", "contact_name", "phone")
            }
            if name == "Supplier":
                values["contact_address"] = original.contact_address.strip()
            with pytest.raises(IntegrityError), transaction.atomic():
                model.objects.create(organization=organization, **values)
    finally:
        MigrationExecutor(connection).migrate(latest)


@pytest.mark.parametrize("model_name", ["Customer", "Supplier"])
def test_migration_stops_on_existing_normalized_duplicates_without_altering_records(model_name):
    apps, latest = migration_state()
    duplicate = None
    try:
        _, organization = create_owner(apps)
        model = apps.get_model("partners", model_name)
        values = {"contact_name": "联系人", "phone": "13800000000"}
        if model_name == "Supplier":
            values["contact_address"] = "地址"
        model.objects.create(organization=organization, name="Existing", **values)
        duplicate = model.objects.create(organization=organization, name=" Existing ", **values)
        before = list(model.objects.order_by("pk").values())
        with pytest.raises(RuntimeError, match="不会自动合并或删除"):
            MigrationExecutor(connection).migrate([NEW_TARGET])
        assert list(model.objects.order_by("pk").values()) == before
        assert NEW_TARGET not in MigrationExecutor(connection).loader.applied_migrations
    finally:
        if duplicate is not None:
            duplicate.delete()
        MigrationExecutor(connection).migrate(latest)
