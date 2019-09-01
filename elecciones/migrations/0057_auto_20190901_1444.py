# Generated by Django 2.2.2 on 2019-09-01 17:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('elecciones', '0056_merge_20190830_1039'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='opcion',
            options={'ordering': ['partido', 'nombre_corto'], 'verbose_name': 'Opción', 'verbose_name_plural': 'Opciones'},
        ),
        migrations.RemoveField(
            model_name='opcion',
            name='orden',
        ),
        migrations.RemoveField(
            model_name='partido',
            name='orden',
        ),
        migrations.AddField(
            model_name='categoria',
            name='distrito',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='elecciones.Distrito'),
        ),
        migrations.AddField(
            model_name='categoria',
            name='seccion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='elecciones.Seccion'),
        ),
        migrations.AddField(
            model_name='categoriaopcion',
            name='orden',
            field=models.PositiveIntegerField(blank=True, help_text='Orden en el acta', null=True),
        ),
        migrations.CreateModel(
            name='CategoriaGeneral',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('eleccion', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='elecciones.Eleccion')),
            ],
        ),
        migrations.AddField(
            model_name='categoria',
            name='categoria_general',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='categorias', to='elecciones.CategoriaGeneral'),
            preserve_default=False,
        ),
    ]
