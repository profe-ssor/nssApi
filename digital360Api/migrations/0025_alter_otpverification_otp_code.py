# Generated by Django 5.2.1 on 2025-06-17 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digital360Api', '0024_alter_otpverification_otp_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otpverification',
            name='otp_code',
            field=models.CharField(default='442cba', max_length=6),
        ),
    ]
