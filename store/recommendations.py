from django.db import models
from django.contrib.auth import get_user_model
from .models import UserProfile, Product, OrderItem
from django.db.models import Count

def get_recommendations(user):
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return Product.objects.none()
    
    # Собираем данные о пользователе
    bought = OrderItem.objects.filter(order__user=user).values_list('product', flat=True)
    favorites = profile.favorite_products.values_list('id', flat=True)
    viewed = profile.viewed_products.values_list('id', flat=True)
    
    # Объединяем все интересующие товары
    interest_ids = list(bought) + list(favorites) + list(viewed)
    
    # Ищем товары из тех же категорий и брендов
    recommendations = Product.objects.filter(
        models.Q(category__products__id__in=interest_ids) |
        models.Q(brand__products__id__in=interest_ids)
    ).exclude(
        id__in=interest_ids
    ).annotate(
        relevance=Count('orders')
    ).order_by('-relevance', '-created_at')[:12]
    
    return recommendations