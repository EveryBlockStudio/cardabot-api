# Generated by Django 4.0.3 on 2022-04-09 01:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cardabot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='client',
            field=models.CharField(blank=True, choices=[('TELEGRAM', 'Telegram'), ('', 'None')], default='', max_length=16),
        ),
    ]
