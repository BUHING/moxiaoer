from django.db import migrations, models
import django.db.models.deletion


def require_return_reconciliation(apps, schema_editor):
    sales_return = apps.get_model("sales", "SalesReturn")
    sales_return_item = apps.get_model("sales", "SalesReturnItem")
    sales_order = apps.get_model("sales", "SalesOrder")
    sales_order_item = apps.get_model("sales", "SalesOrderItem")

    for return_document in sales_return.objects.all():
        return_items = list(sales_return_item.objects.filter(sales_return_id=return_document.id))
        reconciliations = []
        source_orders = sales_order.objects.filter(
            organization_id=return_document.organization_id,
            customer_id=return_document.customer_id,
            status="COMPLETED",
        )
        for source_order in source_orders:
            source_items = []
            for return_item in return_items:
                matching_items = list(
                    sales_order_item.objects.filter(
                        sales_order_id=source_order.id,
                        product_id=return_item.product_id,
                        unit_price=return_item.unit_price,
                        quantity__gte=return_item.quantity,
                    )
                )
                if len(matching_items) != 1:
                    break
                source_items.append(matching_items[0])
            else:
                reconciliations.append((source_order, source_items))

        if len(reconciliations) != 1:
            raise RuntimeError(
                f"Sales return {return_document.document_no} could not be uniquely reconciled to an original sales order."
            )

        source_order, source_items = reconciliations[0]
        sales_return.objects.filter(id=return_document.id).update(sales_order_id=source_order.id)
        for return_item, source_item in zip(return_items, source_items, strict=True):
            sales_return_item.objects.filter(id=return_item.id).update(sales_order_item_id=source_item.id)


class Migration(migrations.Migration):
    dependencies = [("sales", "0004_sales_documents_remark")]

    operations = [
        migrations.AddField(
            model_name="salesreturn",
            name="sales_order",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="returns",
                to="sales.salesorder",
            ),
        ),
        migrations.AddField(
            model_name="salesreturnitem",
            name="sales_order_item",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="return_items",
                to="sales.salesorderitem",
            ),
        ),
        migrations.RunPython(require_return_reconciliation, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="salesreturn",
            name="sales_order",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="returns",
                to="sales.salesorder",
            ),
        ),
        migrations.AlterField(
            model_name="salesreturnitem",
            name="sales_order_item",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="return_items",
                to="sales.salesorderitem",
            ),
        ),
    ]