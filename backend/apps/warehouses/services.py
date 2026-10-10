from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.accounts.models import Organization

from .models import Warehouse


@transaction.atomic
def ensure_default_warehouse(*, organization: Organization) -> Warehouse:
    warehouse = Warehouse.objects.select_for_update().filter(organization=organization, is_default=True).first()
    if warehouse is not None:
        return warehouse
    return Warehouse.objects.create(organization=organization, name="默认仓库", code="DEFAULT", is_default=True)


def get_active_warehouse(*, organization: Organization, warehouse_id=None) -> Warehouse:
    queryset = Warehouse.objects.filter(organization=organization, is_active=True)
    warehouse = queryset.filter(id=warehouse_id).first() if warehouse_id else queryset.filter(is_default=True).first()
    if warehouse is None:
        raise ValidationError({"warehouse_id": ["Active warehouse was not found in the current organization."]})
    return warehouse