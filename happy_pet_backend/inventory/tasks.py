# inventory/tasks.py
import requests
from celery import shared_task
from django.conf import settings
from .models import Order

@shared_task
def fulfill_order_with_supplier(order_id):
    """
    Background task to automatically send paid orders to the AliExpress API.
    """
    try:
        # 1. Fetch the exact order and its items from the database
        order = Order.objects.prefetch_related('items').get(id=order_id)
        
        # 2. Format the payload for the AliExpress Open Platform API
        # (This structure will depend on the exact endpoints in their documentation)
        ali_express_payload = {
            "shipping_address": order.shipping_address,
            "customer_email": order.customer_email,
            "items": []
        }
        
        for item in order.items.all():
            ali_express_payload["items"].append({
                "sku_id": item.supplier_sku,
                "quantity": item.quantity
            })

        # 3. Fire off the request to the Supplier
        headers = {
            "Authorization": f"Bearer {getattr(settings, 'ALIEXPRESS_API_KEY', 'YOUR_KEY_HERE')}",
            "Content-Type": "application/json"
        }
        
        # Using a mockup URL. Replace with real AliExpress dropship endpoint.
        response = requests.post(
            "https://api.aliexpress.com/v1/dropship/order/create", 
            json=ali_express_payload, 
            headers=headers
        )
        
        # 4. Handle the supplier's response
        if response.status_code == 200:
            order.status = 'processing'
            order.save()
            return f"Successfully fulfilled Order {order_id}"
        else:
            # If the supplier API fails (e.g., out of stock), we log it to handle manually
            return f"Failed to fulfill Order {order_id}. API Error: {response.text}"
            
    except Order.DoesNotExist:
        return f"Order {order_id} not found."
    except Exception as e:
        return f"Unexpected error on Order {order_id}: {str(e)}"