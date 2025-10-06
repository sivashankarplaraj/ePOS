from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('manage_orders', '0002_order_completed_at_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='band_co_number',
            field=models.CharField(max_length=4, blank=True, default='', help_text='Channel/company code associated with the selected price band (e.g. SO, JE, DV).'),
        ),
    ]
