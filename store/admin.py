from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .models import (
    Category, Brand, Product, ContactRequest, 
    Cart, CartItem, CustomUser, UserProfile, 
    Order, OrderItem, ProductRating,
    ProductAttribute, ProductAttributeValue,
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    raw_id_fields = ('product',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_key', 'created_at')
    list_filter = ('created_at',)
    inlines = [CartItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ('product',)
    fields = ('product', 'quantity', 'price', 'total_price')
    readonly_fields = ('total_price',)

    def total_price(self, obj):
        return obj.total_price() or "Ошибка в данных" 
    total_price.short_description = 'Сумма'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_link', 'status', 'total', 'created_at', 'city', 'phone')
    list_filter = ('status', 'created_at', 'city')
    search_fields = ('user__username', 'id', 'phone')
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('user', 'status', 'total')}),
        ('Доставка', {'fields': ('address', 'city', 'postal_code', 'phone')}),
        ('Даты', {'fields': ('created_at', 'updated_at')}),
    )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['dashboard_link'] = reverse('admin_dashboard')
        return super().changelist_view(request, extra_context=extra_context)

    def user_link(self, obj):
        from django.utils.html import format_html
        return format_html('<a href="/admin/store/customuser/{}/change/">{}</a>', obj.user.id, obj.user.username)
    user_link.short_description = 'Пользователь'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price', 'discount', 'created_at')
    list_filter = ('category', 'brand', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'category', 'brand')}),
        ('Контент', {'fields': ('description', 'price', 'discount', 'image')}),
        ('Дополнительно', {'fields': ('created_at',)}),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'favorites_count')
    search_fields = ('user__username',)
    filter_horizontal = ('favorite_products',)

    def favorites_count(self, obj):
        return obj.favorite_products.count()
    favorites_count.short_description = 'Избранных товаров'

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'date_joined', 'is_staff')
    search_fields = ('username', 'email', 'phone')
    list_filter = ('is_staff', 'is_superuser', 'date_joined')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('email', 'phone')}),
        ('Права', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 
                      'groups', 'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'password1', 'password2'),
        }),
    )

@admin.register(ProductRating)
class ProductRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username')


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'filter_type')
    list_filter = ('filter_type',)
    filter_horizontal = ('categories',)
    
    # Группировка по категориям в админке
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug')
        }),
        ('Тип фильтра', {
            'fields': ('filter_type',)
        }),
    )

class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1  # Количество пустых форм для добавления

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductAttributeValueInline]
    list_display = ('name', 'category', 'brand', 'price')
    list_filter = ('category', 'brand')
    search_fields = ('name', 'category__name')

    # Автозаполнение slug
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(ContactRequest)