from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from bitrix24_integration.services import Bitrix24Service 

import logging
logger = logging.getLogger(__name__) 

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)


    def product_count(self):
        return self.products.count()

    def __str__(self):
        return self.name
    
class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)
    orders = models.ManyToManyField('Order', through='OrderItem')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def original_price(self):
        return self.price * (100 + self.discount) / 100
    
    @property
    def average_rating(self):
        from django.db.models import Avg
        return self.ratings.aggregate(Avg('rating'))['rating__avg'] or 0.0

    @property
    def ratings_count(self):
        return self.ratings.count()

    def __str__(self):
        return self.name

class ContactRequest(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя')
    email = models.EmailField(verbose_name='Email')
    subject = models.CharField(max_length=200, verbose_name='Тема')
    message = models.TextField(verbose_name='Сообщение')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.email}"

    class Meta:
        verbose_name = 'Обращение'
        verbose_name_plural = 'Обращения'

class Cart(models.Model):
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def total_price(self):
        return self.quantity * self.price

class CustomUser(AbstractUser):
    phone_validator = RegexValidator(
        regex=r'^7\d{10}$',
        message="Телефон должен быть в формате: 79991234567 (11 цифр без +)"
    )
    phone = models.CharField(
        validators=[phone_validator],
        max_length=11,
        unique=True,
        verbose_name='Телефон'
    )
    email = models.EmailField(unique=True)
    agreement = models.BooleanField(default=False)

    def __str__(self):
        return self.username
    

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    favorite_products = models.ManyToManyField('Product', blank=True)
    viewed_products = models.ManyToManyField('Product', through='ProductView', related_name='viewed_by')
    last_activity = models.DateTimeField(default=timezone.now)  # Добавьте это поле

    def update_activity(self):
        self.last_activity = timezone.now()
        self.save()

class ProductView(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
    bitrix_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID сделки в Bitrix24')
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('completed', 'Завершен'),
        ('canceled', 'Отменен'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Новые поля для адреса
    address = models.TextField(verbose_name='Адрес доставки', blank=True)
    city = models.CharField(max_length=100, verbose_name='Город', blank=True)
    postal_code = models.CharField(max_length=20, verbose_name='Индекс', blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон', blank=True)

    def can_be_canceled(self):
        return self.status in ['new', 'processing']

    def __str__(self):
        return f"Заказ #{self.id}"
    
    def update_bitrix_status(self, new_status):
        bitrix = Bitrix24Service()
        try:
            bitrix.bx.call('crm.deal.update', {
                'id': self.bitrix_id,
                'fields': {'STAGE_ID': new_status}
            })
            self.status = self.map_bitrix_status(new_status)
            self.save()
        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {str(e)}")

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)  # Значение по умолчанию
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Обязательное поле

    def total_price(self):
        return self.quantity * self.price

    def total_price(self):
        if self.quantity and self.price:  # Проверка на наличие значений
            return self.quantity * self.price
        return 0 

class ProductRating(models.Model):
    RATING_CHOICES = [
        (1, '1 звезда'),
        (2, '2 звезды'),
        (3, '3 звезды'),
        (4, '4 звезды'),
        (5, '5 звезд'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')  # Один пользователь — одна оценка

    def __str__(self):
        return f"{self.product.name} — {self.get_rating_display()}"


class ProductAttribute(models.Model):
    CATEGORY_CHOICES = [
        ('range', 'Диапазон'),
        ('multi', 'Множественный выбор'),
        ('bool', 'Да/Нет')
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    filter_type = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    categories = models.ManyToManyField(Category)

    def __str__(self):
        return self.name

class ProductAttributeValue(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)
    
    class Meta:
        unique_together = ('product', 'attribute')
