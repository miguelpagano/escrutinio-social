# Generated by Django 2.2.2 on 2019-10-05 20:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0004_colacargaspendientes_distrito'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='colacargaspendientes',
            index=models.Index(fields=['distrito', 'orden'], name='orden_distrito'),
        ),
    ]
