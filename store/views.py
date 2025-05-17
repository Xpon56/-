from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, CartItem, UserProfile, Order, CustomUser 
from .forms import ContactForm, CartItemForm, RegistrationForm, CustomAuthenticationForm, ProfileForm
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator
from .models import Product, Category, Brand
from django.db.models import Count 
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render
from .models import Product, Category, Brand
from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Product, Category, Brand
from .models import OrderItem
from .models import ProductRating, ProductView, ProductAttribute
from .forms import RatingForm
from django.db.models import Q
from .filters import ProductFilter
from django_filters.views import FilterView
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, F, DateField
from django.db.models.functions import Trunc
from django.db.models import Count, Sum, Q, F
from django.db.models.functions import Trunc
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import redirect
from .forms import ProductForm
from bitrix24_integration.tasks import sync_order_to_bitrix24
from django.views.decorators.csrf import csrf_exempt
import json  

import logging
logger = logging.getLogger(__name__) 

def home(request):
    categories = Category.objects.all()[:4]
    brands = Brand.objects.all()[:4]
    products = Product.objects.filter(discount__gt=0)[:3]
    

    if request.user.is_authenticated:
        from .recommendations import get_recommendations
        recommended_products = get_recommendations(request.user)[:3]
    else:
        recommended_products = Product.objects.filter(discount__gt=0)[:3]
    
    context = {
        'categories': categories,
        'brands': brands,
        'products': products,
        'recommended_products': recommended_products
    }
    return render(request, 'store/home.html', context)

def delivery(request):
    return render(request, 'store/delivery.html')

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ваше сообщение успешно отправлено!')
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'store/contact.html', {'form': form})

def get_cart(request):
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart

def cart_detail(request):
    cart = get_cart(request)
    cart_items = cart.items.select_related('product')
    total = sum(item.total_price() for item in cart_items)
    
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        
        if action == 'remove':
            cart_item = get_object_or_404(CartItem, id=item_id)
            cart_item.delete()
        elif action == 'update':
            form = CartItemForm(request.POST)
            if form.is_valid():
                cart_item = get_object_or_404(CartItem, id=item_id)
                cart_item.quantity = form.cleaned_data['quantity']
                cart_item.save()
        return redirect('cart')
    
    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'store/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Проверка существования пользователя
            try:
                user = CustomUser.objects.get(username=username)
            except CustomUser.DoesNotExist:
                messages.error(request, 'Пользователь не найден')
                return render(request, 'store/login.html', {'form': form})

            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Неверный пароль')
        else:
            messages.error(request, 'Ошибка в форме ввода')
        return render(request, 'store/login.html', {'form': form})
    
    form = CustomAuthenticationForm()
    return render(request, 'store/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def profile(request):
    # Безопасное получение профиля (с созданием, если не существует)
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Активные заказы (исключая завершенные/отмененные) с сортировкой
    active_orders = Order.objects.filter(
        user=request.user
    ).exclude(
        status__in=['completed', 'canceled']
    ).order_by('-created_at')
    
    # История заказов (только завершенные/отмененные) с сортировкой
    order_history = Order.objects.filter(
        user=request.user,
        status__in=['completed', 'canceled']
    ).order_by('-created_at')
    
    # Превью избранного (первые 3 товара)
    favorites_preview = profile.favorite_products.all()[:3]
    
    # Обработка формы профиля
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Данные успешно обновлены')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    
    return render(request, 'store/profile.html', {
        'form': form,
        'active_orders': active_orders,
        'order_history': order_history,
        'favorites_preview': favorites_preview  # Передаем только превью
    })


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'price': product.price}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    # Редирект обратно на предыдущую страницу
    redirect_url = request.POST.get('redirect_url', '/')
    return redirect(redirect_url)


def product_detail(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    rating_form = RatingForm()  # Создаем форму для оценки
    if request.user.is_authenticated:
        ProductView.objects.create(
            user_profile=request.user.userprofile,
            product=product
        )
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'rating_form': rating_form  # Добавляем форму в контекст
    })

@login_required
def checkout(request):
    cart = get_cart(request)
    cart_items = cart.items.select_related('product')
    total = sum(item.total_price() for item in cart_items)
    
    if request.method == 'POST':
        # Создаем заказ
        order = Order.objects.create(
            user=request.user,
            total=total,
            status='new',
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            postal_code=request.POST.get('postal_code', ''),
            phone=request.POST.get('phone', '')
        )
        
        # Создаем позиции заказа
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.price
            )
        
        # Очищаем корзину
        cart.items.all().delete()
        
        # Отправляем данные в Битрикс24 через Celery
        user_data = {
            'total': float(total),
            'first_name': request.user.first_name or '',
            'last_name': request.user.last_name or '',
            'email': request.user.email,
            'phone': request.POST.get('phone', '')
        }
        if order:
            customer_data = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'phone': request.user.phone,
                'email': request.user.email,
            }
            sync_order_to_bitrix24.delay(order.id, customer_data)
        
        return redirect('order_success', order_id=order.id)
    
    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total': total
    })

def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/order_success.html', {'order': order})

@login_required
def add_rating(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating, created = ProductRating.objects.update_or_create(
                product=product,
                user=request.user,
                defaults=form.cleaned_data
            )
            messages.success(request, 'Ваша оценка сохранена!')
            return redirect('product_detail', product_slug=product.slug)
    else:
        form = RatingForm()

    return redirect('product_detail', product_slug=product.slug)


@login_required
def add_to_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    profile = request.user.userprofile
    if product not in profile.favorite_products.all():
        profile.favorite_products.add(product)
        messages.success(request, 'Товар добавлен в избранное')
    else:
        messages.info(request, 'Товар уже в избранном')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def remove_from_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    request.user.userprofile.favorite_products.remove(product)
    messages.success(request, 'Товар удален из избранного')
    return redirect('profile')

@login_required
def favorites_full(request):
    profile = request.user.userprofile
    favorites = profile.favorite_products.all()
    
    # Фильтрация
    selected_categories = request.GET.getlist('category')
    selected_brands = request.GET.getlist('brand')
    min_price = request.GET.get('price_min')
    max_price = request.GET.get('price_max')
    
    if selected_categories:
        favorites = favorites.filter(category__id__in=selected_categories)
    if selected_brands:
        favorites = favorites.filter(brand__id__in=selected_brands)
    if min_price:
        favorites = favorites.filter(price__gte=min_price)
    if max_price:
        favorites = favorites.filter(price__lte=max_price)
    
    # Сортировка
    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        favorites = favorites.order_by('price')
    elif sort == 'price_desc':
        favorites = favorites.order_by('-price')
    elif sort == 'newest':
        favorites = favorites.order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(favorites, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'brands': Brand.objects.all(),
    }
    return render(request, 'store/favorites.html', context)

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.select_related('product')
    return render(request, 'store/order_detail.html', {
        'order': order,
        'order_items': order_items
    })

@login_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.can_be_canceled():
        messages.error(request, 'Этот заказ нельзя отменить')
        return redirect('order_detail', order_id=order.id)
    
    order.status = 'canceled'
    order.save()
    messages.success(request, 'Заказ успешно отменен')
    return redirect('order_detail', order_id=order.id)

def warranty(request):
    return render(request, 'store/warranty.html')

def returns(request):
    return render(request, 'store/returns.html')

def faq(request):
    return render(request, 'store/faq.html')


class CatalogView(FilterView):
    filterset_class = ProductFilter
    template_name = 'store/catalog.html'
    paginate_by = 12
    context_object_name = 'products'

    def get_queryset(self):
        # Базовый QuerySet без сортировки
        queryset = Product.objects.all()
        
        # Применяем фильтрацию
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
        filtered_qs = self.filterset.qs
        
        # Применяем сортировку
        sort = self.request.GET.get('sort', '')
        if sort == 'price_asc':
            filtered_qs = filtered_qs.order_by('price')
        elif sort == 'price_desc':
            filtered_qs = filtered_qs.order_by('-price')
        elif sort == 'newest':
            filtered_qs = filtered_qs.order_by('-created_at')
            
        return filtered_qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort'] = self.request.GET.get('sort', '')
        return context
    
# ДЭШБОРД АДМИЯНА АНАЛИТИКА

@staff_member_required
def admin_dashboard(request):
    # Основные метрики
    time_period = 30  # дней

    # 1. Продажи по категориям
    category_sales = (
        Category.objects
        .annotate(total_sales=Sum('products__orderitem__price'))
        .values('name', 'total_sales')
        .order_by('-total_sales')
    )

    # 2. Динамика новых пользователей
    user_growth = (
        CustomUser.objects
        .annotate(day=Trunc('date_joined', 'day', output_field=DateField()))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')[:time_period]
    )

    # 3. Последние заказы
    recent_orders = (
        Order.objects
        .select_related('user')
        .prefetch_related('items')
        .order_by('-created_at')[:10]
    )

    # 4. Статистика заказов
    order_stats = Order.objects.aggregate(
        total_orders=Count('id'),
        canceled_orders=Count('id', filter=Q(status='canceled'))
    )

    # 5. Общая статистика
    total_orders = order_stats.get('total_orders', 0)
    total_revenue = Order.objects.aggregate(total=Sum('total'))['total'] or 0
    avg_order_value = total_revenue / total_orders if total_orders else 0

    # 6. Активность пользователей
    user_activity = {
        'active_users': UserProfile.objects.filter(
            last_activity__gte=timezone.now() - timedelta(days=1)
        ).count()
    }

    context = {
        'category_sales': list(category_sales),
        'user_growth': list(user_growth),
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'user_activity': user_activity,
        'order_stats': order_stats,
    }
    return render(request, 'admin/dashboard.html', context)


@staff_member_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                new_product = form.save()
                print(f"Создан товар: {new_product.name}")  # Для отладки
                messages.success(request, 'Товар успешно добавлен!')
                return redirect('catalog')
            except Exception as e:
                print(f"Ошибка сохранения: {str(e)}")  # Для отладки
                messages.error(request, f'Ошибка: {str(e)}')
        else:
            print("Форма невалидна. Ошибки:", form.errors)  # Для отладки
    else:
        form = ProductForm()
    
    return render(request, 'store/add_product.html', {'form': form})

@csrf_exempt
def bitrix_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        event = data.get('event')
        
        # Обновление статуса сделки
        if event == 'ONCRMDEALUPDATE':
            deal_id = data['data']['FIELDS']['ID']
            new_stage = data['data']['FIELDS']['STAGE_ID']
            try:
                order = Order.objects.get(bitrix_id=deal_id)
                order.status = order.map_bitrix_status(new_stage)
                order.save()
            except Order.DoesNotExist:
                logger.error(f"Заказ с bitrix_id={deal_id} не найден")
        
        return JsonResponse({'status': 'success'})