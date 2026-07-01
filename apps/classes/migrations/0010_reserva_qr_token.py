import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0009_alter_certificadomedico_imagen'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='qr_token',
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name='Token de QR',
            ),
        ),
    ]