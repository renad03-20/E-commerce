from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Product, ProductVariant, Category, Order, OrderItem
from .serializers import ProductSerializer
from decimal import Decimal
import stripe
from django.conf import settings
import logging
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
@permission_classes([AllowAny])
def import_dropship_product(request):
    data = request.data
    
    try:
        category, _ = Category.objects.get_or_create(name="Uncategorized", slug="uncategorized")
        
        # 1. Create the base product
        product = Product.objects.create(
            title=data.get('title'),
            description=f"Imported from AliExpress. Original link: {data.get('source_url')}",
            category=category
        )

        # 2. Extract variants from the extension's request
        variants_data = data.get('variants', [])
        
        if variants_data and isinstance(variants_data, list):
            # Loop through and save all variants sent by the Chrome extension
            for var_data in variants_data:
                ProductVariant.objects.create(
                    product=product,
                    name=var_data.get('name', 'Default'),
                    supplier_sku=var_data.get('supplier_sku', f"AUTO-{product.id.hex[:8]}"),
                    price=var_data.get('price', 0.00),
                    stock_quantity=var_data.get('stock_quantity', 100)
                )
        else:
            # Fallback just in case the extension sends empty data
            ProductVariant.objects.create(
                product=product,
                name="Default",
                supplier_sku=f"AUTO-{product.id.hex[:8]}",
                price=data.get('price', 0.00),
                stock_quantity=100
            )

        return Response(
            {"message": f"Product imported with variants successfully", "product_id": product.id}, 
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

    try:
        for item in items:
            qty = int(item.get('quantity', 1))
            product_id = item.get('id') 
            
            # Look for the exact variant ID chosen on the frontend
            selected_variant_id = item.get('selectedVariantId') 
            
            product = Product.objects.get(id=product_id)
            
            # Securely fetch the specific variant from the database
            if selected_variant_id:
                variant = product.variants.get(id=selected_variant_id)
            else:
                variant = product.variants.first() # Fallback for old cart items
            
            if not variant:
                raise ValueError(f"Product {product.title} has no price configured.")

            db_price = variant.price
            db_sku = variant.supplier_sku
            
            # Append variant name to product title for better order history clarity
            OrderItem.objects.create(
                order=order,
                product_title=f"{product.title} ({variant.name})",
                supplier_sku=db_sku,
                quantity=qty,
                price_at_time=db_price
            )
            calculated_total += (db_price * qty)

        order.total_amount = calculated_total
        order.save()

        # 2. Create Stripe PaymentIntent using the secure calculated total
        amount_in_cents = int(calculated_total * 100)
        
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency="usd",
            metadata={
                "order_id": str(order.id),
                "customer_email": order.customer_email
            }
        )
        
        order.stripe_payment_intent = intent.id
        order.save()
        
        return Response({
            "clientSecret": intent.client_secret,
            "order_id": str(order.id)
        }, status=status.HTTP_201_CREATED)

    except Product.DoesNotExist:
        order.delete()
        return Response({"error": "One or more products in cart do not exist."}, status=status.HTTP_400_BAD_REQUEST)
    except ProductVariant.DoesNotExist:
        order.delete()
        return Response({"error": "Selected size/color does not exist."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        order.delete()
        logger.error(f"Stripe/Checkout error: {str(e)}")
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
    
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.payment_status = 'paid'
                order.status = 'processing'
                order.save()
                
                from .tasks import fulfill_order_with_supplier
                fulfill_order_with_supplier.delay(order_id)
                
                logger.info(f"Payment succeeded for order {order_id}")
                
            except Order.DoesNotExist:
                logger.error(f"Order {order_id} not found")
                
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        order_id = payment_intent['metadata'].get('order_id')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.payment_status = 'failed'
                order.save()
                logger.info(f"Payment failed for order {order_id}")
            except Order.DoesNotExist:
                pass
    
    return JsonResponse({'status': 'success'})