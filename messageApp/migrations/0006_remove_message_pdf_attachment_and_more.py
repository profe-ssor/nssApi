# Generated by Django 5.1.4 on 2025-05-05 15:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('file_uploads', '0001_initial'),
        ('messageApp', '0005_message_pdf_attachment_alter_message_attachment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='pdf_attachment',
        ),
        migrations.AlterField(
            model_name='message',
            name='attachment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages', to='file_uploads.uploadpdf'),
        ),
    ]
