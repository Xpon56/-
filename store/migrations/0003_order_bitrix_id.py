# Generated by Django 5.2 on 2025-05-13 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_userprofile_last_activity'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='bitrix_id',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='ID сделки в Bitrix24'),
        ),
    ]
