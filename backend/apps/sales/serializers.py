from decimal import Decimal

from rest_framework import serializers

from .models import SalesOrder, SalesOrderItem, SalesReturn, SalesReturnItem


class SalesItemInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("0.0001"))
    unit_price = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0)


class SalesReturnItemInputSerializer(SalesItemInputSerializer):
    sales_order_item_id = serializers.UUIDField()


class SalesDocumentWriteSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField(required=False, allow_null=True)
    occurred_on = serializers.DateField(required=False)
    remark = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    items = SalesItemInputSerializer(many=True, required=False)

    def validate(self, attrs):
        if self.instance is None:
            missing_fields = {field: ["此字段为必填项。"] for field in ("occurred_on", "items") if field not in attrs}
            if missing_fields:
                raise serializers.ValidationError(missing_fields)
        if "items" in attrs and not attrs["items"]:
            raise serializers.ValidationError({"items": ["请至少添加一条商品明细。"]})
        return attrs


class SalesReturnWriteSerializer(SalesDocumentWriteSerializer):
    sales_order_id = serializers.UUIDField(required=False)
    items = SalesReturnItemInputSerializer(many=True, required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance is None and "sales_order_id" not in attrs:
            raise serializers.ValidationError({"sales_order_id": ["此字段为必填项。"]})
        return attrs


class SalesDocumentItemSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source="product.id")
    price_level_id = serializers.UUIDField(source="price_level.id", allow_null=True)

    class Meta:
        fields = [
            "id",
            "line_no",
            "product_id",
            "product_name_snapshot",
            "unit_name_snapshot",
            "price_level_id",
            "quantity",
            "unit_price",
            "line_amount",
            "unit_cost_snapshot",
            "cost_amount",
        ]
        read_only_fields = fields


class SalesOrderItemSerializer(SalesDocumentItemSerializer):
    class Meta(SalesDocumentItemSerializer.Meta):
        model = SalesOrderItem


class SalesReturnItemSerializer(SalesDocumentItemSerializer):
    sales_order_item_id = serializers.UUIDField(source="sales_order_item.id")

    class Meta(SalesDocumentItemSerializer.Meta):
        model = SalesReturnItem
        fields = [*SalesDocumentItemSerializer.Meta.fields, "sales_order_item_id"]


class SalesDocumentSerializer(serializers.ModelSerializer):
    customer_id = serializers.UUIDField(source="customer.id", allow_null=True)
    customer_name = serializers.CharField(source="customer.name", allow_null=True, default=None)
    completed_by_user_id = serializers.UUIDField(source="completed_by_user.id", allow_null=True)

    class Meta:
        fields = [
            "id",
            "document_no",
            "customer_id",
            "customer_name",
            "status",
            "occurred_on",
            "total_amount",
            "remark",
            "completed_by_user_id",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class SalesOrderSerializer(SalesDocumentSerializer):
    items = SalesOrderItemSerializer(many=True, read_only=True)

    class Meta(SalesDocumentSerializer.Meta):
        model = SalesOrder
        fields = [*SalesDocumentSerializer.Meta.fields, "items"]


class SalesReturnSerializer(SalesDocumentSerializer):
    sales_order_id = serializers.UUIDField(source="sales_order.id")
    sales_order_no = serializers.CharField(source="sales_order.document_no")
    items = SalesReturnItemSerializer(many=True, read_only=True)

    class Meta(SalesDocumentSerializer.Meta):
        model = SalesReturn
        fields = [*SalesDocumentSerializer.Meta.fields, "sales_order_id", "sales_order_no", "items"]