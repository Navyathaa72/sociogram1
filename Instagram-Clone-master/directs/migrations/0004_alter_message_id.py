# Generated by Django 5.2 on 2025-05-06 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directs', '0003_auto_20220213_2344'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
