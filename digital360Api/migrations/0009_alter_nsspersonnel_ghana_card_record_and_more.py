# Generated by Django 5.1.4 on 2025-03-28 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digital360Api', '0008_remove_nsspersonnel_contact_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nsspersonnel',
            name='ghana_card_record',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='otpverification',
            name='otp_code',
            field=models.CharField(default='a9ef5f', max_length=6),
        ),
    ]
