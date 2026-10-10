from datetime import date, timedelta

from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.services import effective_permissions
from apps.accounts.views import get_membership

from .serializers import (
    DashboardSerializer,
    InventoryReportSerializer,
    PurchaseReportSerializer,
    SalesReportSerializer,
)
from .services import inventory_report, purchase_report, sales_report


dashboard_response = inline_serializer("DashboardResponse", fields={"data": DashboardSerializer()})
sales_report_response = inline_serializer("SalesReportResponse", fields={"data": SalesReportSerializer()})
purchase_report_response = inline_serializer(
    "PurchaseReportResponse", fields={"data": PurchaseReportSerializer()}
)
inventory_report_response = inline_serializer(
    "InventoryReportResponse", fields={"data": InventoryReportSerializer()}
)


def sales_metric(organization, date_from, date_to):
    report = sales_report(organization, date_from, date_to)
    return {
        "sales_order_count": report["sales_order_count"],
        "sales_amount": report["net_sales_amount"],
        "gross_profit": report["gross_profit"],
    }


def parse_date_range(request):
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    if not date_from or not date_to:
        raise ValidationError({"date": ["date_from and date_to are required."]})
    try:
        parsed_from = date.fromisoformat(date_from)
        parsed_to = date.fromisoformat(date_to)
    except ValueError as error:
        raise ValidationError({"date": ["date_from and date_to must use ISO date format."]}) from error
    if parsed_from > parsed_to:
        raise ValidationError({"date": ["date_from cannot be after date_to."]})
    return parsed_from, parsed_to


def require_report_permission(request, message: str):
    membership = get_membership(request.user)
    permissions = effective_permissions(membership)
    if not membership.is_active or ("*" not in permissions and "reports.view" not in permissions):
        raise PermissionDenied(message)
    return membership


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="dashboard_retrieve", responses={200: dashboard_response})
    def get(self, request):
        membership = get_membership(request.user)
        permissions = effective_permissions(membership)
        if not membership.is_active or ("*" not in permissions and "dashboard.view" not in permissions):
            raise PermissionDenied("Dashboard query permission is required.")
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        last_month_end = month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        serializer = DashboardSerializer({
            "today": sales_metric(membership.organization, today, today),
            "week": sales_metric(membership.organization, week_start, today),
            "month": sales_metric(membership.organization, month_start, today),
            "last_month": sales_metric(membership.organization, last_month_start, last_month_end),
        })
        return Response({"data": serializer.data})


class SalesReportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="reports_sales_retrieve",
        parameters=[OpenApiParameter("date_from", date), OpenApiParameter("date_to", date)],
        responses={200: sales_report_response},
    )
    def get(self, request):
        membership = require_report_permission(request, "Sales report query permission is required.")
        date_from, date_to = parse_date_range(request)
        data = sales_report(membership.organization, date_from, date_to)
        return Response({"data": SalesReportSerializer(data).data})


class PurchaseReportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="reports_purchases_retrieve",
        parameters=[OpenApiParameter("date_from", date), OpenApiParameter("date_to", date)],
        responses={200: purchase_report_response},
    )
    def get(self, request):
        membership = require_report_permission(request, "Purchase report query permission is required.")
        date_from, date_to = parse_date_range(request)
        data = purchase_report(membership.organization, date_from, date_to)
        return Response({"data": PurchaseReportSerializer(data).data})


class InventoryReportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="reports_inventory_retrieve", responses={200: inventory_report_response})
    def get(self, request):
        membership = require_report_permission(request, "Inventory report query permission is required.")
        data = inventory_report(membership.organization)
        return Response({"data": InventoryReportSerializer(data).data})