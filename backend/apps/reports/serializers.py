from rest_framework import serializers


class DashboardMetricSerializer(serializers.Serializer):
    sales_order_count = serializers.IntegerField(read_only=True)
    sales_amount = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    gross_profit = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
        read_only=True,
    )


class DashboardSerializer(serializers.Serializer):
    today = DashboardMetricSerializer(read_only=True)
    week = DashboardMetricSerializer(read_only=True)
    month = DashboardMetricSerializer(read_only=True)
    last_month = DashboardMetricSerializer(read_only=True)


class SalesReportSerializer(serializers.Serializer):
    sales_order_count = serializers.IntegerField(read_only=True)
    sales_quantity = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)
    sales_amount = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    sales_return_quantity = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)
    sales_return_amount = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    net_sales_quantity = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)
    net_sales_amount = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    sales_cost = serializers.DecimalField(max_digits=18, decimal_places=6, read_only=True)
    sales_return_cost = serializers.DecimalField(max_digits=18, decimal_places=6, read_only=True)
    net_sales_cost = serializers.DecimalField(max_digits=18, decimal_places=6, read_only=True)
    gross_profit = serializers.DecimalField(max_digits=18, decimal_places=6, read_only=True)


class PurchaseReportSerializer(serializers.Serializer):
    purchase_count = serializers.IntegerField(read_only=True)
    purchase_quantity = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)
    purchase_amount = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    purchase_return_quantity = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)
    purchase_return_amount = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    net_purchase_quantity = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)
    net_purchase_amount = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)


class InventoryReportSerializer(serializers.Serializer):
    product_count = serializers.IntegerField(read_only=True)
    in_stock_product_count = serializers.IntegerField(read_only=True)
    out_of_stock_product_count = serializers.IntegerField(read_only=True)
    total_quantity = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)
    total_amount = serializers.DecimalField(max_digits=38, decimal_places=6, read_only=True)