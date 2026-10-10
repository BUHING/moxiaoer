from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0002_product_purchase_price_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="remark",
            field=models.TextField(blank=True),
        ),
    ]