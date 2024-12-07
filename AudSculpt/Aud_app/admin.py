from django.contrib import admin
from .models import CustomUser, Image,Coupons,Product
# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Image)
admin.site.register(Coupons)
admin.site.register(Product)




