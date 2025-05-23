# Generated by Django 5.1.4 on 2025-04-27 14:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('nss_supervisors', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Administrator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('admin_name', models.CharField(max_length=255)),
                ('ghana_card_record', models.CharField(max_length=20)),
                ('contact', models.CharField(max_length=20)),
                ('assigned_supervisors', models.ManyToManyField(related_name='managed_by_admin', to='nss_supervisors.supervisor')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='administrator_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
