# Generated by Django 2.2.2 on 2019-08-05 18:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problemas', '0006_auto_20190722_2251'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportedeproblema',
            name='tipo_de_problema',
            field=models.CharField(choices=[('spam', 'La foto no es ni de un acta ni de un certificado. Parece subida maliciosamente.'), ('ilegible', 'La foto es de un acta pero no la puedo leer con claridad.'), ('falta_foto', 'La parte que es necesario cargar no está entre las fotos presentes.'), ('falta_identificador', 'El sistema no tiene la sección, circuito o mesa. Indicá el dato faltante en la descripción.'), ('falta_lista', 'El sistema no tiene una de las opciones que aparecen en el acta ocertificado. Indicá el dato faltante en la descripción.'), ('otro', 'El problema no encaja en ninguna de las anteriores; describilo en la descripción.')], default='ilegible', max_length=100, null=True),
        ),
    ]
