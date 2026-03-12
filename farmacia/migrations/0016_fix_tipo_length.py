from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('farmacia', '0015_increase_tipo_length'),  # Depende de la migración anterior
    ]

    operations = [
        migrations.AlterField(
            model_name='movimientoinventario',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('ENTRADA', 'Entrada'),
                    ('SALIDA', 'Salida'),
                    ('COMPRA', 'Compra'),
                    ('VENTA', 'Venta'),
                    ('AJUSTE_POSITIVO', 'Ajuste +'),
                    ('AJUSTE_NEGATIVO', 'Ajuste -'),
                    ('PERDIDA', 'Pérdida'),
                ],
                max_length=20,
                verbose_name='Tipo de Movimiento'
            ),
        ),
    ]
