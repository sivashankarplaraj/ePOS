from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('manage_orders', '0003_order_band_co_number'),
        ('manage_orders', '0004_order_packed_at_alter_order_status'),
    ]

    operations = [
        # Merge migration resolves conflict between parallel 0003/0004 branches.
    ]
