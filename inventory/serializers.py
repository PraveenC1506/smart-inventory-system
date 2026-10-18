
from decimal import Decimal

from rest_framework import serializers

from .models import Product, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Category name cannot be empty."
            )

        queryset = Category.objects.filter(name__iexact=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "A category with this name already exists."
            )

        return value


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    class Meta:
        model = Product
        fields = "__all__"

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Product name cannot be empty."
            )

        return value

    def validate_sku(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "SKU cannot be empty."
            )

        queryset = Product.objects.filter(sku__iexact=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "A product with this SKU already exists."
            )

        return value

    def validate_purchase_price(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError(
                "Purchase price cannot be negative."
            )

        return value

    def validate_selling_price(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError(
                "Selling price cannot be negative."
            )

        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Stock quantity cannot be negative."
            )

        return value

    def validate_reorder_level(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Reorder level cannot be negative."
            )

        return value
