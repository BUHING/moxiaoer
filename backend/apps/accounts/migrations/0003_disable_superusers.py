from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_remove_superuser_accounts")]

    operations = [
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=models.Q(("is_superuser", False)),
                name="accounts_user_superuser_disabled",
            ),
        )
    ]