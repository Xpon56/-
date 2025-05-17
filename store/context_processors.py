from .models import Cart

def cart_context(request):  # ← Измените название функции
    if not request.session.session_key:
        request.session.create()
    cart = Cart.objects.filter(session_key=request.session.session_key).first()
    if not cart:
        cart = Cart.objects.create(session_key=request.session.session_key)
    return {'cart': cart}