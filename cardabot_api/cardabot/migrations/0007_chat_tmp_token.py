# Generated by Django 4.0.3 on 2022-05-19 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cardabot', '0006_alter_cardabotuser_stake_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='tmp_token',
            field=models.CharField(max_length=56, null=True, unique=True),
        ),
    ]
