from django.urls import path

from .views import (
    CustomerDeactivateView,
    CustomerDetailView,
    CustomerListCreateView,
    SupplierDeactivateView,
    SupplierDetailView,
    SupplierListCreateView,
)

urlpatterns = [
    path("customers/", CustomerListCreateView.as_view(), name="customer-list"),
    path("customers/<uuid:customer_id>/", CustomerDetailView.as_view(), name="customer-detail"),
    path(
        "customers/<uuid:customer_id>/deactivate/",
        CustomerDeactivateView.as_view(),
        name="customer-deactivate",
    ),
    path("suppliers/", SupplierListCreateView.as_view(), name="supplier-list"),
    path("suppliers/<uuid:supplier_id>/", SupplierDetailView.as_view(), name="supplier-detail"),
    path(
        "suppliers/<uuid:supplier_id>/deactivate/",
        SupplierDeactivateView.as_view(),
        name="supplier-deactivate",
    ),
]