from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.services import effective_permissions
from apps.accounts.views import data_response, get_membership
from apps.products.views import PAGINATION_PARAMETERS, list_response, parse_uuid_parameter

from .models import Purchase, PurchaseReturn
from .serializers import (
    PurchaseDocumentWriteSerializer,
    PurchaseReturnSerializer,
    PurchaseReturnWriteSerializer,
    PurchaseSerializer,
)
from .services import (
    complete_purchase,
    complete_purchase_return,
    create_purchase,
    create_purchase_return,
    delete_purchase,
    delete_purchase_return,
    update_purchase,
    update_purchase_return,
)


def require_purchase_permission(user, permission: str):
    membership = get_membership(user)
    permissions = effective_permissions(membership)
    if not membership.is_active or ("*" not in permissions and permission not in permissions):
        raise PermissionDenied("Purchase permission is required.")
    return membership


class PurchaseDocumentView(APIView):
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    write_serializer_class = PurchaseDocumentWriteSerializer
    permission = ""
    create_service = None
    update_service = None
    complete_service = None
    delete_service = None

    def get_queryset(self, organization):
        return self.model.objects.filter(organization=organization).select_related(
            "supplier", "completed_by_user"
        ).prefetch_related("items__product")

    def get_object(self, organization, document_id):
        try:
            return self.get_queryset(organization).get(id=document_id)
        except self.model.DoesNotExist as error:
            raise NotFound("Purchase document was not found.") from error

    def get(self, request, document_id=None):
        membership = require_purchase_permission(request.user, self.permission)
        if document_id is not None:
            return data_response(self.serializer_class(self.get_object(membership.organization, document_id)).data)
        queryset = self.get_queryset(membership.organization)
        if status_value := request.query_params.get("status"):
            queryset = queryset.filter(status=status_value)
        if supplier_id := parse_uuid_parameter(request, "supplier_id"):
            queryset = queryset.filter(supplier_id=supplier_id)
        return list_response(request, queryset.order_by("-occurred_on", "-created_at"), self.serializer_class)

    def post(self, request):
        membership = require_purchase_permission(request.user, self.permission)
        serializer = self.write_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = self.create_service(
            organization=membership.organization,
            user=request.user,
            values=serializer.validated_data,
        )
        return data_response(
            self.serializer_class(self.get_object(membership.organization, document.id)).data,
            status.HTTP_201_CREATED,
        )

    def patch(self, request, document_id):
        membership = require_purchase_permission(request.user, self.permission)
        document = self.get_object(membership.organization, document_id)
        serializer = self.write_serializer_class(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = self.update_service(document=document, user=request.user, values=serializer.validated_data)
        return data_response(self.serializer_class(self.get_object(membership.organization, updated.id)).data)

    def delete(self, request, document_id):
        membership = require_purchase_permission(request.user, self.permission)
        try:
            self.delete_service(document_id=document_id, organization=membership.organization)
        except self.model.DoesNotExist as error:
            raise NotFound("Purchase document was not found.") from error
        return Response(status=status.HTTP_204_NO_CONTENT)

    def complete(self, request, document_id):
        membership = require_purchase_permission(request.user, self.permission)
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            raise ValidationError({"Idempotency-Key": ["This header is required."]})
        if len(idempotency_key) > 255:
            raise ValidationError({"Idempotency-Key": ["Ensure this header has at most 255 characters."]})
        document = self.complete_service(
            document_id=document_id,
            organization=membership.organization,
            user=request.user,
            idempotency_key=idempotency_key,
        )
        return data_response(self.serializer_class(self.get_object(membership.organization, document.id)).data)


purchase_response = inline_serializer("PurchaseResponse", fields={"data": PurchaseSerializer()})
purchase_list_response = inline_serializer("PurchaseListResponse", fields={"data": PurchaseSerializer(many=True), "meta": serializers.DictField()})
purchase_return_response = inline_serializer("PurchaseReturnResponse", fields={"data": PurchaseReturnSerializer()})
purchase_return_list_response = inline_serializer("PurchaseReturnListResponse", fields={"data": PurchaseReturnSerializer(many=True), "meta": serializers.DictField()})


@extend_schema_view(
    get=extend_schema(
        operation_id="purchases_list",
        parameters=[OpenApiParameter("status", str), OpenApiParameter("supplier_id", str), *PAGINATION_PARAMETERS],
        responses={200: purchase_list_response},
    ),
    post=extend_schema(operation_id="purchases_create", request=PurchaseDocumentWriteSerializer, responses={201: purchase_response}),
)
class PurchaseListCreateView(PurchaseDocumentView):
    http_method_names = ["get", "post", "options"]
    model = Purchase
    serializer_class = PurchaseSerializer
    permission = "purchases.create"
    create_service = staticmethod(create_purchase)
    update_service = staticmethod(update_purchase)
    complete_service = staticmethod(complete_purchase)
    delete_service = staticmethod(delete_purchase)


@extend_schema_view(
    get=extend_schema(operation_id="purchases_retrieve", responses={200: purchase_response}),
    patch=extend_schema(operation_id="purchases_partial_update", request=PurchaseDocumentWriteSerializer, responses={200: purchase_response}),
    delete=extend_schema(operation_id="purchases_delete", responses={204: None}),
)
class PurchaseDetailView(PurchaseListCreateView):
    http_method_names = ["get", "patch", "delete", "options"]


class PurchaseCompleteView(PurchaseListCreateView):
    http_method_names = ["post", "options"]

    @extend_schema(operation_id="purchases_complete", parameters=[OpenApiParameter("Idempotency-Key", str, location=OpenApiParameter.HEADER, required=True)], request=None, responses={200: purchase_response})
    def post(self, request, document_id):
        return self.complete(request, document_id)


@extend_schema_view(
    get=extend_schema(
        operation_id="purchase_returns_list",
        parameters=[OpenApiParameter("status", str), OpenApiParameter("supplier_id", str), *PAGINATION_PARAMETERS],
        responses={200: purchase_return_list_response},
    ),
    post=extend_schema(operation_id="purchase_returns_create", request=PurchaseReturnWriteSerializer, responses={201: purchase_return_response}),
)
class PurchaseReturnListCreateView(PurchaseDocumentView):
    http_method_names = ["get", "post", "options"]
    model = PurchaseReturn
    serializer_class = PurchaseReturnSerializer
    write_serializer_class = PurchaseReturnWriteSerializer
    permission = "purchases.returns.manage"
    create_service = staticmethod(create_purchase_return)
    update_service = staticmethod(update_purchase_return)
    complete_service = staticmethod(complete_purchase_return)
    delete_service = staticmethod(delete_purchase_return)


@extend_schema_view(
    get=extend_schema(operation_id="purchase_returns_retrieve", responses={200: purchase_return_response}),
    patch=extend_schema(operation_id="purchase_returns_partial_update", request=PurchaseReturnWriteSerializer, responses={200: purchase_return_response}),
    delete=extend_schema(operation_id="purchase_returns_delete", responses={204: None}),
)
class PurchaseReturnDetailView(PurchaseReturnListCreateView):
    http_method_names = ["get", "patch", "delete", "options"]


class PurchaseReturnCompleteView(PurchaseReturnListCreateView):
    http_method_names = ["post", "options"]

    @extend_schema(operation_id="purchase_returns_complete", parameters=[OpenApiParameter("Idempotency-Key", str, location=OpenApiParameter.HEADER, required=True)], request=None, responses={200: purchase_return_response})
    def post(self, request, document_id):
        return self.complete(request, document_id)