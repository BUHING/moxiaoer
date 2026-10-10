from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("purchases", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="purchase",
            name="remark",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="purchasereturn",
            name="remark",
            field=models.TextField(blank=True),
        ),
    ]