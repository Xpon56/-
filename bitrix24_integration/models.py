from django.db import models

class BitrixSyncLog(models.Model):
    ACTION_CHOICES = [
        ('DEAL_CREATE', 'Создание сделки'),
        ('CONTACT_UPDATE', 'Обновление контакта'),
        ('ERROR', 'Ошибка синхронизации'),
    ]

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_success = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_action_display()} - {self.created_at}"