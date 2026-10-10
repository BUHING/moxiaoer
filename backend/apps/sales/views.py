from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers

from apps.accounts.services import effective_permissions
from apps.accounts.views import data_response, get_membership
from apps.products.views import PAGINATION_PARAMETERS, list_response, parse_uuid_parameter

from .models import SalesOrder, SalesReturn
from .serializers import (
    SalesDocumentWriteSerializer,
    SalesOrderSerializer,
    SalesReturnSerializer,
    SalesReturnWriteSerializer,
)
from .services import (
    complete_sales_order,
    complete_sales_return,
    create_sales_order,
    create_sales_return,
    delete_sales_order,
    delete_sales_return,
    update_sales_order,
    update_sales_return,
)


def require_sales_permission(user, permission: str):
    membership = get_membership(user)
    permissions = effective_permissions(membership)
    if not membership.is_active or ("*" not in permissions and permission not in permissions):
        raise PermissionDenied("Sales permission is required.")
    return membership


class SalesDocumentView(APIView):
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    write_serializer_class = SalesDocumentWriteSerializer
    permission = ""
    create_service = None
    update_service = None
    complete_service = None
    delete_service = None

    def get_queryset(self, organization):
        return self.model.objects.filter(organization=organization).select_related("customer", "completed_by_user").prefetch_related("items__product", "items__price_level")

    def get_object(self, organization, document_id):
        try:
            return self.get_queryset(organization).get(id=document_id)
        except self.model.DoesNotExist as error:
            raise NotFound("Sales document was not found.") from error

    def get(self, request, document_id=None):
        membership = require_sales_permission(request.user, self.permission)
        if document_id is not None:
            return data_response(self.serializer_class(self.get_object(membership.organization, document_id)).data)
        queryset = self.get_queryset(membership.organization)
        if status_value := request.query_params.get("status"):
            queryset = queryset.filter(status=status_value)
        if customer_id := parse_uuid_parameter(request, "customer_id"):
            queryset = queryset.filter(customer_id=customer_id)
        return list_response(request, queryset.order_by("-occurred_on", "-created_at"), self.serializer_class)

    def post(self, request):
        membership = require_sales_permission(request.user, self.permission)
        serializer = self.write_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = self.create_service(
            organization=membership.organization,
            user=request.user,
            values=serializer.validated_data,
        )
        return data_response(self.serializer_class(self.get_object(membership.organization, document.id)).data, status.HTTP_201_CREATED)

    def patch(self, request, document_id):
        membership = require_sales_permission(request.user, self.permission)
        document = self.get_object(membership.organization, document_id)
        serializer = self.write_serializer_class(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = self.update_service(document=document, user=request.user, values=serializer.validated_data)
        return data_response(self.serializer_class(self.get_object(membership.organization, updated.id)).data)

    def delete(self, request, document_id):
        membership = require_sales_permission(request.user, self.permission)
        try:
            self.delete_service(document_id=document_id, organization=membership.organization)
        except self.model.DoesNotExist as error:
            raise NotFound("Sales document was not found.") from error
        return Response(status=status.HTTP_204_NO_CONTENT)

    def complete(self, request, document_id):
        membership = require_sales_permission(request.user, self.permission)
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


sales_order_response = inline_serializer("SalesOrderResponse", fields={"data": SalesOrderSerializer()})
sales_order_list_response = inline_serializer("SalesOrderListResponse", fields={"data": SalesOrderSerializer(many=True), "meta": serializers.DictField()})
sales_return_response = inline_serializer("SalesReturnResponse", fields={"data": SalesReturnSerializer()})
sales_return_list_response = inline_serializer("SalesReturnListResponse", fields={"data": SalesReturnSerializer(many=True), "meta": serializers.DictField()})


@extend_schema_view(
    get=extend_schema(
        operation_id="sales_orders_list",
        parameters=[OpenApiParameter("status", str), OpenApiParameter("customer_id", str), *PAGINATION_PARAMETERS],
        responses={200: sales_order_list_response},
    ),
    post=extend_schema(operation_id="sales_orders_create", request=SalesDocumentWriteSerializer, responses={201: sales_order_response}),
)
class SalesOrderListCreateView(SalesDocumentView):
    http_method_names = ["get", "post", "options"]
    model = SalesOrder
    serializer_class = SalesOrderSerializer
    permission = "sales.create"
    create_service = staticmethod(create_sales_order)
    update_service = staticmethod(update_sales_order)
    complete_service = staticmethod(complete_sales_order)
    delete_service = staticmethod(delete_sales_order)


@extend_schema_view(
    get=extend_schema(operation_id="sales_orders_retrieve", responses={200: sales_order_response}),
    patch=extend_schema(operation_id="sales_orders_partial_update", request=SalesDocumentWriteSerializer, responses={200: sales_order_response}),
    delete=extend_schema(operation_id="sales_orders_delete", responses={204: None}),
)
class SalesOrderDetailView(SalesOrderListCreateView):
    http_method_names = ["get", "patch", "delete", "options"]


class SalesOrderCompleteView(SalesOrderListCreateView):
    http_method_names = ["post", "options"]

    @extend_schema(
        operation_id="sales_orders_complete",
        parameters=[OpenApiParameter("Idempotency-Key", str, location=OpenApiParameter.HEADER, required=True)],
        request=None,
        responses={200: sales_order_response},
    )
    def post(self, request, document_id):
        return self.complete(request, document_id)


@extend_schema_view(
    get=extend_schema(
        operation_id="sales_returns_list",
        parameters=[OpenApiParameter("status", str), OpenApiParameter("customer_id", str), *PAGINATION_PARAMETERS],
        responses={200: sales_return_list_response},
    ),
    post=extend_schema(operation_id="sales_returns_create", request=SalesDocumentWriteSerializer, responses={201: sales_return_response}),
)
class SalesReturnListCreateView(SalesDocumentView):
    http_method_names = ["get", "post", "options"]
    model = SalesReturn
    serializer_class = SalesReturnSerializer
    write_serializer_class = SalesReturnWriteSerializer
    permission = "sales.returns.manage"
    create_service = staticmethod(create_sales_return)
    update_service = staticmethod(update_sales_return)
    complete_service = staticmethod(complete_sales_return)
    delete_service = staticmethod(delete_sales_return)


@extend_schema_view(
    get=extend_schema(operation_id="sales_returns_retrieve", responses={200: sales_return_response}),
    patch=extend_schema(operation_id="sales_returns_partial_update", request=SalesDocumentWriteSerializer, responses={200: sales_return_response}),
    delete=extend_schema(operation_id="sales_returns_delete", responses={204: None}),
)
class SalesReturnDetailView(SalesReturnListCreateView):
    http_method_names = ["get", "patch", "delete", "options"]


class SalesReturnCompleteView(SalesReturnListCreateView):
    http_method_names = ["post", "options"]

    @extend_schema(
        operation_id="sales_returns_complete",
        parameters=[OpenApiParameter("Idempotency-Key", str, location=OpenApiParameter.HEADER, required=True)],
        request=None,
        responses={200: sales_return_response},
    )
    def post(self, request, document_id):
        return self.complete(request, document_id)