# Generated by Django 5.1.4 on 2025-05-05 14:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('messageApp', '0002_message_attachment_pdf'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='attachment_pdf',
        ),
    ]
