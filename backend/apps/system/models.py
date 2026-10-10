import uuid

from django.conf import settings
from django.db import models

from apps.accounts.models import Organization, TimestampedModel


class LabelTemplate(TimestampedModel):
    class Orientation(models.TextChoices):
        PORTRAIT = "PORTRAIT", "Portrait"
        LANDSCAPE = "LANDSCAPE", "Landscape"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="label_templates")
    name = models.CharField(max_length=100)
    width_mm = models.DecimalField(max_digits=7, decimal_places=2)
    height_mm = models.DecimalField(max_digits=7, decimal_places=2)
    orientation = models.CharField(max_length=12, choices=Orientation.choices)
    template = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_label_templates")
    updated_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="updated_label_templates")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "name"], name="system_label_template_organization_name_unique")]