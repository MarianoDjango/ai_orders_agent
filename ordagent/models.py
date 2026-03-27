from django.db import models

class Business(models.Model):
    name = models.CharField(max_length=200)
    whatsapp_phone_id = models.CharField(max_length=100, unique=True)
    whatsapp_token = models.CharField(max_length=500)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Businesses"


class Product(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.business.name} — {self.name}"

    class Meta:
        verbose_name_plural = "Products"


class Alias(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='aliases')
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name} → {self.product.name}"

    class Meta:
        verbose_name_plural = "Aliases"


class Order(models.Model):

    STATUSES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='orders')
    customer_phone = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='pending')

    def __str__(self):
        return f"Order #{self.id} — {self.customer_phone} — {self.status}"

    class Meta:
        verbose_name_plural = "Orders"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    class Meta:
        verbose_name_plural = "Order Items"


class ActiveConversation(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='conversations')
    customer_phone = models.CharField(max_length=50)
    preliminary_order = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business.name} — {self.customer_phone}"

    class Meta:
        verbose_name_plural = "Active Conversations"
        unique_together = ['business', 'customer_phone']