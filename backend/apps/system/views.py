from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers

from apps.accounts.services import effective_permissions
from apps.accounts.views import data_response, get_membership
from apps.products.views import list_response

from .models import LabelTemplate
from .serializers import LabelTemplateSerializer, LabelTemplateWriteSerializer


def require_label_template_permission(user):
    membership = get_membership(user)
    permissions = effective_permissions(membership)
    if not membership.is_active or ("*" not in permissions and "products.manage" not in permissions):
        raise PermissionDenied("Product management permission is required.")
    return membership


label_template_response = inline_serializer("LabelTemplateResponse", fields={"data": LabelTemplateSerializer()})
label_template_list_response = inline_serializer("LabelTemplateListResponse", fields={"data": LabelTemplateSerializer(many=True), "meta": serializers.DictField()})


@extend_schema_view(
    get=extend_schema(operation_id="label_templates_list", responses={200: label_template_list_response}),
    post=extend_schema(operation_id="label_templates_create", request=LabelTemplateWriteSerializer, responses={201: label_template_response}),
)
class LabelTemplateListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = require_label_template_permission(request.user)
        queryset = LabelTemplate.objects.filter(organization=membership.organization).order_by("name")
        return list_response(request, queryset, LabelTemplateSerializer)

    def post(self, request):
        membership = require_label_template_permission(request.user)
        serializer = LabelTemplateWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        label_template = LabelTemplate.objects.create(
            organization=membership.organization,
            created_by_user=request.user,
            updated_by_user=request.user,
            **serializer.validated_data,
        )
        return data_response(LabelTemplateSerializer(label_template).data, status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(operation_id="label_templates_retrieve", responses={200: label_template_response}),
    patch=extend_schema(operation_id="label_templates_partial_update", request=LabelTemplateWriteSerializer, responses={200: label_template_response}),
)
class LabelTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, organization, template_id):
        try:
            return LabelTemplate.objects.get(id=template_id, organization=organization)
        except LabelTemplate.DoesNotExist as error:
            raise NotFound("Label template was not found.") from error

    def get(self, request, template_id):
        membership = require_label_template_permission(request.user)
        return data_response(LabelTemplateSerializer(self.get_object(membership.organization, template_id)).data)

    def patch(self, request, template_id):
        membership = require_label_template_permission(request.user)
        label_template = self.get_object(membership.organization, template_id)
        serializer = LabelTemplateWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(label_template, field, value)
        label_template.updated_by_user = request.user
        label_template.save()
        return data_response(LabelTemplateSerializer(label_template).data)