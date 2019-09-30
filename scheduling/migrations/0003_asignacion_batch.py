# Generated by Django 2.2.2 on 2019-09-23 13:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('adjuntos', '0014_reemplazo_taken'),
        ('elecciones', '0059_merge_20190910_0847'),
        ('scheduling', '0002_auto_20190801_1943'),
    ]

    operations = [
        migrations.CreateModel(
            name='ColaCargasPendientes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.PositiveIntegerField(db_index=True)),
                ('numero_carga', models.PositiveIntegerField(default=1)),
                ('attachment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='adjuntos.Attachment')),
                ('mesa_categoria', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='elecciones.MesaCategoria')),
            ],
            options={
                'unique_together': {('mesa_categoria', 'numero_carga'), ('attachment', 'numero_carga')},
                'verbose_name': 'Cola de Identificaciones y Cargas pendientes',
                'verbose_name_plural': 'Cola de Identificaciones y Cargas pendientes',
            },
        ),
    ]
