# Generated by Django 5.1.4 on 2025-03-27 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digital360Api', '0006_alter_otpverification_otp_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='nsspersonnel',
            name='nss_id',
            field=models.CharField(default='nss_id', max_length=25),
        ),
        migrations.AlterField(
            model_name='otpverification',
            name='otp_code',
            field=models.CharField(default='47a705', max_length=6),
        ),
    ]
