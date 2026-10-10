import uuid

from django.db import models
from django.db.models import Q

from apps.accounts.models import Organization, TimestampedModel


class Warehouse(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="warehouses")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=32)
    address = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organization", "name"], name="warehouses_warehouse_organization_name_unique"),
            models.UniqueConstraint(fields=["organization", "code"], name="warehouses_warehouse_organization_code_unique"),
            models.UniqueConstraint(fields=["organization"], condition=Q(is_default=True), name="warehouses_one_default_per_organization"),
        ]