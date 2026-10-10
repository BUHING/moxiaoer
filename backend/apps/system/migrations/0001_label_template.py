import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("accounts", "0001_initial")

    operations = [
        migrations.CreateModel(
            name="LabelTemplate",
            fields=[
                ("id", models.UUIDField(default=__import__("uuid").uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("width_mm", models.DecimalField(decimal_places=2, max_digits=7)),
                ("height_mm", models.DecimalField(decimal_places=2, max_digits=7)),
                ("orientation", models.CharField(choices=[("PORTRAIT", "Portrait"), ("LANDSCAPE", "Landscape")], max_length=12)),
                ("template", models.JSONField(default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("created_by_user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_label_templates", to=settings.AUTH_USER_MODEL)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="label_templates", to="accounts.organization")),
                ("updated_by_user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="updated_label_templates", to=settings.AUTH_USER_MODEL)),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("organization", "name"), name="system_label_template_organization_name_unique")]},
        ),
    ]