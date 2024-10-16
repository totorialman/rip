# Generated by Django 4.2.4 on 2024-10-16 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0002_alter_vmachine_request_from_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='vmachine_request',
            name='final_price',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name='Итоговая цена'),
        ),
    ]