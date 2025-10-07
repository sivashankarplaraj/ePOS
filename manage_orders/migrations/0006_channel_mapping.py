from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manage_orders', '0005_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChannelMapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('band', models.PositiveSmallIntegerField()),
                ('channel_code', models.CharField(help_text='Code incl. fulfilment suffix e.g. JE-D, SO-C', max_length=10)),
                ('co_number', models.CharField(help_text='Short channel/company code persisted on Order', max_length=4)),
                ('active', models.BooleanField(default=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'name'],
                'unique_together': {('channel_code', 'band')},
            },
        ),
    ]
