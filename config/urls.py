from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from store import views
from django.contrib.auth import views as auth_views
from store.views import CatalogView
from store.views import admin_dashboard, add_product

urlpatterns = [
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/', admin.site.urls),
    path('add-product/', add_product, name='add_product'),
    path('', views.home, name='home'),
    path('contacts/', views.contact, name='contact'),
    path('delivery/', views.delivery, name='delivery'),
    path('cart/', views.cart_detail, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('catalog/', CatalogView.as_view(), name='catalog'),
    path('product/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('product/<int:product_id>/rate/', views.add_rating, name='add_rating'),
    path('product/<int:product_id>/add-to-favorites/', views.add_to_favorites, name='add_to_favorites'),
    path('product/<int:product_id>/remove-from-favorites/', views.remove_from_favorites, name='remove_from_favorites'),
    path('profile/favorites/', views.favorites_full, name='favorites_full'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('warranty/', views.warranty, name='warranty'),
    path('returns/', views.returns, name='returns'),
    path('faq/', views.faq, name='faq'),

    # Восстановление пароля
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='store/password_reset.html',
             email_template_name='store/password_reset_email.html',
             success_url='done/'
         ),
         name='password_reset'),
    
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='store/password_reset_done.html'
         ),
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='store/password_reset_confirm.html',
             success_url='/reset/done/'
         ),
         name='password_reset_confirm'),
    
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='store/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)