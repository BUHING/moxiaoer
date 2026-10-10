from django.urls import path

from .views import LabelTemplateDetailView, LabelTemplateListCreateView

urlpatterns = [
    path("label-templates/", LabelTemplateListCreateView.as_view(), name="label-template-list"),
    path("label-templates/<uuid:template_id>/", LabelTemplateDetailView.as_view(), name="label-template-detail"),
]