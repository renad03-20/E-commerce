# inventory/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Category, Order, OrderItem
from .serializers import ProductSerializer
from decimal import Decimal
import stripe
from django.conf import settings
import logging
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
def import_dropship_product(request):
    data = request.data
    
    try:
        category, _ = Category.objects.get_or_create(name="Uncategorized", slug="uncategorized")
        
        product = Product.objects.create(
            title=data.get('title'),
            description=f"Imported from AliExpress. Original link: {data.get('source_url')}",
            category=category
        )

        return Response(
            {"message": "Product imported successfully", "product_id": product.id}, 
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([AllowAny])
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

    # 1. Create the order
    order = Order.objects.create(
        customer_email=data.get('customer_email'),
        shipping_address=data.get('shipping_address'),
        status='pending',
        payment_status='pending'
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
        # 2. Create Stripe PaymentIntent
        amount_in_cents = int(calculated_total * 100)
        
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency="usd",
            metadata={
                "order_id": str(order.id),
                "customer_email": order.customer_email
            }
        )
        
        # 3. Save the PaymentIntent ID to the order
        order.stripe_payment_intent = intent.id
        order.save()
        
        # 4. Return the client_secret to the frontend
        return Response({
            "clientSecret": intent.client_secret,
            "order_id": str(order.id)
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        # Delete the order if Stripe fails
        order.delete()
        logger.error(f"Stripe error: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.payment_status = 'paid'
                order.status = 'processing'
                order.save()
                
                # NOW trigger the Celery task after payment is confirmed
                from .tasks import fulfill_order_with_supplier
                fulfill_order_with_supplier.delay(order_id)
                
                logger.info(f" Payment succeeded for order {order_id}")
                
            except Order.DoesNotExist:
                logger.error(f" Order {order_id} not found")
                
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.payment_status = 'failed'
                order.save()
                logger.info(f" Payment failed for order {order_id}")
            except Order.DoesNotExist:
                pass
    
    return JsonResponse({'status': 'success'})