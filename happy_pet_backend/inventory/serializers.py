from rest_framework import serializers
from .models import Product, ProductVariant

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'price', 'stock_quantity', 'supplier_sku']

class ProductSerializer(serializers.ModelSerializer):
    # This automatically nests the variants inside the product JSON object
    variants = ProductVariantSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'category_name', 'variants', 'created_at']