from django.db import models


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Payment'),
        ('processing', 'Sent to Supplier'),
        ('shipped', 'Shipped to Customer'),
    )
    customer_email = models.EmailField()
    shipping_address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.customer_email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_title = models.CharField(max_length=255) # We save the text in case the original product gets deleted
    supplier_sku = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_title}"

