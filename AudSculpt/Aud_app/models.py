from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from calendar import month_abbr
# Create your models here.

class CustomUser(AbstractUser):
    age =models.IntegerField(null=True)
    gender = models.CharField(max_length=100,null=True)
    phone = models.CharField(max_length=100,null=True)
    altphone = models.CharField(max_length=100,null=True)
    dob = models.DateField(null=True, blank=True)

class UserImage(models.Model):
    image = models.ImageField(upload_to='media/',null=True)
    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE,related_name='userimage')

class Address(models.Model):
    houseno = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    landmark = models.CharField(max_length=100)
    pincode = models.CharField(max_length=100)
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name="address")

class State(models.Model):
    state = models.CharField(max_length=100)
    address = models.ForeignKey(Address,on_delete=models.CASCADE,related_name='state')


class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='media/')
    unlist = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='media/', blank=True, null=True)
    highlights = models.TextField()
    unlist = models.BooleanField(default=False)
    code = models.IntegerField(null=True)
    discount = models.IntegerField(null = True, blank = True, default = 0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')

class varients(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.IntegerField(null=True)
    stock = models.IntegerField(null = True, blank = True)
    variation = models.CharField(max_length=100,null=True)
    code = models.IntegerField(null=True)
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='varients')

class Image(models.Model):
    image = models.ImageField(upload_to='media/')
    code = models.IntegerField(null=True)
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='images')

    def __str__(self):
        return self.product.name    

class Brands(models.Model):
    name = models.CharField(max_length = 100)
    product = models.ForeignKey(Product,on_delete = models.CASCADE,related_name='Brands')


class cart(models.Model):
    quantity = models.IntegerField(default = 1)
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='usercart')
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name = 'carts')

class Coupons(models.Model):
    code = models.CharField(max_length =100)
    discount_price = models.IntegerField()
    starting_date = models.DateField()
    ending_date = models.DateField()
    count = models.IntegerField()

class Order(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    status = models.CharField(max_length=100)
    payment = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1)
    coupon_code = models.CharField(max_length=100,null=True, blank=True)
    coupon_price = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='userorder')
    address = models.ForeignKey(Address,on_delete=models.CASCADE,related_name='orderaddress')
    product = models.ManyToManyField(Product,related_name='orderproduct')


    class Meta:
        db_table = "Order"

    @classmethod
    def get_orders_count_today(cls):
        today = timezone.now().date()
        return cls.objects.filter(date=today, status='Ordered').count()

    @classmethod
    def get_cancelled_orders_count_today(cls):
        today = timezone.now().date()
        return cls.objects.filter(date=today, status='Cancelled').count()
    
    @classmethod
    def get_orders_count_monthly(cls):
        current_month = timezone.now().date().replace(day=1)
        next_month = (current_month + timezone.timedelta(days=32)).replace(day=1)
        monthly_counts = cls.objects.filter(date__gte=current_month, date__lt=next_month, status='Ordered') \
                                     .values('date__month') \
                                     .annotate(count=models.Count('id'))

        # Create a mapping between numeric months and their abbreviations
        month_mapping = {i: month_abbr[i] for i in range(1, 13)}

        # Initialize monthly data with 0 counts for all months
        monthly_data = {month_abbr[i]: 0 for i in range(1, 13)}

        # Update counts for existing months
        for entry in monthly_counts:
            month_name = month_mapping.get(entry['date__month'])
            if month_name:
                monthly_data[month_name] = entry['count']

        return monthly_data

    @classmethod
    def get_cancelled_orders_count_monthly(cls):
        current_month = timezone.now().date().replace(day=1)
        next_month = (current_month + timezone.timedelta(days=32)).replace(day=1)
        monthly_counts = cls.objects.filter(date__gte=current_month, date__lt=next_month, status='Cancelled') \
                                     .values('date__month') \
                                     .annotate(count=models.Count('id'))

        monthly_data = {entry['date__month']: entry['count'] for entry in monthly_counts}
        return monthly_data

class razor_pay(models.Model):
    razopay_order_id = models.CharField(max_length = 100,null=True, blank = True)
    razopay_payment_id = models.CharField(max_length = 100,null=True, blank = True)
    order = models.OneToOneField(Order, on_delete = models.CASCADE, related_name = 'razor_pay',null=True,blank=True)


class wallet_user(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2,default = 0)
    payment_type = models.CharField(max_length = 100,null = True)
    user = models.OneToOneField(CustomUser, on_delete = models.CASCADE, related_name = 'wallet',null = True)

class WalletHistory(models.Model):
    TRANSACTION_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES)
    date = models.DateTimeField(auto_now_add=True)