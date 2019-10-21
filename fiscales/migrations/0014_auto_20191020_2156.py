# Generated by Django 2.2.2 on 2019-10-21 00:56

from django.db import migrations
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('fiscales', '0013_fiscal_distrito_afin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fiscal',
            name='estado',
            field=model_utils.fields.StatusField(choices=[(0, 'dummy')], default='PREINSCRIPTO', max_length=100, no_check_for_status=True),
        ),
    ]
