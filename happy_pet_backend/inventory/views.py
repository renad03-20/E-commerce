from rest_framework.decorators import api_view, permission_classes
from .tasks import fulfill_order_with_supplier
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Category
from .models import Product
from .serializers import ProductSerializer
from .models import Order, OrderItem
from decimal import Decimal
import stripe
from django.conf import settings



stripe.api_key = settings.STRIPE_SECRET_KEY


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
    
@api_view(['POST'])
@permission_classes([AllowAny])
def process_checkout(request):
    data = request.data
    items = data.get('items', [])
    
    if not items:
        return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Start the order in our database
    order = Order.objects.create(
        customer_email=data.get('customer_email'),
        shipping_address=data.get('shipping_address'),
        status='pending'
    )

    calculated_total = Decimal('0.00')

    for item in items:
        price = Decimal(str(item.get('variants', [{}])[0].get('price', '0.00')))
        qty = int(item.get('quantity', 1))
        
        OrderItem.objects.create(
            order=order,
            product_title=item.get('title'),
            supplier_sku=item.get('variants', [{}])[0].get('supplier_sku', 'UNKNOWN'),
            quantity=qty,
            price_at_time=price
        )
        calculated_total += (price * qty)

    order.total_amount = calculated_total
    order.save()

    try:
        # 2. Stripe expects amounts in cents (integers)
        amount_in_cents = int(calculated_total * 100)
        
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency="usd",
            metadata={
                "order_id": order.id,
                "customer_email": order.customer_email
            }
        )

        fulfill_order_with_supplier.delay(order.id)
        
        # 3. Return the client_secret so React can finalize the payment
        return Response({
            "clientSecret": intent.client_secret,
            "order_id": order.id
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)