from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
def bitrix_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Обработка изменения статуса сделки
            # Добавьте свою логику обработки
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)