# Generated by Django 5.2.1 on 2025-07-18 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nss_personnel', '0003_archivednsspersonnel'),
    ]

    operations = [
        migrations.AddField(
            model_name='archivednsspersonnel',
            name='restored_once',
            field=models.BooleanField(default=False),
        ),
    ]
