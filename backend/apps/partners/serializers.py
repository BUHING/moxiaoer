from rest_framework import serializers

from .models import Customer, Supplier


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "contact_name", "phone", "remark", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CustomerWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    contact_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    remark = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if self.instance is None and "name" not in attrs:
            raise serializers.ValidationError({"name": ["此字段为必填项。"]})
        return attrs


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "contact_name",
            "contact_address",
            "phone",
            "remark",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SupplierWriteSerializer(CustomerWriteSerializer):
    contact_address = serializers.CharField(max_length=255, required=False, allow_blank=True)