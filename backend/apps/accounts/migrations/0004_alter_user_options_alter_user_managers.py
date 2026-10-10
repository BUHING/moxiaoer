import apps.accounts.models
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_disable_superusers")]

    operations = [
        migrations.AlterModelOptions(name="user", options={}),
        migrations.AlterModelManagers(
            name="user",
            managers=[("objects", apps.accounts.models.UserManager())],
        ),
    ]