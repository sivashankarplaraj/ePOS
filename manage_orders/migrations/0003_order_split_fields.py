from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manage_orders', '0002_order_completed_at_order_status'),
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
