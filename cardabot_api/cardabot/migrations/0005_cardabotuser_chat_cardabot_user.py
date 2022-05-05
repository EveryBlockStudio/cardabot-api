# Generated by Django 4.0.3 on 2022-05-04 01:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cardabot', '0004_alter_chat_default_language'),
    ]

    operations = [
        migrations.CreateModel(
            name='CardaBotUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stake_key', models.CharField(max_length=256)),
            ],
        ),
        migrations.AddField(
            model_name='chat',
            name='cardabot_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='cardabot.cardabotuser'),
        ),
    ]
