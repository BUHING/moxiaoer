from decimal import Decimal

from rest_framework import serializers

from .models import LabelTemplate


class LabelTemplateWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    width_mm = serializers.DecimalField(max_digits=7, decimal_places=2, min_value=Decimal("0.01"))
    height_mm = serializers.DecimalField(max_digits=7, decimal_places=2, min_value=Decimal("0.01"))
    orientation = serializers.ChoiceField(choices=LabelTemplate.Orientation.choices)
    template = serializers.JSONField()
    is_active = serializers.BooleanField(required=False)

    def validate_template(self, value):
        if not isinstance(value, dict) or not isinstance(value.get("elements"), list):
            raise serializers.ValidationError("Template must be an object containing an elements array.")
        if len(value["elements"]) > 100:
            raise serializers.ValidationError("A label template can contain at most 100 elements.")
        return value


class LabelTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabelTemplate
        fields = ["id", "name", "width_mm", "height_mm", "orientation", "template", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]