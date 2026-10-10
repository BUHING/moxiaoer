from django.db import migrations
from django.db.models.deletion import ProtectedError


def remove_superuser_accounts(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Membership = apps.get_model("accounts", "Membership")

    for user in User.objects.filter(is_superuser=True):
        if Membership.objects.filter(user_id=user.id).exists():
            User.objects.filter(id=user.id).update(is_superuser=False, is_staff=False)
            continue
        try:
            user.delete()
        except ProtectedError:
            User.objects.filter(id=user.id).update(is_superuser=False, is_staff=False, is_active=False)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [migrations.RunPython(remove_superuser_accounts, migrations.RunPython.noop)]