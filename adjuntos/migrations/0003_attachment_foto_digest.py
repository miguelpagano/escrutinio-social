# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-08 03:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adjuntos', '0002_attachment_mesa'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='foto_digest',
            field=models.CharField(default='000', max_length=128, unique=True),
            preserve_default=False,
        ),
    ]
