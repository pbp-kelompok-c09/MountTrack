
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0002_remove_booking_gunung_delete_gunung'),
        ('list_gunung', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='gunung',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='list_gunung.mountain'),
        ),
    ]
