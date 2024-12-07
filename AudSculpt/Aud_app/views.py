from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.conf import settings
import random
from .models import Category, Product, Image, Address, State, varients, CustomUser,WalletHistory ,cart, UserImage, Order, Coupons,Brands, razor_pay, wallet_user
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.http import JsonResponse, HttpResponseBadRequest,HttpResponse
from django.shortcuts import redirect, get_object_or_404
import json
from decimal import Decimal
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.auth.hashers import check_password
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
import razorpay
from django.views.decorators.csrf import csrf_exempt
from datetime import date, timedelta
from django.db.models import Max, F, Min
from openpyxl import Workbook

def generate_otp():
    values = '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    
    for i in range(5):
        OTP = ''.join(random.choice(values) for _ in range(5))
    return OTP


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signin(request):

    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_home')
        return redirect('home') 
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate( request, username = email, password = password)

        if user:
            if user.is_superuser:
                login(request,user)
                return redirect('admin_home')
            else:
                login(request,user)
                return redirect('home')
            

        user_err = 'Invalid user details'
        return render(request,'logindd.html',{'user_err':user_err})
    
    return render(request,'logindd.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):

    if request.user.is_authenticated:
        user = CustomUser.objects.get(username = request.user.username)
        return render(request,'home.html',{'user':user})
    
    return redirect('signin')



def get_otp(email):

    o = generate_otp()
    print(o)
    if email == 'aksharaaruvi@gmail.com':
        send_mail('AudSculpt',f'Your OTP is {o} and I Love You',settings.EMAIL_HOST_USER,[email],fail_silently=False)
        return o
    try:
        send_mail('AudSculpt',f'Your OTP is {o}',settings.EMAIL_HOST_USER,[email],fail_silently=False)
        return o
    except Exception as e:
        print(e)
        return o


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup(request):

    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        
        auth_user = CustomUser.objects.filter(username = username).exists()
        auth_email = CustomUser.objects.filter(email = email).exists()

        if auth_user:
            user_err = 'username already used..!'
            return render(request,'signup.html',{'user_err':user_err})
        elif auth_email:
            user_err = 'email already used..!'
            return render(request,'signup.html',{'user_err':user_err})

        if password1 == password2:
            user = {
                'first_name' : firstname,
                'last_name' : lastname,
                'username' : username,
                'email' : email,
                'password':password1
            }           
            
            request.session['user'] = user
            O = get_otp(email)
            request.session['otp'] = O
                        
            return redirect('otp_entering')
        err = 'password must be same'
        return render(request,'signup.html',{'pass_err':err})      

    return render(request,'signup.html')

def otp_entering(request):

    stored_otp = request.session.get('otp',None)
    stored_user = request.session.get('user',None)
    
    if stored_user is None:
        return redirect('signup')
    
    
    if request.method == 'POST':

        
        entered_otp = request.POST.get('entered_otp')


        if str(stored_otp) == str(entered_otp):
            user = CustomUser.objects.create_user(
            first_name = stored_user['first_name'],
            last_name = stored_user['last_name'],
            username = stored_user['username'],
            email = stored_user['email'],
            password =stored_user['password']
            )
            return redirect('signin')
    
        otp_err = 'Entered otp is incorrect'
        return render(request, 'otp_entering.html', {'otp_err': otp_err})

    return render(request,'otp_entering.html')


def otp_sending(request):

    if request.method == 'POST':
        email = request.POST.get('email')
        users = CustomUser.objects.filter(email = email).exists()
        err = None
       
        if users:
            O = get_otp(email)
            request.session['otp'] = O
            request.session['email_from_otp_sending'] = email
            return redirect('otp_entering2')
        else:
            err = 'Invalid Email Id'
            return render(request,'otp_sending.html',{'err':err})

    return render(request,'otp_sending.html')

def password_update(request):

    user_confirm2 = request.session.get('user_confirm')
    email = request.session.get('email_from_otp_sending')


    if user_confirm2 == 'user_confirmed':

        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')

            user = CustomUser.objects.get(email = email)

            if user:
                if password1 == password2:
                    user.set_password(password1)
                    user.save()
                    return redirect('signin')
                err = 'password must be same'
                return render(request,'change_password',{'err':err})

        return render(request,'password_update.html')
    return redirect('otp_entering2')

def otp_entering2(request):

    o = request.session.get('otp')
    email = request.session.get('email_from_otp_sending')
    if request.method == 'POST':
        
        entered_otp = request.POST.get('entered_otp')

        if str(entered_otp) == str(o):
            request.session['user_confirm'] = "user_confirmed"
            return redirect('password_update')
        else:
            err = 'Invalid otp'
            return render(request,'otp_entering2.html',{'err':err})
      

    return render(request,'otp_entering2.html')

from django.db.models import Count

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_home(request):

    if request.user.is_authenticated:
        if request.user.is_superuser:

            orders_count_today = Order.get_orders_count_today()
            cancelled_orders_count_today = Order.get_cancelled_orders_count_today()
            monthly_orders_count = Order.get_orders_count_monthly()
            monthly_cancelled_orders_count = Order.get_cancelled_orders_count_monthly()
            user = CustomUser.objects.get(username = request.user.username)

           
            context = {"OCT" : orders_count_today , "COCT" :cancelled_orders_count_today,'monthly_orders_count': monthly_orders_count,
        'monthly_cancelled_orders_count': monthly_cancelled_orders_count,'user':user
    }

            return render(request, 'adminhome.html', context)
               
        return redirect('home')

    return redirect('signin')


def logg(request):
    return render(request,'login.html')


def admin_users(request):
    
    if request.user.is_authenticated:
        if request.user.is_superuser:
            if request.method == "POST":
                value = request.POST.get('search')
                users = CustomUser.objects.filter(first_name__icontains = value ,is_superuser = False)

                return render(request, 'admin_users.html',{'users':users})

            users = CustomUser.objects.filter(is_superuser = False)
            return render(request, 'admin_users.html',{'users':users})
        return redirect('signin')
        
    return redirect('signin')


def admin_orders(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:

            orders = Order.objects.all().order_by('-id')
           
            if 'search' in request.POST:
                value = request.POST.get('search')

                user = None
                product = None
                try:
                    user = CustomUser.objects.get(username__icontains = value)
                except CustomUser.DoesNotExist:
                    product = Product.objects.filter(name__icontains = value)
                
                if user:
                    orders = Order.objects.filter(user = user)
                else:
                    for product in product:
                        orders = Order.objects.filter(product = product.id)

                return render(request,'admin_orders.html',{'orders':orders})

            elif request.method == 'POST':
                selected_status = request.POST.get('orderStatus')
                pk = request.GET.get('pk')
                ord = Order.objects.get(id = pk)
                ord.status = selected_status
                ord.save()
                if selected_status == 'Returned':
                    try:
                        wallet = wallet_user.objects.get(user = request.user)
                        wallet.amount += ord.price
                        wallet.save()

                        obj = WalletHistory(amount=ord.price,transaction_type='credit',user=request.user)
                        obj.save()
                    except:
                        wallet = wallet_user.objects.create(
                            amount = ord.price,
                            payment_type = ord.payment,
                            user = request.user
                        )
                        obj = WalletHistory(amount=ord.price,transaction_type='credit',user=request.user)
                        obj.save()

                
                return redirect('admin_orders')


            return render(request,'admin_orders.html',{'orders':orders})
        return redirect('signin')
    return redirect('signin')


def admin_offers(request):
    if request.user.is_authenticated:
        if User.is_superuser:
            
            categories = Category.objects.filter(unlist = True)
            products = Product.objects.filter(category__unlist = True , unlist = False)

            return render(request,'admin_offers.html',{'categories':categories,'products':products})

def admin_offerpage(request):
    if request.user.is_authenticated:

        if User.is_superuser:
            pk = request.GET.get('pk')
            obj = None
            obj2 = None

            try:
                obj = Category.objects.get(id = pk)
            except:
                obj2 = Product.objects.get(id = pk)

            if request.method == 'POST':
                if obj:
                    discount = request.POST.get('discount')
                    if discount:
                        for products in obj.products.all():
                            products.discount = discount
                            products.save()
                            for variants in products.varients.all():
                                a = int(discount)
                                if a != 0:
                                    variants.discount_price = variants.price - (variants.price/a)
                                    variants.save()
                                else:
                                    variants.discount_price = None
                                    variants.save()

                        return redirect('admin_offers')
                elif obj2:
                    discount = request.POST.get('discount')
                    if discount:
                        obj2.discount = discount
                        obj2.save()
                    for variant in obj2.varients.all():
                        a = int(discount)
                        if a != 0:                        
                            variant.discount_price = variant.price - (variant.price / a)
                            variant.save()
                        else:
                            variant.discount_price = None
                            variant.save()
                    return redirect('admin_offers')

            return render(request,'admin_offerpage.html',{'obj':obj,'obj2':obj2})


def admin_category(request):
    
    if request.user.is_authenticated:
        if request.user.is_superuser:
            users = Category.objects.all()      

            if 'search' in request.POST:
                value = request.POST.get('search')
                users = Category.objects.filter(name__icontains = value)
                err2 = ''
                if not users:
                    err2 = 'This category name is not available'
                return render(request,'admin_category.html',{'users':users,'err2':err2})


            elif request.method == 'POST':

                
                image = request.FILES.get('image')
                name = request.POST.get('name')

                if image and name:
                    if Category.objects.filter(name = name).exists():
                        err = 'Name Already used...!'
                        return render(request,'admin_category.html',{'users':users,'err':err})
                
                    else:
                        category = Category.objects.create(
                            image = image,
                            name = name
                        )
                        category.save()
                        return redirect('admin_category')
                
            return render(request,'admin_category.html',{'users':users})
        
        return redirect('signin')
    return redirect('signin')
    
    

def admin_products(request):
    
    if request.user.is_authenticated:
        if request.user.is_superuser:

            if request.method == "POST":
                value = request.POST.get('search')
                users = Category.objects.filter(unlist = True , name__icontains = value)
                return render(request,'admin_products.html',{'users':users})


            users = Category.objects.filter(unlist = True)

            
            return render(request,'admin_products.html',{'users':users})
        return redirect('signin')
    return redirect('signin')
    
    

def admin_products_list(request):

    if request.user.is_authenticated:
        if request.user.is_superuser:

            imageid = request.GET.get('image_id')
            products = Product.objects.filter(category__id=imageid)
            variant = varients.objects.all

            if 'search' in request.POST:
                value = request.POST.get('search')
                products = Product.objects.filter(name__icontains = value , category__id=imageid)
          

            elif request.method == 'POST':
                name = request.POST.get('name')
                price = request.POST.get('price')
                image1 = request.FILES.getlist('image1')
                stock = request.POST.get('stock')
                brand = request.POST.get('brand')
                description = request.POST.get('description')
                highlights = request.POST.get('highlights')
                code = request.POST.get('code')
                color = request.POST.get('color')
                

                product = Product.objects.create(
                    name = name,
                    description = description,
                    highlights = highlights,
                    code = code,                
                    category_id = imageid

                )
                product.save()

                
                
                brand = Brands.objects.create(
                    name = brand,
                    product = product
                )


                for i in range(len(image1)):
                    image = f'image{i}'
                    if image in request.FILES:
                        image = request.FILES.getlist(image)

                        # Process or save each image as needed
                        for img in image:
                            img_instance = Image.objects.create(image=img, code=code, product=product)
                            img_instance.save()

                    
                price = varients.objects.create(
                    price = price,
                    variation = color,
                    stock = stock,
                    code = code,
                    product = product
                )
                price.save()
                return redirect(reverse('admin_products_list') + f'?image_id={request.GET.get("image_id")}')
          
                
            
            return render(request,'admin_products_list.html',{'products':products,'variant':variant})
        return redirect('signin')
    return redirect('signin')


def image_delete(request):
    prod = request.GET.get('id')
    obj = Image.objects.get(id = prod)
    obj.delete()   
    return JsonResponse({'status': 'ok'})


def product_edit(request,pk):

    if request.user.is_authenticated:
        if request.user.is_superuser:

            obj = Product.objects.get(id = pk)
            obj2 = varients.objects.get(product =  obj)
            obj3 = Image.objects.filter(product = obj)
            obj4 = Brands.objects.get(product = obj)
        
            if request.method == 'POST':

                name = request.POST.get('name')
                price = request.POST.get('price')
                image = request.FILES.getlist('image')
                brand = request.POST.get('brand')
                stock = request.POST.get('stock')
                description = request.POST.get('description')
                highlights = request.POST.get('highlights')
                
                obj.name = name
                obj2.price = price
                obj2.stock = stock
                obj.description = description
                obj.highlights = highlights
                obj4.name = brand

                obj2.save()
                obj.save()
                obj4.save()
                image_file = request.FILES.get('image', None)
                if image_file:
                    # If a new image is provided, create a new Image object
                    img_instance = Image.objects.create(image=image_file, code=obj.code, product=obj)
      
                return redirect(reverse('admin_products_list') + f'?image_id={obj.category.id}')
  
            return render(request,'product_edit.html',{'prod':obj,'img':obj3})
        return redirect('signin')

    return redirect('signin')


def unlist_product(request,pk):
    if request.user.is_authenticated:
        if request.user.is_superuser:

            obj = Product.objects.get(id=pk)
            if obj.unlist:
                obj.unlist = False
                obj.save()
            else:
                obj.unlist = True
                obj.save()
            return redirect(reverse('admin_products_list') + f'?image_id={obj.category.id}')
        return redirect('signin')
    return redirect('signin')



def products(request):

    if request.user.is_authenticated:

        Cart = cart.objects.filter(user = request.user).values_list("product",flat = True)

        err = None
        obj = None

        

        sort = request.GET.get('pk')
        if sort:
            if sort == 'products_high_to_low' :
                obj = Product.objects.annotate(max_price=Max('varients__price')).order_by('-max_price').filter(category__unlist = True , unlist = False)
            elif sort == 'products_low_to_high':
                obj = Product.objects.annotate(min_price=Min('varients__price')).order_by('min_price').filter(category__unlist=True, unlist=False)
            elif sort == 'obj_alpha_asc':
                obj = Product.objects.filter(category__unlist=True, unlist=False).order_by('name')
            elif sort == 'obj_alpha_desc':
                obj = Product.objects.filter(category__unlist=True, unlist=False).order_by('-name')
            elif sort == 'black':
                obj = Product.objects.filter(category__unlist=True,unlist=False,varients__variation='#000000').distinct()
            elif sort == 'white':
                obj = Product.objects.filter(category__unlist=True,unlist=False,varients__variation='#ffffff').distinct()
            else:
                obj = Product.objects.filter(category__unlist = True , unlist = False)

            paginator = Paginator(obj, 8    )
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
            return render(request,'product.html',{'product':page_obj,'cart':Cart,'err':err})
        
        obj = Product.objects.filter(category__unlist = True , unlist = False)
        if request.method == "POST":
            value = request.POST.get('search_query')
            try:
                obj = Product.objects.filter(name__icontains = value)
            except:
                pass
               
            # if obj:
            #     return render(request,'product.html',{'product':obj,'cart':Cart})
            if not obj:
                obj = Product.objects.filter(category__unlist = True , unlist = False)

                err = f'This product name "{value}" is not Available'
                # obj = Product.objects.filter(category__unlist = True , unlist = False)
                # return render(request,'product.html',{'product':obj,'cart':Cart,'err':err})
        paginator = Paginator(obj, 8)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(request,'product.html',{'product':page_obj,'cart':Cart,'err':err})
        
    return redirect('signin')


def increment_count(request):
    if request.user.is_authenticated:
        prod = request.GET.get('pk')
        obj = cart.objects.get(id = prod)
        for variant in obj.product.varients.all():
            if obj.quantity < variant.stock:
                obj.quantity += 1  # increment quantity
                obj.save()
                total = 0
                quant = 0
                for Cart in cart.objects.filter(user=request.user):
                    for variants in Cart.product.varients.all():
                        total += variants.price*Cart.quantity
                        quant += Cart.quantity
                subtotal = total + 40  # Update this according to your logic
                return JsonResponse({'quantity': obj.quantity, 'total': total, 'quant': quant, 'subtotal': subtotal})

def decrement_count(request):
    if request.user.is_authenticated:
        prod = request.GET.get('pk')
        obj = cart.objects.get(id = prod)
        if obj.quantity > 1:
            obj.quantity -= 1  # decrement quantity
            obj.save()
            total = 0
            quant = 0
            for Cart in cart.objects.filter(user=request.user):
                for variants in Cart.product.varients.all():
                    total += variants.price*Cart.quantity
                    quant -= Cart.quantity
            subtotal = total + 40  # Update this according to your logic
            return JsonResponse({'quantity': obj.quantity, 'total': total, 'quant': quant, 'subtotal': subtotal})

def Cart(request):
    if request.user.is_authenticated:
        if request.session.get('disc_price',None):
            del request.session['disc_price']
        user = CustomUser.objects.get(id = request.user.id)
        cart_items = cart.objects.filter(user = user)
        coupons = Coupons.objects.all()
        coupon_applied = 0
        today = date.today()

        try:
            address = Address.objects.filter(user = user).first()
        except Address.DoesNotExist:
            address = None


        total = 0
        quant = 0
        subtotal = 0
        cart_price = 1
        saved= 0
        totu = 0

        for Cart in cart_items:
            for variants in Cart.product.varients.all():
                if Cart.product.discount:
                    total += variants.price*Cart.quantity
                    totu += variants.price*Cart.quantity
                    quant += Cart.quantity
                    subtotal = total+40
                    cart_price = total / Cart.quantity
                    saved += totu-total

                else:
                    total += variants.price*Cart.quantity
                    quant += Cart.quantity
                    subtotal = total+40
                    cart_price = total / Cart.quantity
            

        coupon_error = 0
        coup = None
        disc_price = None

        if request.method == 'POST':
            coupon = request.POST.get('coupon')

            try:
                coup = Coupons.objects.get(code = coupon)
                if Order.objects.filter(coupon_code = coup.code , user = request.user).exists():
                    coupon_error = "you have already applied this coupon ..."
                    coup  = None

            except Coupons.DoesNotExist:
                coupon_error = "you have entered the wrong coupon .."
                coup = None
            
            if coup:
                if coup.code == coupon:
                    if coup.count > 0 and coup.ending_date > date.today() :
                        coup.count -=1
                        total = total 
                        subtotal = (total+ 40) - coup.discount_price
                        coupon_applied = coupon
                        coup.save()
                        disc_price = coup.discount_price

                        
                    else:
                        coupon_error = "coupon has reached maximum number.."
                        coup = None
                
        if coup:    
            request.session['coupon'] = int(coup.id)
            request.session['disc_price'] = disc_price
        else:
            request.session['coupon'] = None
            
        request.session['total_price'] = int(total)    
        
        err = request.session.get('err')
        if 'err' in request.session:
            del request.session['err']

        if err:
            return render(request,'cart.html',{'cart':cart_items,'saved':saved,'cart_price':cart_price,'disc_price':disc_price,'err':err ,'user':user,'total':total,'quant':quant,'address':address,'subtotal':subtotal,'coupon':coupons,'today':today ,'coupon_applied':coupon_applied , 'coupon_error' : coupon_error})        

        else:
            return render(request,'cart.html',{'cart':cart_items,'saved':saved ,'cart_price':cart_price,'disc_price':disc_price,'user':user,'total':total,'quant':quant,'address':address,'subtotal':subtotal,'coupon':coupons ,'coupon_applied':coupon_applied ,'today':today ,'coupon_error' : coupon_error})        
    return redirect('signin')
    
    
def add_to_cart(request):

    obj = request.GET.get('pk')
    obj2 = varients.objects.get(product = obj)

    Cart = cart.objects.create(
        user = request.user,
        product = obj2.product
    )
    Cart.save()

    return JsonResponse({'status': 'ok'})


def add_to_cart2(request):

    obj = request.GET.get('pk')
    obj2 = varients.objects.get(product = obj)
    obj3 = Product.objects.get(id = obj)

    Cart = cart.objects.create(
        user = request.user,
        product = obj2.product
    )
    Cart.save()

    return redirect(reverse('item_page',kwargs={'pk': obj}))
   

def cart_delete(request):
    prod = request.GET.get('pk')
    obj = cart.objects.get(id = prod)
    obj.delete()   
    return JsonResponse({'status': 'ok'})


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signout(request):
    if not request.user.is_authenticated:
        return redirect('signin')
    logout(request)
    return JsonResponse({'status': 'ok'})


def user_block(request,pk):

    try:
        user = CustomUser.objects.get(id = pk)
        user.is_active = False
        user.save()
        return redirect('admin_users')
    except CustomUser.DoesNotExist:
        return redirect('admin_users')
    

def user_unblock(request,pk):

    try:
        user = CustomUser.objects.get(id = pk)
        user.is_active = True
        user.save()
        return redirect('admin_users')
    except CustomUser.DoesNotExist:
        return redirect('admin_users')
    

def item_page(request,pk):

    if request.user.is_authenticated:
        Cart = cart.objects.all().values_list("product",flat = True)
       
        obj2 = Product.objects.get(id = pk)
        obj = Image.objects.filter(product = obj2)
        obj3 = varients.objects.get(product_id = obj2.id)
        colors = varients.objects.filter(code = obj2.code)
        return render(request,'item_page.html',{'img':obj,'product':obj2,'varients':obj3,'colors':colors,'cart':Cart})
    
    return redirect('signin')



def admin_category_edit(request,pk):
    if request.user.is_authenticated:
        if request.user.is_superuser:

            cate = Category.objects.get(id = pk)

            if request.method == 'POST':
                name = request.POST.get('name')
                image = request.FILES.get('image')

                cate.name = name
                cate.image = image

                cate.save()
                return redirect('admin_category')

            return render(request,'admin_category_edit.html',{'cate':cate})
        return redirect('signin')
    return redirect('signin')


def makeUnlist(request,pk):
    if request.user.is_authenticated:
        print('hi')
        catt = Category.objects.get(id = pk)
        catt.unlist = False
        catt.save()
        return redirect('admin_category')
    return redirect('signin')
    
def makeList(request,pk):
    if request.user.is_authenticated:
        print('hello')
        catt = Category.objects.get(id = pk)
        catt.unlist = True
        catt.save()
        return redirect('admin_category')
    return redirect('signin')
    
def user_profile(request):
    if request.user.is_authenticated:
        obj = CustomUser.objects.get(id = request.user.id)
        try:
            image = UserImage.objects.get(user = obj)
        except UserImage.DoesNotExist:
            image = None
        try:
            address = Address.objects.filter(user = obj)
            
        except Address.DoesNotExist:
            address = None

        tot_add = Address.objects.filter(user=obj)
        tot = 0
        ad = False
        for i in tot_add:
            tot += 1
        
        if tot < 4:
            ad = True

        return render(request,'user_profile.html',{'user':obj,'address':address,'image':image,'ad':ad})
    return redirect('signin')
    
def edit_profile(request):
    if request.user.is_authenticated:
        obj = CustomUser.objects.get(id = request.user.id)
        try:
            img = UserImage.objects.get(user=obj)
        except UserImage.DoesNotExist:
            img = UserImage(user=obj)

        try:
            address = Address.objects.filter(user = obj).first()            
        except Address.DoesNotExist:
            address = None

        a=''
        if request.GET.get('from') == 'checkout':
            a = reverse('checkout')
        else:
            a = reverse('user_profile')


        if request.method == "POST":
            firstname = request.POST.get('firstname')
            lastname = request.POST.get('lastname')
            username = request.POST.get('username')
            dob = request.POST.get('dob')
            age = request.POST.get('age')
            gender = request.POST.get('gender')
            phone = request.POST.get('phone')
            altphone = request.POST.get('altphone')
            image = request.FILES.get('photo')
           
            if age:
                obj.age = age
            if dob:
                obj.dob = dob
            obj.first_name = firstname
            obj.last_name = lastname
            obj.username = username
            obj.gender = gender
            obj.phone = phone
            obj.altphone = altphone
            
            obj.save()


            img.image = image
            img.save()
            


            return redirect('user_profile')

        return render(request,'edit_profile.html',{'user':obj,'img':img,'a':a,'address1':address})
    return redirect('signin')
    
def user_address(request,pk):
    if request.user.is_authenticated:
        user = CustomUser.objects.get(id = request.user.id)
        try:
            obj = Address.objects.get(id=pk)
        except Address.DoesNotExist:
            obj = None


        err = None

        if request.method == 'POST':
            houseno = request.POST.get('houseno')
            street = request.POST.get('street')
            city = request.POST.get('city')
            landmark = request.POST.get('landmark')
            pincode = request.POST.get('pincode')

            if obj:
                obj.houseno = houseno
                obj.street = street
                obj.city = city
                obj.landmark = landmark
                obj.pincode = pincode
            else:
                obj = Address.objects.create(
                    user=user,
                    houseno=houseno,
                    street=street,
                    city=city,
                    landmark=landmark,
                    pincode=pincode
                )
            
            if len(pincode) == 6 :
                obj.save()
                return redirect('user_profile')
            else:
                err = 'pincode must be valid'
        return render(request,'user_address.html',{'address':obj,'err':err})

    return redirect('signin')

def del_address(request,pk):
    if request.user.is_authenticated:
        obj = Address.objects.get(id = pk)
        obj.delete()
        return redirect('user_profile')

def add_address(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            houseno = request.POST.get('houseno')
            street = request.POST.get('street')
            city = request.POST.get('city')
            landmark = request.POST.get('landmark')
            pincode = request.POST.get('pincode')

            obj = Address.objects.create(
                user= request.user,
                houseno=houseno,
                street=street,
                city=city,
                landmark=landmark,
                pincode=pincode
            )

            obj.save()
            
            return redirect('user_profile')

        return render(request,'add_address.html')
    return redirect('signin')

def add_address_from_checkout(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            houseno = request.POST.get('houseno')
            street = request.POST.get('street')
            city = request.POST.get('city')
            landmark = request.POST.get('landmark')
            pincode = request.POST.get('pincode')

            obj = Address.objects.create(
                user= request.user,
                houseno=houseno,
                street=street,
                city=city,
                landmark=landmark,
                pincode=pincode
            )

            obj.save()
            return redirect('checkout')
        
        return render(request,'add_address_from_checkout.html')


def check(request):
    user = CustomUser.objects.get(id = request.user.id)
    cart_items = cart.objects.filter(user = user)

    for Cart in cart_items:
        for variants in Cart.product.varients.all():
            if Cart.quantity <= variants.stock:
                return redirect('checkout')
            else:
                err = 'Quantity not available'
                request.session['err'] = err
                return redirect('cart')
    

def checkout(request):
    if request.user.is_authenticated:

        user = CustomUser.objects.get(id = request.user.id)
        cart_items = cart.objects.filter(user = user)
        try:
            wallet = wallet_user.objects.get(user_id = request.user.id)
        except wallet_user.DoesNotExist:
            wallet = 0

        if request.POST.get('address'):
            change_add = request.POST.get('address')
            address = Address.objects.get(id=change_add)
        else:

            try:
                address = Address.objects.filter(user=user).first()
            except Address.DoesNotExist:
                address = None

        try:
            addresses = Address.objects.filter(user = user)
        except Address.DoesNotExist:
            addresses = None

        total = request.session.get('total_price')
        coup = request.session.get('coupon')
        disc_price = request.session.get('disc_price',None)
        sub_total = total
        if disc_price:
            sub_total = int(total) - int(disc_price)
            del request.session['disc_price']

        
        
        
        
        tot_add = Address.objects.filter(user=user)
        tot = 0
        ad = False
        for i in tot_add:
            tot += 1
        
        if tot < 4:
            ad = True

        quant = 0
        for Cart in cart_items:
            for variants in Cart.product.varients.all():
                quant += Cart.quantity

        coupon = 0
        try:
            coupon = Coupons.objects.get(id = coup)
        except Coupons.DoesNotExist:
            coupon = None

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY , settings.RAZORPAY_SECRET))
        order = client.order.create({'amount':int((sub_total+40)*100),'currency':'INR','payment_capture':1})
        
        if request.method == 'POST':
            print(request.POST.get('payment_method'),'jjj' , request.POST)
            if request.POST.get("payment_method"):
                print('entered')

                payment = request.POST.get('payment_method')
                address = request.POST.get("address")
                address =  Address.objects.get(pk = address)

                wall_err = ''
                if payment == 'wallet' and wallet.amount < sub_total+40:
                    wall_err = 'Your wallet amount is not enough'
                    print('wall_err')
                    return render(request,'checkout.html',{'user':user,'ad':ad,'address':address,'cart':cart_items,'quant':quant,'total':total,'addresses':addresses , 'order':order,'disc_price':disc_price,'sub_total':sub_total,'wallet':wallet,'wall_err':wall_err})
                
                elif payment:        

                    

            
                    order = Order.objects.create(
                        price = sub_total + 40,
                        date = date.today(),
                        status = 'Ordered',
                        payment = payment,
                        user = user,
                        address = address,
                        quantity = Cart.quantity,
                    )

                    if coupon :
                        order.coupon_code = coupon.code,
                        order.coupon_price = coupon.discount_price
                    if payment == 'online':
                        razor_id = request.session.get('razor_id')

                        razor = razor_pay.objects.get(id = razor_id)

                        razor.order = order

                        razor.save()

                    elif payment == 'wallet':
                        wallet.amount -= order.price
                        wallet.save()

                        wall_his = WalletHistory(amount=order.price,transaction_type='debit',user=request.user)
                        wall_his.save()

                    products = cart.objects.filter(user = user)
    
                    for cart_item in products:
                        order.product.add(cart_item.product)

                    del_cart = cart.objects.filter(user = user)
                    for carts in del_cart:
                        variants.stock = variants.stock-carts.quantity
                        variants.save()
                        
                    order.save()

                    del_cart.delete()


                    ordered = True
                    request.session['ordered'] = ordered
                    if request.session.get('disc_price',None):
                        del request.session['disc_price']


                    return redirect('order_confirm')
            else:
                err = 'please select a payment method'
                return render(request,'checkout.html',{'user':user,'ad':ad,'address':address,'cart':cart_items,'quant':quant,'total':Decimal(total),'err':err,'order':order,'addresses':addresses,'disc_price':disc_price,'sub_total':sub_total,'wallet':wallet})
        

        return render(request,'checkout.html',{'user':user,'ad':ad,'address':address,'cart':cart_items,'quant':quant,'total':total,'addresses':addresses , 'order':order,'disc_price':disc_price,'sub_total':sub_total,'wallet':wallet})
    return redirect('signin')

    
def order_confirm(request):
    if request.user.is_authenticated:
        
        ord = request.session.get('ordered')
       

        if ord:
            return render(request, 'order_confirm.html')
        else:
            del request.session[ord]
            return redirect('home')
    return redirect('signin')

@csrf_exempt
def razor_success(request):
    if request.method == 'POST':
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        print(razorpay_payment_id)
        print(razorpay_order_id)

        
        razor = razor_pay.objects.create(
            razopay_order_id = razorpay_order_id,
            razopay_payment_id = razorpay_payment_id, 
        )

        razor.save()

        request.session['razor_id'] = razor.id


        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
def myorders(request):
    if request.user.is_authenticated:
        try:
            orders = Order.objects.filter(user = request.user).order_by('-id')
        except Order.DoesNotExist:
            orders = None

        date_valid = False
        if orders:
            
            for order in orders:
                
                ordered_date = order.date

                date_limit = ordered_date + timedelta(days=7)

                if date.today() <= date_limit:
                    date_valid = True



        return render(request, 'myorders.html',{'orders':orders,'date_valid':date_valid})
    return redirect('signin')
    
def order_details(request):
    if request.user.is_authenticated:

        pk = request.GET.get('pk')
        orders = Order.objects.filter(id = pk)



        return render(request,'order_details.html',{'orders':orders})


def change_password(request):

    if request.user.is_authenticated:
        if request.method == 'POST':
            curr_password = request.POST.get('currentpassword')
            new_password = request.POST.get('newPassword')
            confirm_password = request.POST.get('confirmPassword')

            if check_password(curr_password, request.user.password):
                if new_password == confirm_password:
                    request.user.set_password(new_password)
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    return redirect('user_profile')
                err = 'password must be same'
                return render(request,'change_password',{'err':err})
            err2 = 'current password is wrong'
            return render(request,'change_password',{'err2':err2})

        return render(request,'change_password.html')
    return redirect('signin')

def cancel_order(request):
    if request.user.is_authenticated:
        obj = request.GET.get('pk')
        order = Order.objects.get(id = obj)
        
        for product in order.product.all():
            for variant in product.varients.all():
                variant.stock += order.quantity
                variant.save()
        order.status = 'Cancelled'

        if order.payment == 'online':

            try:
                wallet = wallet_user.objects.get(user = request.user)
                wallet.amount += order.price
                wallet.save()

                obj = WalletHistory(amount=order.price,transaction_type='credit',user=request.user)
                obj.save()
            except:
                wallet = wallet_user.objects.create(
                    amount = order.price,
                    payment_type = order.payment,
                    user = request.user
                )
                obj = WalletHistory(amount=order.price,transaction_type='credit',user=request.user)
                obj.save()

        

        order.date = date.today()
        order.save()
        
        return JsonResponse({'status': 'ok'})

def admin_coupons(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:

            try:
                coupon = Coupons.objects.all()
            except Coupons.DoesNotExist:
                coupon = None

            if request.method == 'POST':
                code = request.POST.get('code')
                discount_price = request.POST.get('discount_price')
                starting_date = request.POST.get('starting_date')
                ending_date = request.POST.get('ending_date')
                count = request.POST.get('count')


                obj = Coupons.objects.create(
                    code = code,
                    discount_price = discount_price,
                    starting_date = starting_date,
                    ending_date = ending_date,
                    count = count
                )
                obj.save()
                return redirect('admin_coupons')

            return render(request,'admin_coupons.html',{'coupons':coupon})  
        return redirect('signin')
    return redirect('signin')
    
def admin_coupon_edit(request,pk):
    if request.user.is_authenticated:
        if request.user.is_superuser:

            coupon = Coupons.objects.get(id = pk)
            
            if request.method == 'POST':
                coupon.code = request.POST.get('code')
                coupon.discount_price = request.POST.get('discount_price')
                coupon.starting_date = request.POST.get('starting_date')
                coupon.ending_date = request.POST.get('ending_date')
                coupon.count = request.POST.get('count')
                coupon.save()

                return redirect('admin_coupons')

            return render(request,'admin_coupon_edit.html',{'coupon':coupon})
        return redirect('signin')
    
    return redirect('signin')

def admin_coupon_delete(request,pk):
    if request.user.is_authenticated:
        if request.user.is_superuser:
        
            coupon = Coupons.objects.get(id = pk)
            coupon.delete()
            return redirect('admin_coupons')
        return redirect('signin')
    return redirect('signin')


def invoice_pdf(request , pk):
    template_path = 'invoice.html'
    order = Order.objects.get(pk = pk)
    for prod in order.product.all():
        for brands in prod.Brands.all():
            brands = brands.name


    context = {'order': order,'brand':brands}
   
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response ,encoding='UTF-8')
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


def export_to_pdf(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    order = Order.objects.filter(date__gte = start,date__lte = end)
    template_path = 'admin_pdf_salesreport.html'
    context = {'orders': order}
   
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="salesreport.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response ,encoding='UTF-8')
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

def export_to_excel(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="products.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = "Sales report"

    # Add headers
    headers = ["id","date","products", "user" , "price" ,"quantity" ,"payment" ]
    ws.append(headers)

    # Add data from the model
    order = Order.objects.filter(date__gte = start,date__lte = end)
    for i in order:
        product=""
        for j in i.product.all():
            product +=j.name

        ws.append([f"ORD{i.id}",str(i.date),product,i.user.first_name,i.price,i.quantity,i.payment])

    # Save the workbook to the HttpResponse
    wb.save(response)
    return response


def my_wallet(request):
    if request.user.is_authenticated:
        try:
            wallet = wallet_user.objects.get(user=request.user)
        except wallet_user.DoesNotExist:
            wallet = None
        history = WalletHistory.objects.filter(user=request.user).order_by('-date')

        context = {'user': request.user, 'wallet': wallet, 'history': history}
        return render(request, 'my_wallet.html', context)
    return redirect('signin')

def return_order(request,pk):

    orders = Order.objects.get(id = pk)
    orders.status = 'Returning'
    orders.save()

    return redirect('myorders')
    

def wishlist(request):
    if request.user.is_authenticated:
        return render(request,'404.html')
    return redirect('signin')

def aboutus(request):
    if request.user.is_authenticated:
        return render(request,'404.html')
    return redirect('signin')