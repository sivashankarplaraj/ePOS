from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manage_orders', '0011_alter_order_band_co_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='split_cash_pence',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='order',
            name='split_card_pence',
            field=models.IntegerField(default=0),
        ),
    ]
