from rest_framework import serializers

from apps.partners.models import PriceLevel

from .models import AttributeOption, Product, ProductAttribute, ProductPrice, ProductSpecificationValue, Specification, Unit


class CatalogSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["id", "name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class UnitSerializer(CatalogSerializer):
    class Meta(CatalogSerializer.Meta):
        model = Unit


class CatalogWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if self.instance is None and "name" not in attrs:
            raise serializers.ValidationError({"name": ["此字段为必填项。"]})
        return attrs


class UnitWriteSerializer(CatalogWriteSerializer):
    pass


class SpecificationSerializer(CatalogSerializer):
    class Meta(CatalogSerializer.Meta):
        model = Specification


class SpecificationWriteSerializer(CatalogWriteSerializer):
    pass


class AttributeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeOption
        fields = ["id", "value", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class AttributeOptionWriteSerializer(serializers.Serializer):
    value = serializers.CharField(max_length=100, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if self.instance is None and "value" not in attrs:
            raise serializers.ValidationError({"value": ["此字段为必填项。"]})
        return attrs


class ProductAttributeSerializer(CatalogSerializer):
    options = AttributeOptionSerializer(many=True, read_only=True)

    class Meta(CatalogSerializer.Meta):
        model = ProductAttribute
        fields = ["id", "name", "input_type", "is_active", "options", "created_at", "updated_at"]
        read_only_fields = ["id", "options", "created_at", "updated_at"]


class ProductAttributeWriteSerializer(CatalogWriteSerializer):
    input_type = serializers.ChoiceField(choices=ProductAttribute.InputType.choices, required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance is None and "input_type" not in attrs:
            raise serializers.ValidationError({"input_type": ["此字段为必填项。"]})
        return attrs


class PriceLevelSerializer(CatalogSerializer):
    class Meta(CatalogSerializer.Meta):
        model = PriceLevel
        fields = ["id", "name", "sort_order", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PriceLevelWriteSerializer(CatalogWriteSerializer):
    sort_order = serializers.IntegerField(min_value=0, required=False)


class ProductSpecificationValueInputSerializer(serializers.Serializer):
    specification_id = serializers.UUIDField()
    value = serializers.CharField(max_length=100)


class ProductAttributeValueInputSerializer(serializers.Serializer):
    attribute_id = serializers.UUIDField()
    text_value = serializers.CharField(max_length=500, required=False, allow_blank=False)
    option_id = serializers.UUIDField(required=False)


class ProductPriceInputSerializer(serializers.Serializer):
    price_level_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0)


class ProductWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False)
    unit_id = serializers.UUIDField(required=False)
    supplier_id = serializers.UUIDField(required=False, allow_null=True)
    purchase_price = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0, required=False)
    specification = serializers.CharField(max_length=100, required=False, allow_blank=True)
    remark = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    specification_values = ProductSpecificationValueInputSerializer(many=True, required=False)
    attribute_values = ProductAttributeValueInputSerializer(many=True, required=False)
    prices = ProductPriceInputSerializer(many=True, required=False)
    initial_quantity = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        min_value=0,
        required=False,
        write_only=True,
    )

    def validate(self, attrs):
        if self.instance is None and ("name" not in attrs or "unit_id" not in attrs):
            raise serializers.ValidationError("商品名称和单位为必填项。")
        if self.instance is not None and "initial_quantity" in attrs:
            raise serializers.ValidationError({"initial_quantity": ["初始库存仅可在新建商品时填写。"]})
        return attrs


class ProductSpecificationValueSerializer(serializers.ModelSerializer):
    specification_id = serializers.UUIDField(source="specification.id")
    specification_name = serializers.CharField(source="specification.name")

    class Meta:
        model = ProductSpecificationValue
        fields = ["specification_id", "specification_name", "value"]


class ProductAttributeValueSerializer(serializers.Serializer):
    attribute_id = serializers.UUIDField(source="attribute.id")
    attribute_name = serializers.CharField(source="attribute.name")
    input_type = serializers.CharField(source="attribute.input_type")
    text_value = serializers.CharField(allow_null=True)
    option_id = serializers.UUIDField(source="option.id", allow_null=True)
    option_value = serializers.CharField(source="option.value", allow_null=True)


class ProductPriceSerializer(serializers.ModelSerializer):
    price_level_id = serializers.UUIDField(source="price_level.id")
    price_level_name = serializers.CharField(source="price_level.name")

    class Meta:
        model = ProductPrice
        fields = ["price_level_id", "price_level_name", "amount"]


class ProductSerializer(serializers.ModelSerializer):
    unit_id = serializers.UUIDField(source="unit.id")
    unit_name = serializers.CharField(source="unit.name")
    supplier_id = serializers.UUIDField(source="supplier.id", allow_null=True)
    supplier_name = serializers.CharField(source="supplier.name", allow_null=True)
    specification_values = ProductSpecificationValueSerializer(many=True, read_only=True)
    attribute_values = ProductAttributeValueSerializer(many=True, read_only=True)
    prices = ProductPriceSerializer(many=True, read_only=True)
    stock_quantity = serializers.DecimalField(source="stock_balance.quantity", max_digits=18, decimal_places=4)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "unit_id",
            "unit_name",
            "supplier_id",
            "supplier_name",
            "purchase_price",
            "specification",
            "remark",
            "is_active",
            "specification_values",
            "attribute_values",
            "prices",
            "stock_quantity",
            "created_at",
            "updated_at",
        ]