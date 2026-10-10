from django.urls import path

from .views import StockBalanceListView, StockMovementListView

urlpatterns = [
    path("inventory/balances/", StockBalanceListView.as_view(), name="inventory-balance-list"),
    path("inventory/movements/", StockMovementListView.as_view(), name="inventory-movement-list"),
]