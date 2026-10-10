import uuid

import django.db.models.deletion
from django.db import migrations, models


def create_default_warehouses(apps, schema_editor):
    organization_model = apps.get_model("accounts", "Organization")
    warehouse_model = apps.get_model("warehouses", "Warehouse")
    for organization in organization_model.objects.iterator():
        warehouse_model.objects.get_or_create(
            organization_id=organization.id,
            code="DEFAULT",
            defaults={"name": "默认仓库", "is_default": True},
        )


class Migration(migrations.Migration):
    initial = True
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Warehouse",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("code", models.CharField(max_length=32)),
                ("address", models.CharField(blank=True, max_length=255)),
                ("is_default", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="warehouses", to="accounts.organization")),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(fields=("organization", "name"), name="warehouses_warehouse_organization_name_unique"),
                    models.UniqueConstraint(fields=("organization", "code"), name="warehouses_warehouse_organization_code_unique"),
                    models.UniqueConstraint(condition=models.Q(("is_default", True)), fields=("organization",), name="warehouses_one_default_per_organization"),
                ],
            },
        ),
        migrations.RunPython(create_default_warehouses, migrations.RunPython.noop),
    ]