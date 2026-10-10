from django.utils.dateparse import parse_date
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.services import effective_permissions
from apps.accounts.views import get_membership

from .models import StockBalance, StockMovement
from .serializers import StockBalanceSerializer, StockMovementSerializer


def require_inventory_permission(user):
    membership = get_membership(user)
    if not membership.is_active:
        raise PermissionDenied("Active organization membership is required.")
    permissions = effective_permissions(membership)
    if "*" not in permissions and "inventory.view" not in permissions:
        raise PermissionDenied("Inventory view permission is required.")
    return membership


def paginated_response(request, queryset, serializer_class):
    try:
        page = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
    except ValueError as error:
        raise ValidationError({"pagination": ["page and page_size must be integers."]}) from error
    total = queryset.count()
    offset = (page - 1) * page_size
    data = serializer_class(queryset[offset : offset + page_size], many=True).data
    return Response({"data": data, "meta": {"page": page, "page_size": page_size, "total": total}})


def parse_date_parameter(request, name: str):
    value = request.query_params.get(name)
    if not value:
        return None
    parsed = parse_date(value)
    if parsed is None:
        raise ValidationError({name: ["Use ISO 8601 date format (YYYY-MM-DD)."]})
    return parsed


def parse_uuid_parameter(request, name: str):
    value = request.query_params.get(name)
    if not value:
        return None
    field = serializers.UUIDField()
    try:
        return field.run_validation(value)
    except serializers.ValidationError as error:
        raise ValidationError({name: error.detail}) from error


balance_list_response = inline_serializer(
    "StockBalanceListResponse",
    fields={"data": StockBalanceSerializer(many=True), "meta": serializers.DictField()},
)
movement_list_response = inline_serializer(
    "StockMovementListResponse",
    fields={"data": StockMovementSerializer(many=True), "meta": serializers.DictField()},
)


class StockBalanceListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="inventory_balances_list",
        parameters=[
            OpenApiParameter("search", str),
            OpenApiParameter("product_id", str),
            OpenApiParameter("page", int),
            OpenApiParameter("page_size", int),
        ],
        responses={200: balance_list_response},
    )
    def get(self, request):
        membership = require_inventory_permission(request.user)
        queryset = StockBalance.objects.filter(organization=membership.organization).select_related(
            "product", "product__unit"
        )
        if product_id := parse_uuid_parameter(request, "product_id"):
            queryset = queryset.filter(product_id=product_id)
        if search := request.query_params.get("search"):
            queryset = queryset.filter(product__name__icontains=search)
        return paginated_response(request, queryset.order_by("product__name", "id"), StockBalanceSerializer)


class StockMovementListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="inventory_movements_list",
        parameters=[
            OpenApiParameter("search", str),
            OpenApiParameter("product_id", str),
            OpenApiParameter("movement_type", str, enum=StockMovement.MovementType.values),
            OpenApiParameter("date_from", str),
            OpenApiParameter("date_to", str),
            OpenApiParameter("page", int),
            OpenApiParameter("page_size", int),
        ],
        responses={200: movement_list_response},
    )
    def get(self, request):
        membership = require_inventory_permission(request.user)
        queryset = StockMovement.objects.filter(organization=membership.organization).select_related(
            "product", "product__unit", "operator_user"
        )
        if product_id := parse_uuid_parameter(request, "product_id"):
            queryset = queryset.filter(product_id=product_id)
        if movement_type := request.query_params.get("movement_type"):
            if movement_type not in StockMovement.MovementType.values:
                raise ValidationError({"movement_type": ["Unsupported movement type."]})
            queryset = queryset.filter(movement_type=movement_type)
        if search := request.query_params.get("search"):
            queryset = queryset.filter(product__name__icontains=search)
        if date_from := parse_date_parameter(request, "date_from"):
            queryset = queryset.filter(occurred_at__date__gte=date_from)
        if date_to := parse_date_parameter(request, "date_to"):
            queryset = queryset.filter(occurred_at__date__lte=date_to)
        return paginated_response(request, queryset.order_by("-occurred_at", "-id"), StockMovementSerializer)