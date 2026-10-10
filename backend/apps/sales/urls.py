from django.urls import path

from .views import (
    SalesOrderCompleteView,
    SalesOrderDetailView,
    SalesOrderListCreateView,
    SalesReturnCompleteView,
    SalesReturnDetailView,
    SalesReturnListCreateView,
)

urlpatterns = [
    path("sales-orders/", SalesOrderListCreateView.as_view(), name="sales-order-list"),
    path("sales-orders/<uuid:document_id>/", SalesOrderDetailView.as_view(), name="sales-order-detail"),
    path("sales-orders/<uuid:document_id>/complete/", SalesOrderCompleteView.as_view(), name="sales-order-complete"),
    path("sales-returns/", SalesReturnListCreateView.as_view(), name="sales-return-list"),
    path("sales-returns/<uuid:document_id>/", SalesReturnDetailView.as_view(), name="sales-return-detail"),
    path("sales-returns/<uuid:document_id>/complete/", SalesReturnCompleteView.as_view(), name="sales-return-complete"),
]