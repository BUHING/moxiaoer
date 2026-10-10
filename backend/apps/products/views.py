from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers

from apps.accounts.services import effective_permissions
from apps.accounts.views import data_response, get_membership
from apps.partners.models import PriceLevel

from .models import AttributeOption, Product, ProductAttribute, Specification, Unit
from .serializers import (
    AttributeOptionSerializer,
    AttributeOptionWriteSerializer,
    PriceLevelWriteSerializer,
    PriceLevelSerializer,
    ProductAttributeSerializer,
    ProductAttributeWriteSerializer,
    ProductPriceSerializer,
    ProductSerializer,
    ProductWriteSerializer,
    SpecificationSerializer,
    SpecificationWriteSerializer,
    UnitSerializer,
    UnitWriteSerializer,
)
from .services import create_product, update_product


PAGINATION_PARAMETERS = [OpenApiParameter("page", int), OpenApiParameter("page_size", int)]


class ResourceInUse(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "resource_in_use"
    default_detail = "该资源已被使用，无法删除。"


class ResourceAlreadyExists(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "resource_already_exists"
    default_detail = "名称已存在。"


class PriceLevelLimit(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "price_level_limit"
    default_detail = "No more than six active price levels are allowed."


def require_product_permission(user, permission: str):
    membership = get_membership(user)
    if not membership.is_active:
        raise PermissionDenied("Active organization membership is required.")
    permissions = effective_permissions(membership)
    if "*" not in permissions and permission not in permissions:
        raise PermissionDenied("Product permission is required.")
    return membership


def get_pagination(request):
    try:
        page = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
    except ValueError as error:
        raise ValidationError({"pagination": ["page and page_size must be integers."]}) from error
    return page, page_size


def parse_uuid_parameter(request, name: str):
    value = request.query_params.get(name)
    if not value:
        return None
    field = serializers.UUIDField()
    try:
        return field.run_validation(value)
    except serializers.ValidationError as error:
        raise ValidationError({name: error.detail}) from error


def list_response(request, queryset, serializer_class):
    page, page_size = get_pagination(request)
    total = queryset.count()
    offset = (page - 1) * page_size
    data = serializer_class(queryset[offset : offset + page_size], many=True).data
    return Response({"data": data, "meta": {"page": page, "page_size": page_size, "total": total}})


class OrganizationCatalogListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    write_serializer_class = None

    def get_queryset(self, organization):
        return self.model.objects.filter(organization=organization).order_by("name")

    def get(self, request):
        membership = require_product_permission(request.user, "products.view")
        queryset = self.get_queryset(membership.organization)
        is_active = request.query_params.get("is_active")
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=is_active == "true")
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)
        return list_response(request, queryset, self.serializer_class)

    def post(self, request):
        membership = require_product_permission(request.user, "products.manage")
        serializer = self.write_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            instance = self.model.objects.create(
                organization=membership.organization, **serializer.validated_data
            )
        except IntegrityError as error:
            raise ResourceAlreadyExists from error
        return data_response(self.serializer_class(instance).data, status.HTTP_201_CREATED)


class OrganizationCatalogDetailView(APIView):
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    write_serializer_class = None

    def get_object(self, organization, resource_id):
        try:
            return self.model.objects.get(id=resource_id, organization=organization)
        except self.model.DoesNotExist as error:
            raise NotFound("Resource was not found.") from error

    def get(self, request, resource_id):
        membership = require_product_permission(request.user, "products.view")
        return data_response(self.serializer_class(self.get_object(membership.organization, resource_id)).data)

    def patch(self, request, resource_id):
        membership = require_product_permission(request.user, "products.manage")
        instance = self.get_object(membership.organization, resource_id)
        serializer = self.write_serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field_name, value in serializer.validated_data.items():
            setattr(instance, field_name, value)
        try:
            instance.save()
        except IntegrityError as error:
            raise ResourceAlreadyExists from error
        return data_response(self.serializer_class(instance).data)

    def delete(self, request, resource_id):
        membership = require_product_permission(request.user, "products.manage")
        instance = self.get_object(membership.organization, resource_id)
        try:
            instance.delete()
        except ProtectedError as error:
            raise ResourceInUse from error
        return Response(status=status.HTTP_204_NO_CONTENT)


class CatalogDeactivateView(APIView):
    permission_classes = [IsAuthenticated]
    model = None

    @extend_schema(request=None, responses={200: inline_serializer("DeactivationResponse", fields={"data": serializers.DictField()})})
    def post(self, request, resource_id):
        membership = require_product_permission(request.user, "products.manage")
        try:
            instance = self.model.objects.get(id=resource_id, organization=membership.organization)
        except self.model.DoesNotExist as error:
            raise NotFound("Resource was not found.") from error
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
        return Response({"data": {"id": str(instance.id), "is_active": False}})


unit_response = inline_serializer("UnitResponse", fields={"data": UnitSerializer()})
unit_list_response = inline_serializer(
    "UnitListResponse", fields={"data": UnitSerializer(many=True), "meta": serializers.DictField()}
)


@extend_schema_view(
    get=extend_schema(
        operation_id="units_list", parameters=PAGINATION_PARAMETERS, responses={200: unit_list_response}
    ),
    post=extend_schema(operation_id="units_create", request=UnitWriteSerializer, responses={201: unit_response}),
)
class UnitListCreateView(OrganizationCatalogListCreateView):
    model = Unit
    serializer_class = UnitSerializer
    write_serializer_class = UnitWriteSerializer


@extend_schema_view(
    get=extend_schema(operation_id="units_retrieve", responses={200: unit_response}),
    patch=extend_schema(operation_id="units_partial_update", request=UnitWriteSerializer, responses={200: unit_response}),
    delete=extend_schema(operation_id="units_destroy", responses={204: None}),
)
class UnitDetailView(OrganizationCatalogDetailView):
    model = Unit
    serializer_class = UnitSerializer
    write_serializer_class = UnitWriteSerializer


class UnitDeactivateView(CatalogDeactivateView):
    model = Unit


specification_response = inline_serializer("SpecificationResponse", fields={"data": SpecificationSerializer()})
specification_list_response = inline_serializer(
    "SpecificationListResponse",
    fields={"data": SpecificationSerializer(many=True), "meta": serializers.DictField()},
)


@extend_schema_view(
    get=extend_schema(
        operation_id="specifications_list",
        parameters=PAGINATION_PARAMETERS,
        responses={200: specification_list_response},
    ),
    post=extend_schema(
        operation_id="specifications_create",
        request=SpecificationWriteSerializer,
        responses={201: specification_response},
    ),
)
class SpecificationListCreateView(OrganizationCatalogListCreateView):
    model = Specification
    serializer_class = SpecificationSerializer
    write_serializer_class = SpecificationWriteSerializer


@extend_schema_view(
    get=extend_schema(operation_id="specifications_retrieve", responses={200: specification_response}),
    patch=extend_schema(
        operation_id="specifications_partial_update",
        request=SpecificationWriteSerializer,
        responses={200: specification_response},
    ),
    delete=extend_schema(operation_id="specifications_destroy", responses={204: None}),
)
class SpecificationDetailView(OrganizationCatalogDetailView):
    model = Specification
    serializer_class = SpecificationSerializer
    write_serializer_class = SpecificationWriteSerializer


class SpecificationDeactivateView(CatalogDeactivateView):
    model = Specification


product_attribute_response = inline_serializer(
    "ProductAttributeResponse", fields={"data": ProductAttributeSerializer()}
)
product_attribute_list_response = inline_serializer(
    "ProductAttributeListResponse",
    fields={"data": ProductAttributeSerializer(many=True), "meta": serializers.DictField()},
)


@extend_schema_view(
    get=extend_schema(
        operation_id="product_attributes_list",
        parameters=PAGINATION_PARAMETERS,
        responses={200: product_attribute_list_response},
    ),
    post=extend_schema(
        operation_id="product_attributes_create",
        request=ProductAttributeWriteSerializer,
        responses={201: product_attribute_response},
    ),
)
class ProductAttributeListCreateView(OrganizationCatalogListCreateView):
    model = ProductAttribute
    serializer_class = ProductAttributeSerializer
    write_serializer_class = ProductAttributeWriteSerializer


@extend_schema_view(
    get=extend_schema(operation_id="product_attributes_retrieve", responses={200: product_attribute_response}),
    patch=extend_schema(
        operation_id="product_attributes_partial_update",
        request=ProductAttributeWriteSerializer,
        responses={200: product_attribute_response},
    ),
    delete=extend_schema(operation_id="product_attributes_destroy", responses={204: None}),
)
class ProductAttributeDetailView(OrganizationCatalogDetailView):
    model = ProductAttribute
    serializer_class = ProductAttributeSerializer
    write_serializer_class = ProductAttributeWriteSerializer


class ProductAttributeDeactivateView(CatalogDeactivateView):
    model = ProductAttribute


price_level_response = inline_serializer("PriceLevelResponse", fields={"data": PriceLevelSerializer()})
price_level_list_response = inline_serializer(
    "PriceLevelListResponse",
    fields={"data": PriceLevelSerializer(many=True), "meta": serializers.DictField()},
)


@extend_schema_view(
    get=extend_schema(
        operation_id="price_levels_list",
        parameters=PAGINATION_PARAMETERS,
        responses={200: price_level_list_response},
    ),
    post=extend_schema(
        operation_id="price_levels_create",
        request=PriceLevelWriteSerializer,
        responses={201: price_level_response},
    ),
)
class PriceLevelListCreateView(OrganizationCatalogListCreateView):
    model = PriceLevel
    serializer_class = PriceLevelSerializer
    write_serializer_class = PriceLevelWriteSerializer

    def get_queryset(self, organization):
        return self.model.objects.filter(organization=organization).order_by("sort_order", "name")

    def post(self, request):
        membership = require_product_permission(request.user, "products.manage")
        if PriceLevel.objects.filter(organization=membership.organization, is_active=True).count() >= 6:
            raise PriceLevelLimit
        return super().post(request)


@extend_schema_view(
    get=extend_schema(operation_id="price_levels_retrieve", responses={200: price_level_response}),
    patch=extend_schema(
        operation_id="price_levels_partial_update",
        request=PriceLevelWriteSerializer,
        responses={200: price_level_response},
    ),
    delete=extend_schema(operation_id="price_levels_destroy", responses={204: None}),
)
class PriceLevelDetailView(OrganizationCatalogDetailView):
    model = PriceLevel
    serializer_class = PriceLevelSerializer
    write_serializer_class = PriceLevelWriteSerializer

    def patch(self, request, resource_id):
        membership = require_product_permission(request.user, "products.manage")
        price_level = self.get_object(membership.organization, resource_id)
        if (
            request.data.get("is_active") is True
            and not price_level.is_active
            and PriceLevel.objects.filter(organization=membership.organization, is_active=True).count() >= 6
        ):
            raise PriceLevelLimit
        return super().patch(request, resource_id)


class PriceLevelDeactivateView(CatalogDeactivateView):
    model = PriceLevel


attribute_option_response = inline_serializer("AttributeOptionResponse", fields={"data": AttributeOptionSerializer()})
attribute_option_list_response = inline_serializer(
    "AttributeOptionListResponse",
    fields={"data": AttributeOptionSerializer(many=True), "meta": serializers.DictField()},
)


@extend_schema_view(
    get=extend_schema(
        operation_id="product_attribute_options_list",
        parameters=PAGINATION_PARAMETERS,
        responses={200: attribute_option_list_response},
    ),
    post=extend_schema(
        operation_id="product_attribute_options_create",
        request=AttributeOptionWriteSerializer,
        responses={201: attribute_option_response},
    ),
)
class AttributeOptionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_attribute(self, organization, attribute_id):
        try:
            return ProductAttribute.objects.get(id=attribute_id, organization=organization)
        except ProductAttribute.DoesNotExist as error:
            raise NotFound("Product attribute was not found.") from error

    def get(self, request, attribute_id):
        membership = require_product_permission(request.user, "products.view")
        attribute = self.get_attribute(membership.organization, attribute_id)
        return list_response(request, attribute.options.order_by("value"), AttributeOptionSerializer)

    def post(self, request, attribute_id):
        membership = require_product_permission(request.user, "products.manage")
        attribute = self.get_attribute(membership.organization, attribute_id)
        if attribute.input_type != ProductAttribute.InputType.SELECT:
            raise PermissionDenied("Only select attributes support options.")
        serializer = AttributeOptionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        option = AttributeOption.objects.create(attribute=attribute, **serializer.validated_data)
        return data_response(AttributeOptionSerializer(option).data, status.HTTP_201_CREATED)


@extend_schema_view(
    patch=extend_schema(
        operation_id="product_attribute_options_partial_update",
        request=AttributeOptionWriteSerializer,
        responses={200: attribute_option_response},
    ),
    delete=extend_schema(operation_id="product_attribute_options_destroy", responses={204: None}),
)
class AttributeOptionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_option(self, organization, attribute_id, option_id):
        try:
            return AttributeOption.objects.get(
                id=option_id,
                attribute_id=attribute_id,
                attribute__organization=organization,
            )
        except AttributeOption.DoesNotExist as error:
            raise NotFound("Attribute option was not found.") from error

    def patch(self, request, attribute_id, option_id):
        membership = require_product_permission(request.user, "products.manage")
        option = self.get_option(membership.organization, attribute_id, option_id)
        serializer = AttributeOptionWriteSerializer(option, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field_name, value in serializer.validated_data.items():
            setattr(option, field_name, value)
        option.save()
        return data_response(AttributeOptionSerializer(option).data)

    def delete(self, request, attribute_id, option_id):
        membership = require_product_permission(request.user, "products.manage")
        option = self.get_option(membership.organization, attribute_id, option_id)
        try:
            option.delete()
        except ProtectedError as error:
            raise ResourceInUse from error
        return Response(status=status.HTTP_204_NO_CONTENT)


product_response = inline_serializer("ProductResponse", fields={"data": ProductSerializer()})
product_list_response = inline_serializer(
    "ProductListResponse",
    fields={"data": ProductSerializer(many=True), "meta": serializers.DictField()},
)
product_price_list_response = inline_serializer(
    "ProductPriceListResponse", fields={"data": ProductPriceSerializer(many=True)}
)


@extend_schema_view(
    get=extend_schema(
        operation_id="products_list",
        parameters=[
            OpenApiParameter("is_active", bool),
            OpenApiParameter("search", str),
            OpenApiParameter("unit_id", str),
            OpenApiParameter("price_level_id", str),
            *PAGINATION_PARAMETERS,
        ],
        responses={200: product_list_response},
    ),
    post=extend_schema(operation_id="products_create", request=ProductWriteSerializer, responses={201: product_response}),
)
class ProductListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, organization):
        return Product.objects.filter(organization=organization).select_related("unit", "supplier", "stock_balance").prefetch_related(
            "specification_values__specification",
            "attribute_values__attribute",
            "attribute_values__option",
            "prices__price_level",
        )

    def get(self, request):
        membership = require_product_permission(request.user, "products.view")
        queryset = self.get_queryset(membership.organization)
        if request.query_params.get("is_active") in {"true", "false"}:
            queryset = queryset.filter(is_active=request.query_params["is_active"] == "true")
        if search := request.query_params.get("search"):
            queryset = queryset.filter(name__icontains=search)
        if unit_id := parse_uuid_parameter(request, "unit_id"):
            queryset = queryset.filter(unit_id=unit_id)
        if price_level_id := parse_uuid_parameter(request, "price_level_id"):
            queryset = queryset.filter(prices__price_level_id=price_level_id)
        return list_response(request, queryset.order_by("-created_at").distinct(), ProductSerializer)

    def post(self, request):
        membership = require_product_permission(request.user, "products.manage")
        serializer = ProductWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = create_product(
            organization=membership.organization,
            user=request.user,
            values=serializer.validated_data.copy(),
        )
        return data_response(ProductSerializer(self.get_queryset(membership.organization).get(id=product.id)).data, status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(operation_id="products_retrieve", responses={200: product_response}),
    patch=extend_schema(operation_id="products_partial_update", request=ProductWriteSerializer, responses={200: product_response}),
    delete=extend_schema(operation_id="products_destroy", responses={204: None}),
)
class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, organization):
        return Product.objects.filter(organization=organization).select_related("unit", "supplier", "stock_balance").prefetch_related(
            "specification_values__specification",
            "attribute_values__attribute",
            "attribute_values__option",
            "prices__price_level",
        )

    def get_object(self, organization, product_id):
        try:
            return self.get_queryset(organization).get(id=product_id)
        except Product.DoesNotExist as error:
            raise NotFound("Product was not found.") from error

    def get(self, request, product_id):
        membership = require_product_permission(request.user, "products.view")
        return data_response(ProductSerializer(self.get_object(membership.organization, product_id)).data)

    def patch(self, request, product_id):
        membership = require_product_permission(request.user, "products.manage")
        product = self.get_object(membership.organization, product_id)
        serializer = ProductWriteSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_product = update_product(product=product, user=request.user, values=serializer.validated_data.copy())
        return data_response(ProductSerializer(self.get_object(membership.organization, updated_product.id)).data)

    def delete(self, request, product_id):
        membership = require_product_permission(request.user, "products.manage")
        product = self.get_object(membership.organization, product_id)
        if product.stock_movements.exists():
            raise ResourceInUse
        product.stock_balance.delete()
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductPriceListView(ProductDetailView):
    http_method_names = ["get", "options"]

    @extend_schema(operation_id="product_prices_list", responses={200: product_price_list_response})
    def get(self, request, product_id):
        membership = require_product_permission(request.user, "products.view")
        product = self.get_object(membership.organization, product_id)
        return data_response(ProductPriceSerializer(product.prices.select_related("price_level").order_by("price_level__sort_order"), many=True).data)


class ProductDeactivateView(CatalogDeactivateView):
    model = Product