from django.db import migrations, models
import django.db.models.deletion


def require_return_reconciliation(apps, schema_editor):
    purchase_return = apps.get_model("purchases", "PurchaseReturn")
    purchase_return_item = apps.get_model("purchases", "PurchaseReturnItem")
    if purchase_return.objects.exists() or purchase_return_item.objects.exists():
        raise RuntimeError(
            "Existing purchase returns must be reconciled to their original purchases before this migration."
        )


class Migration(migrations.Migration):
    dependencies = [("purchases", "0002_purchase_documents_remark")]

    operations = [
        migrations.AddField(
            model_name="purchasereturn",
            name="purchase",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="returns",
                to="purchases.purchase",
            ),
        ),
        migrations.AddField(
            model_name="purchasereturnitem",
            name="purchase_item",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="return_items",
                to="purchases.purchaseitem",
            ),
        ),
        migrations.RunPython(require_return_reconciliation, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="purchasereturn",
            name="purchase",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="returns",
                to="purchases.purchase",
            ),
        ),
        migrations.AlterField(
            model_name="purchasereturnitem",
            name="purchase_item",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="return_items",
                to="purchases.purchaseitem",
            ),
        ),
    ]