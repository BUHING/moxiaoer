from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0003_product_remark"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="specification",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]