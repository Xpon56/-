from celery import shared_task
from django.conf import settings
import requests
import json
import logging
from store.models import Order
from store.models import Order, Product 
from bitrix24_integration.services import Bitrix24Service 

logger = logging.getLogger(__name__)

class Bitrix24API:
    def __init__(self):
        self.webhook_url = settings.BITRIX24_WEBHOOK_URL.rstrip('/')
        self.timeout = 10

    def _call_method(self, method, data):  # ✅ Метод с отступами
        url = f"{self.webhook_url}/{method}"
        try:
            response = requests.post(
                url,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Bitrix24 API Error: {str(e)}")
            return None

    def create_deal(self, order_data):
        contact_id = self.create_contact(order_data['customer'])
        if not contact_id:
            return None
            
        deal_data = {
            'fields': {
                'TITLE': f"Заказ #{order_data['id']}",
                'STAGE_ID': settings.BITRIX24_DEAL_STAGE,
                'ASSIGNED_BY_ID': settings.BITRIX24_ASSIGNEE,
                'CONTACT_ID': contact_id,
                'OPPORTUNITY': order_data['total'],
                'CURRENCY_ID': 'RUB',
                'COMMENTS': f"Номер заказа: {order_data['id']}"
            }
        }
        return self._call_method('crm.deal.add', deal_data)

    def create_contact(self, customer_data):
        contact_data = {
            'fields': {
                'NAME': customer_data.get('first_name', ''),
                'LAST_NAME': customer_data.get('last_name', ''),
                'PHONE': [{'VALUE': customer_data['phone'], 'VALUE_TYPE': 'WORK'}],
                'EMAIL': [{'VALUE': customer_data['email'], 'VALUE_TYPE': 'WORK'}]
            }
        }
        result = self._call_method('crm.contact.add', contact_data)
        return result.get('result') if result else None

@shared_task(bind=True, max_retries=3)
def sync_order_to_bitrix24(self, order_id, customer_data):
    try:
        order = Order.objects.get(id=order_id)
        bitrix = Bitrix24API()
        
        order_data = {
            'id': order.id,
            'total': float(order.total),
            'customer': {
                'first_name': customer_data.get('first_name', ''),
                'last_name': customer_data.get('last_name', ''),
                'phone': customer_data['phone'],
                'email': customer_data['email']
            }
        }
        
        result = bitrix.create_deal(order_data)
        if result and 'result' in result:
            order.bitrix_id = result['result']
            order.save()
            return True
            
    except Exception as e:
        logger.error(f"Sync failed for order {order_id}: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)
        
    return False

@shared_task
def sync_products_to_bitrix24():
    products = Product.objects.all()
    bitrix = Bitrix24Service()
    for product in products:
        product_data = {
            'name': product.name,
            'description': product.description,
            'price': product.price,
        }
        bitrix.create_product(product_data)