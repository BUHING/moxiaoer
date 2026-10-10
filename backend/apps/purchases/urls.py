from django.urls import path

from .views import (
    PurchaseCompleteView,
    PurchaseDetailView,
    PurchaseListCreateView,
    PurchaseReturnCompleteView,
    PurchaseReturnDetailView,
    PurchaseReturnListCreateView,
)

urlpatterns = [
    path("purchases/", PurchaseListCreateView.as_view(), name="purchase-list"),
    path("purchases/<uuid:document_id>/", PurchaseDetailView.as_view(), name="purchase-detail"),
    path("purchases/<uuid:document_id>/complete/", PurchaseCompleteView.as_view(), name="purchase-complete"),
    path("purchase-returns/", PurchaseReturnListCreateView.as_view(), name="purchase-return-list"),
    path("purchase-returns/<uuid:document_id>/", PurchaseReturnDetailView.as_view(), name="purchase-return-detail"),
    path("purchase-returns/<uuid:document_id>/complete/", PurchaseReturnCompleteView.as_view(), name="purchase-return-complete"),
]