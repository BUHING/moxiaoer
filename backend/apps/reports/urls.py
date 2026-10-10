from django.urls import path

from .views import DashboardView, InventoryReportView, PurchaseReportView, SalesReportView

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("reports/sales/", SalesReportView.as_view(), name="sales-report"),
    path("reports/purchases/", PurchaseReportView.as_view(), name="purchase-report"),
    path("reports/inventory/", InventoryReportView.as_view(), name="inventory-report"),
]