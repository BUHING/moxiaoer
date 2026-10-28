from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers

from apps.accounts.services import effective_permissions
from apps.accounts.views import data_response, get_membership
from apps.products.views import PAGINATION_PARAMETERS, list_response

from .models import Customer, Supplier
from .serializers import (
    CustomerSerializer,
    CustomerWriteSerializer,
    SupplierSerializer,
    SupplierWriteSerializer,
)
from .services import save_partner


class ResourceInUse(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "resource_in_use"
    default_detail = "该资源已被使用，无法删除。"


def require_partner_permission(user, permission: str):
    membership = get_membership(user)
    permissions = effective_permissions(membership)
    if not membership.is_active or ("*" not in permissions and permission not in permissions):
        raise PermissionDenied("Partner permission is required.")
    return membership


customer_response = inline_serializer("CustomerResponse", fields={"data": CustomerSerializer()})
customer_list_response = inline_serializer(
    "CustomerListResponse", fields={"data": CustomerSerializer(many=True), "meta": serializers.DictField()}
)


@extend_schema_view(
    get=extend_schema(
        operation_id="customers_list",
        parameters=[OpenApiParameter("is_active", bool), OpenApiParameter("search", str), *PAGINATION_PARAMETERS],
        responses={200: customer_list_response},
    ),
    post=extend_schema(operation_id="customers_create", request=CustomerWriteSerializer, responses={201: customer_response}),
)
class CustomerListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = require_partner_permission(request.user, "partners.view")
        customers = Customer.objects.filter(organization=membership.organization)
        if request.query_params.get("is_active") in {"true", "false"}:
            customers = customers.filter(is_active=request.query_params["is_active"] == "true")
        if search := request.query_params.get("search"):
            customers = customers.filter(name__icontains=search)
        return list_response(request, customers.order_by("name", "id"), CustomerSerializer)

    def post(self, request):
        membership = require_partner_permission(request.user, "partners.manage")
        serializer = CustomerWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = save_partner(
            model=Customer, organization=membership.organization, values=serializer.validated_data
        )
        return data_response(CustomerSerializer(customer).data, status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(operation_id="customers_retrieve", responses={200: customer_response}),
    patch=extend_schema(operation_id="customers_partial_update", request=CustomerWriteSerializer, responses={200: customer_response}),
    delete=extend_schema(operation_id="customers_destroy", responses={204: None}),
)
class CustomerDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, organization, customer_id):
        try:
            return Customer.objects.get(id=customer_id, organization=organization)
        except Customer.DoesNotExist as error:
            raise NotFound("Customer was not found.") from error

    def get(self, request, customer_id):
        membership = require_partner_permission(request.user, "partners.view")
        return data_response(CustomerSerializer(self.get_object(membership.organization, customer_id)).data)

    def patch(self, request, customer_id):
        membership = require_partner_permission(request.user, "partners.manage")
        customer = self.get_object(membership.organization, customer_id)
        serializer = CustomerWriteSerializer(customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        customer = save_partner(
            model=Customer,
            organization=membership.organization,
            values=serializer.validated_data,
            instance=customer,
        )
        return data_response(CustomerSerializer(customer).data)

    def delete(self, request, customer_id):
        membership = require_partner_permission(request.user, "partners.manage")
        customer = self.get_object(membership.organization, customer_id)
        try:
            customer.delete()
        except ProtectedError as error:
            raise ResourceInUse from error
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="customers_deactivate",
        request=None,
        responses={
            200: inline_serializer(
                "CustomerDeactivationResponse", fields={"data": serializers.DictField()}
            )
        },
    )
    def post(self, request, customer_id):
        membership = require_partner_permission(request.user, "partners.manage")
        customer = CustomerDetailView().get_object(membership.organization, customer_id)
        customer.is_active = False
        customer.save(update_fields=["is_active", "updated_at"])
        return data_response({"id": str(customer.id), "is_active": False})


supplier_response = inline_serializer("SupplierResponse", fields={"data": SupplierSerializer()})
supplier_list_response = inline_serializer(
    "SupplierListResponse", fields={"data": SupplierSerializer(many=True), "meta": serializers.DictField()}
)


class SupplierListCreateView(CustomerListCreateView):
    @extend_schema(
        operation_id="suppliers_list",
        parameters=[OpenApiParameter("is_active", bool), OpenApiParameter("search", str), *PAGINATION_PARAMETERS],
        responses={200: supplier_list_response},
    )
    def get(self, request):
        membership = require_partner_permission(request.user, "partners.view")
        suppliers = Supplier.objects.filter(organization=membership.organization)
        if request.query_params.get("is_active") in {"true", "false"}:
            suppliers = suppliers.filter(is_active=request.query_params["is_active"] == "true")
        if search := request.query_params.get("search"):
            suppliers = suppliers.filter(name__icontains=search)
        return list_response(request, suppliers.order_by("name", "id"), SupplierSerializer)

    @extend_schema(
        operation_id="suppliers_create",
        request=SupplierWriteSerializer,
        responses={201: supplier_response},
    )
    def post(self, request):
        membership = require_partner_permission(request.user, "partners.manage")
        serializer = SupplierWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = save_partner(
            model=Supplier, organization=membership.organization, values=serializer.validated_data
        )
        return data_response(SupplierSerializer(supplier).data, status.HTTP_201_CREATED)


class SupplierDetailView(CustomerDetailView):
    @extend_schema(operation_id="suppliers_retrieve", responses={200: supplier_response})
    def get(self, request, supplier_id):
        membership = require_partner_permission(request.user, "partners.view")
        return data_response(SupplierSerializer(self.get_object(membership.organization, supplier_id)).data)

    @extend_schema(
        operation_id="suppliers_partial_update",
        request=SupplierWriteSerializer,
        responses={200: supplier_response},
    )
    def patch(self, request, supplier_id):
        membership = require_partner_permission(request.user, "partners.manage")
        supplier = self.get_object(membership.organization, supplier_id)
        serializer = SupplierWriteSerializer(supplier, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        supplier = save_partner(
            model=Supplier,
            organization=membership.organization,
            values=serializer.validated_data,
            instance=supplier,
        )
        return data_response(SupplierSerializer(supplier).data)

    def get_object(self, organization, supplier_id):
        try:
            return Supplier.objects.get(id=supplier_id, organization=organization)
        except Supplier.DoesNotExist as error:
            raise NotFound("Supplier was not found.") from error

    @extend_schema(operation_id="suppliers_destroy", responses={204: None})
    def delete(self, request, supplier_id):
        membership = require_partner_permission(request.user, "partners.manage")
        supplier = self.get_object(membership.organization, supplier_id)
        try:
            supplier.delete()
        except ProtectedError as error:
            raise ResourceInUse from error
        return Response(status=status.HTTP_204_NO_CONTENT)


class SupplierDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="suppliers_deactivate",
        request=None,
        responses={200: inline_serializer("SupplierDeactivationResponse", fields={"data": serializers.DictField()})},
    )
    def post(self, request, supplier_id):
        membership = require_partner_permission(request.user, "partners.manage")
        supplier = SupplierDetailView().get_object(membership.organization, supplier_id)
        supplier.is_active = False
        supplier.save(update_fields=["is_active", "updated_at"])
        return data_response({"id": str(supplier.id), "is_active": False})