from rest_framework import serializers

from .models import StockBalance, StockMovement


class StockBalanceSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source="product.id")
    product_name = serializers.CharField(source="product.name")
    unit_name = serializers.CharField(source="product.unit.name")

    class Meta:
        model = StockBalance
        fields = ["id", "product_id", "product_name", "unit_name", "quantity", "updated_at"]


class StockMovementSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source="product.id")
    product_name = serializers.CharField(source="product.name")
    unit_name = serializers.CharField(source="product.unit.name")
    operator_name = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "product_id",
            "product_name",
            "unit_name",
            "movement_type",
            "quantity_delta",
            "source_type",
            "source_id",
            "occurred_at",
            "operator_name",
            "remark",
        ]

    def get_operator_name(self, obj: StockMovement) -> str:
        return obj.operator_user.display_name or obj.operator_user.username