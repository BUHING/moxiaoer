from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("sales", "0005_sales_return_source_order"),
    ]

    operations = [
        migrations.AlterField(
            model_name="salesorder",
            name="customer",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="partners.customer"),
        ),
        migrations.AlterField(
            model_name="salesreturn",
            name="customer",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="partners.customer"),
        ),
    ]