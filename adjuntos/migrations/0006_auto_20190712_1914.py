# Generated by Django 2.2.1 on 2019-07-12 22:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adjuntos', '0005_auto_20190710_1356'),
    ]

    operations = [
        migrations.AlterField(
            model_name='identificacion',
            name='consolidada',
            field=models.BooleanField(default=False, help_text='una identificación consolidada es aquella que se considera representativa y determina el estado del attachment'),
        ),
    ]
