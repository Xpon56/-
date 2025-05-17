from pybitrix24 import Bitrix24
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Bitrix24Service:
    def __init__(self):
        self.bx = Bitrix24()
        self.bx.set_webhook(settings.BITRIX_WEBHOOK_URL)
    
    def create_deal(self, order_data):
        """Создание сделки в Битрикс24"""
        try:
            response = self.bx.call(
                'crm.deal.add',
                {
                    'fields': {
                        'TITLE': f"Заказ #{order_data['id']}",
                        'STAGE_ID': settings.BITRIX_DEAL_STAGE_ID,
                        'ASSIGNED_BY_ID': settings.BITRIX_ASSIGNEE_ID,
                        'OPPORTUNITY': float(order_data['total']),
                        'CONTACT_ID': self._get_or_create_contact(order_data['user'])
                    }
                }
            )
            return response
        except Exception as e:
            logger.error(f"Bitrix24 Error: {str(e)}")
            return None

    def _get_or_create_contact(self, user_info):
        """Создание/получение контакта"""
        contact = self.bx.call(
            'crm.contact.list',
            {'filter': {'EMAIL': user_info['email']}}
        )
        
        if contact.get('result'):
            return contact['result'][0]['ID']
        
        new_contact = self.bx.call(
            'crm.contact.add',
            {
                'fields': {
                    'NAME': user_info['first_name'],
                    'LAST_NAME': user_info['last_name'],
                    'EMAIL': [{'VALUE': user_info['email'], 'VALUE_TYPE': 'WORK'}],
                    'PHONE': [{'VALUE': user_info['phone'], 'VALUE_TYPE': 'WORK'}]
                }
            }
        )
        return new_contact['result']
    
    def create_product(self, product_data):
        """Создание товара в Битрикс24"""
        try:
            response = self.bx.call(
                'crm.product.add',
                {
                    'fields': {
                        'NAME': product_data['name'],
                        'DESCRIPTION': product_data['description'],
                        'PRICE': float(product_data['price']),
                        'CURRENCY_ID': 'RUB',
                        'CATEGORY_ID': settings.BITRIX_PRODUCT_CATEGORY_ID,
                    }
                }
            )
            return response
        except Exception as e:
            logger.error(f"Ошибка создания товара: {str(e)}")
            return None