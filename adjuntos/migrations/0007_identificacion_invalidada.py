# Generated by Django 2.2.2 on 2019-07-19 18:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adjuntos', '0006_auto_20190716_1301'),
    ]

    operations = [
        migrations.AddField(
            model_name='identificacion',
            name='invalidada',
            field=models.BooleanField(default=False),
        ),
    ]
