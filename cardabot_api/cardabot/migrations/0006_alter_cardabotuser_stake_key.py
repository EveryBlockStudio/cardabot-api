# Generated by Django 4.0.3 on 2022-05-04 01:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cardabot', '0005_cardabotuser_chat_cardabot_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cardabotuser',
            name='stake_key',
            field=models.CharField(max_length=256, unique=True),
        ),
    ]
