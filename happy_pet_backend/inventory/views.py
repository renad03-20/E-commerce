from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Category
from .models import Product
from .serializers import ProductSerializer

@api_view(['POST'])
# @permission_classes([IsAdminUser]) # Lock down so only you can access it
def import_dropship_product(request):
    data = request.data
    
    try:
        # Fallback to a general category or match it programmatically 
        category, _ = Category.objects.get_or_create(name="Uncategorized", slug="uncategorized")
        
        # Create the base product
        product = Product.objects.create(
            title=data.get('title'),
            description=f"Imported from AliExpress. Original link: {data.get('source_url')}",
            category=category
        )
        
        # In production, you would trigger a Celery background task here 
        # to download the image from data.get('image_url') and upload it to AWS S3.

        return Response(
            {"message": "Product imported successfully", "product_id": product.id}, 
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([AllowAny]) # Anyone visiting the site can view products
def public_product_list(request):
    products = Product.objects.filter(is_active=True).prefetch_related('variants')
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)