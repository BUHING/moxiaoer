from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Membership, PermissionRequest, ShopProfile, User
from .services import MANAGEABLE_PERMISSION_CODES, effective_permissions


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_username(self, username: str) -> str:
        if get_user_model().objects.filter(username=username).exists():
            raise serializers.ValidationError("用户名已被使用")
        return username


class TokenLoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs[self.username_field]
        user = get_user_model().objects.filter(username=username).first()
        if user is None:
            raise serializers.ValidationError({self.username_field: ["用户不存在"]})
        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError({"password": ["密码错误"]})
        if not user.is_active:
            raise serializers.ValidationError({self.username_field: ["账号已停用"]})
        return super().validate(attrs)


class TokenRefreshInputSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)


class TokenAccessSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)


class EmployeeCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    display_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class EmployeeUpdateSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=150, required=False)
    is_active = serializers.BooleanField(required=False)
    permission_codes = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(MANAGEABLE_PERMISSION_CODES)),
        required=False,
    )


class EmployeeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    display_name = serializers.CharField(source="user.display_name", read_only=True)
    last_login = serializers.DateTimeField(source="user.last_login", read_only=True)
    permission_codes = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = ["id", "username", "display_name", "is_active", "last_login", "permission_codes", "created_at"]

    def get_permission_codes(self, membership: Membership) -> list[str]:
        return sorted(membership.permission_grants.values_list("permission_code", flat=True))


class CurrentUserSerializer(serializers.ModelSerializer):
    organization_id = serializers.SerializerMethodField()
    organization_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "display_name", "organization_id", "organization_name", "role", "permissions"]

    def get_organization_id(self, user: User):
        return user.membership.organization_id

    def get_organization_name(self, user: User):
        return user.membership.organization.name

    def get_role(self, user: User):
        return user.membership.role

    def get_permissions(self, user: User) -> list[str]:
        return sorted(effective_permissions(user.membership))


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class PermissionRequestCreateSerializer(serializers.Serializer):
    permission_code = serializers.ChoiceField(choices=sorted(MANAGEABLE_PERMISSION_CODES))


class PermissionRequestSerializer(serializers.ModelSerializer):
    employee_id = serializers.UUIDField(source="membership.user_id", read_only=True)
    employee_name = serializers.CharField(source="membership.user.display_name", read_only=True)

    class Meta:
        model = PermissionRequest
        fields = [
            "id",
            "employee_id",
            "employee_name",
            "permission_code",
            "status",
            "reviewed_at",
            "created_at",
        ]


class ShopProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopProfile
        fields = ["shop_name", "remark"]