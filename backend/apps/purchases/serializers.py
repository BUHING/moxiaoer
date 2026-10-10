from decimal import Decimal

from rest_framework import serializers

from .models import Purchase, PurchaseItem, PurchaseReturn, PurchaseReturnItem


class PurchaseItemInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("0.0001"))
    unit_price = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0, required=False)


class PurchaseReturnItemInputSerializer(PurchaseItemInputSerializer):
    purchase_item_id = serializers.UUIDField(required=False, allow_null=True)


class PurchaseDocumentWriteSerializer(serializers.Serializer):
    supplier_id = serializers.UUIDField(required=False, allow_null=True)
    occurred_on = serializers.DateField(required=False)
    remark = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    items = PurchaseItemInputSerializer(many=True, required=False)

    def validate(self, attrs):
        if self.instance is None:
            missing_fields = {
                field: ["此字段为必填项。"]
                for field in ("occurred_on", "items")
                if field not in attrs
            }
            if missing_fields:
                raise serializers.ValidationError(missing_fields)
        if "items" in attrs and not attrs["items"]:
            raise serializers.ValidationError({"items": ["请至少添加一条商品明细。"]})
        return attrs


class PurchaseReturnWriteSerializer(PurchaseDocumentWriteSerializer):
    purchase_id = serializers.UUIDField(required=False, allow_null=True)
    items = PurchaseReturnItemInputSerializer(many=True, required=False)

class PurchaseDocumentItemSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source="product.id")

    class Meta:
        fields = [
            "id",
            "line_no",
            "product_id",
            "product_name_snapshot",
            "unit_name_snapshot",
            "quantity",
            "unit_price",
            "line_amount",
        ]
        read_only_fields = fields


class PurchaseItemSerializer(PurchaseDocumentItemSerializer):
    class Meta(PurchaseDocumentItemSerializer.Meta):
        model = PurchaseItem


class PurchaseReturnItemSerializer(PurchaseDocumentItemSerializer):
    purchase_item_id = serializers.UUIDField(source="purchase_item.id", allow_null=True)

    class Meta(PurchaseDocumentItemSerializer.Meta):
        model = PurchaseReturnItem
        fields = [*PurchaseDocumentItemSerializer.Meta.fields, "purchase_item_id"]


class PurchaseDocumentSerializer(serializers.ModelSerializer):
    supplier_id = serializers.UUIDField(source="supplier.id", allow_null=True)
    supplier_name = serializers.CharField(source="supplier.name", allow_null=True, default=None)
    completed_by_user_id = serializers.UUIDField(source="completed_by_user.id", allow_null=True)

    class Meta:
        fields = [
            "id",
            "document_no",
            "supplier_id",
            "supplier_name",
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


class PurchaseSerializer(PurchaseDocumentSerializer):
    items = PurchaseItemSerializer(many=True, read_only=True)

    class Meta(PurchaseDocumentSerializer.Meta):
        model = Purchase
        fields = [*PurchaseDocumentSerializer.Meta.fields, "items"]


class PurchaseReturnSerializer(PurchaseDocumentSerializer):
    purchase_id = serializers.UUIDField(source="purchase.id", allow_null=True)
    purchase_no = serializers.CharField(source="purchase.document_no", allow_null=True, default=None)
    items = PurchaseReturnItemSerializer(many=True, read_only=True)

    class Meta(PurchaseDocumentSerializer.Meta):
        model = PurchaseReturn
        fields = [*PurchaseDocumentSerializer.Meta.fields, "purchase_id", "purchase_no", "items"]