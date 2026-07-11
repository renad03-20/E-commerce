from django.db import models
import uuid
class Supplier(models.Model):
    name = models.CharField(max_length=255)
    api_endpoint = models.URLField(blank=True, null=True)
    contact_email = models.EmailField()
    
    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100) # e.g., "Cats", "Dogs", "Aquatic"
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True) # For subcategories like Cats -> Toys

    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=255) # e.g., "Interactive Laser Pointer"
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    supplier_sku = models.CharField(max_length=100, unique=True) # Crucial for automated dropshipping fulfillment
    name = models.CharField(max_length=100) # e.g., "Red - Small"
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0) # Will be synced via Celery tasks
    
    def __str__(self):
        return f"{self.product.title} - {self.name}"


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

