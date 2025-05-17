from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.bitrix_webhook, name='bitrix_webhook'),
]