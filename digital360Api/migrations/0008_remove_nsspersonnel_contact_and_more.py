# Generated by Django 5.1.4 on 2025-03-27 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digital360Api', '0007_nsspersonnel_nss_id_alter_otpverification_otp_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='nsspersonnel',
            name='contact',
        ),
        migrations.AlterField(
            model_name='otpverification',
            name='otp_code',
            field=models.CharField(default='c32472', max_length=6),
        ),
    ]
