# Generated by Django 2.2.2 on 2019-09-07 23:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0057_auto_20190901_1444'),
        ('scheduling', '0002_auto_20190801_1943'),
    ]

    operations = [
        migrations.CreateModel(
            name='ColaCargaPendientes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.PositiveIntegerField(db_index=True)),
                ('carga_parcial', models.BooleanField(default=False)),
                ('mesaCategoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elecciones.MesaCategoria')),
            ],
        ),
    ]
