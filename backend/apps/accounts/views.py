from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer

from .models import Membership, PermissionRequest, User
from .serializers import (
    CurrentUserSerializer,
    EmployeeCreateSerializer,
    EmployeeSerializer,
    EmployeeUpdateSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PermissionRequestCreateSerializer,
    PermissionRequestSerializer,
    RegisterSerializer,
    ShopProfileSerializer,
    TokenAccessSerializer,
    TokenLoginSerializer,
    TokenPairSerializer,
    TokenRefreshInputSerializer,
)
from .services import create_employee, grant_permission, register_boss, review_permission_request


current_user_response = inline_serializer("CurrentUserResponse", fields={"data": CurrentUserSerializer()})
employee_response = inline_serializer("EmployeeResponse", fields={"data": EmployeeSerializer()})
employee_list_response = inline_serializer(
    "EmployeeListResponse", fields={"data": EmployeeSerializer(many=True)}
)
permission_request_response = inline_serializer(
    "PermissionRequestResponse", fields={"data": PermissionRequestSerializer()}
)
permission_request_list_response = inline_serializer(
    "PermissionRequestListResponse", fields={"data": PermissionRequestSerializer(many=True)}
)
shop_profile_response = inline_serializer("ShopProfileResponse", fields={"data": ShopProfileSerializer()})
token_response = inline_serializer("TokenResponse", fields={"data": TokenPairSerializer()})
refresh_response = inline_serializer("RefreshResponse", fields={"data": TokenAccessSerializer()})


def data_response(data, status_code=status.HTTP_200_OK):
    return Response({"data": data}, status=status_code)


def get_membership(user) -> Membership:
    try:
        return user.membership
    except Membership.DoesNotExist as error:
        raise PermissionDenied("User has no active organization membership.") from error


def require_boss(user) -> Membership:
    membership = get_membership(user)
    if membership.role != Membership.Role.BOSS or not membership.is_active:
        raise PermissionDenied("Boss permission is required.")
    return membership


@extend_schema(request=RegisterSerializer, responses={201: current_user_response})
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = register_boss(**serializer.validated_data)
        return data_response(CurrentUserSerializer(membership.user).data, status.HTTP_201_CREATED)


@extend_schema(request=TokenLoginSerializer, responses={200: token_response})
class TokenView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = TokenLoginSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return data_response(response.data, response.status_code)


@extend_schema(request=TokenRefreshInputSerializer, responses={200: refresh_response})
class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return data_response(response.data, response.status_code)


@extend_schema(request=PasswordResetRequestSerializer, responses={204: None})
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for user in get_user_model().objects.filter(email__iexact=serializer.validated_data["email"], is_active=True):
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = settings.PASSWORD_RESET_URL.format(uid=uid, token=token)
            send_mail(
                subject="GrindBuddy 密码重置",
                message=f"请使用以下链接重置密码：{reset_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=PasswordResetConfirmSerializer, responses={204: None})
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user_id = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = get_user_model().objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            raise NotFound("密码重置链接无效或已过期。")
        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            raise NotFound("密码重置链接无效或已过期。")
        try:
            validate_password(serializer.validated_data["password"], user)
        except DjangoValidationError as error:
            raise ValidationError({"password": list(error.messages)}) from error
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(responses={200: current_user_response})
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        get_membership(request.user)
        return data_response(CurrentUserSerializer(request.user).data)


@extend_schema_view(
    get=extend_schema(operation_id="employees_list", responses={200: employee_list_response}),
    post=extend_schema(
        operation_id="employees_create", request=EmployeeCreateSerializer, responses={201: employee_response}
    ),
)
class EmployeeListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = require_boss(request.user)
        employees = Membership.objects.filter(
            organization=membership.organization,
            role=Membership.Role.EMPLOYEE,
        ).select_related("user").prefetch_related("permission_grants")
        return data_response(EmployeeSerializer(employees, many=True).data)

    def post(self, request):
        boss_membership = require_boss(request.user)
        serializer = EmployeeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = create_employee(boss_membership=boss_membership, **serializer.validated_data)
        return data_response(EmployeeSerializer(employee).data, status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        operation_id="employees_retrieve",
        parameters=[OpenApiParameter("user_id", type=str, location=OpenApiParameter.PATH)],
        responses={200: employee_response},
    ),
    patch=extend_schema(
        operation_id="employees_partial_update",
        parameters=[OpenApiParameter("user_id", type=str, location=OpenApiParameter.PATH)],
        request=EmployeeUpdateSerializer,
        responses={200: employee_response},
    ),
)
class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user, user_id):
        boss_membership = require_boss(user)
        return get_object_or_404(
            Membership.objects.select_related("user").prefetch_related("permission_grants"),
            organization=boss_membership.organization,
            user_id=user_id,
            role=Membership.Role.EMPLOYEE,
        )

    def get(self, request, user_id):
        return data_response(EmployeeSerializer(self.get_object(request.user, user_id)).data)

    def patch(self, request, user_id):
        employee = self.get_object(request.user, user_id)
        serializer = EmployeeUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if "display_name" in values:
            employee.user.display_name = values["display_name"]
            employee.user.save(update_fields=["display_name", "updated_at"])
        if "is_active" in values:
            employee.is_active = values["is_active"]
            employee.save(update_fields=["is_active", "updated_at"])
        for permission_code in values.get("permission_codes", []):
            grant_permission(
                employee_membership=employee,
                permission_code=permission_code,
                granted_by_user=request.user,
            )
        return data_response(EmployeeSerializer(self.get_object(request.user, user_id)).data)


@extend_schema_view(
    get=extend_schema(
        operation_id="permission_requests_list", responses={200: permission_request_list_response}
    ),
    post=extend_schema(
        operation_id="permission_requests_create",
        request=PermissionRequestCreateSerializer,
        responses={201: permission_request_response},
    ),
)
class PermissionRequestListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = get_membership(request.user)
        queryset = PermissionRequest.objects.select_related("membership__user")
        if membership.role == Membership.Role.BOSS:
            queryset = queryset.filter(membership__organization=membership.organization)
        else:
            queryset = queryset.filter(membership=membership)
        return data_response(PermissionRequestSerializer(queryset.order_by("-created_at"), many=True).data)

    def post(self, request):
        membership = get_membership(request.user)
        if membership.role != Membership.Role.EMPLOYEE or not membership.is_active:
            raise PermissionDenied("Only active employees can request permissions.")
        serializer = PermissionRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permission_request = PermissionRequest.objects.create(membership=membership, **serializer.validated_data)
        return data_response(PermissionRequestSerializer(permission_request).data, status.HTTP_201_CREATED)


@extend_schema(
    parameters=[OpenApiParameter("request_id", type=str, location=OpenApiParameter.PATH)],
    responses={200: permission_request_response},
)
class PermissionRequestReviewView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PermissionRequestSerializer

    approved = False

    def post(self, request, request_id):
        boss_membership = require_boss(request.user)
        try:
            permission_request = review_permission_request(
                request_id=request_id,
                organization=boss_membership.organization,
                reviewer=request.user,
                approved=self.approved,
            )
        except PermissionRequest.DoesNotExist as error:
            raise NotFound("Permission request was not found.") from error
        return data_response(PermissionRequestSerializer(permission_request).data)


class ApprovePermissionRequestView(PermissionRequestReviewView):
    approved = True

    @extend_schema(
        parameters=[OpenApiParameter("request_id", type=str, location=OpenApiParameter.PATH)],
        request=None,
        responses={200: permission_request_response},
    )
    def post(self, request, request_id):
        return super().post(request, request_id)


class RejectPermissionRequestView(PermissionRequestReviewView):
    approved = False

    @extend_schema(
        parameters=[OpenApiParameter("request_id", type=str, location=OpenApiParameter.PATH)],
        request=None,
        responses={200: permission_request_response},
    )
    def post(self, request, request_id):
        return super().post(request, request_id)


@extend_schema_view(
    get=extend_schema(operation_id="shop_profile_retrieve", responses={200: shop_profile_response}),
    put=extend_schema(
        operation_id="shop_profile_update", request=ShopProfileSerializer, responses={200: shop_profile_response}
    ),
)
class ShopProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = require_boss(request.user)
        return data_response(ShopProfileSerializer(membership.organization.shop_profile).data)

    def put(self, request):
        membership = require_boss(request.user)
        serializer = ShopProfileSerializer(membership.organization.shop_profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return data_response(serializer.data)