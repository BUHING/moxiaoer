from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sales", "0003_salesorderitem_cost_amount_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="salesorder",
            name="remark",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="salesreturn",
            name="remark",
            field=models.TextField(blank=True),
        ),
    ]