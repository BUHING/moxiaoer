from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("purchases", "0003_purchase_return_source_purchase"),
    ]

    operations = [
        migrations.AlterField(
            model_name="purchase",
            name="supplier",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="partners.supplier"),
        ),
        migrations.AlterField(
            model_name="purchasereturn",
            name="purchase",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="returns", to="purchases.purchase"),
        ),
        migrations.AlterField(
            model_name="purchasereturn",
            name="supplier",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="partners.supplier"),
        ),
        migrations.AlterField(
            model_name="purchasereturnitem",
            name="purchase_item",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="return_items", to="purchases.purchaseitem"),
        ),
    ]