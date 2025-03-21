# Generated by Django 5.1.4 on 2025-03-19 06:32

import django.contrib.auth.models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('Greater Accra', 'Greater Accra'), ('Western', 'Western'), ('Ashanti', 'Ashanti'), ('Eastern', 'Eastern'), ('Central', 'Central'), ('Volta', 'Volta'), ('Northern', 'Northern'), ('Western North', 'Western North'), ('Oti', 'Oti'), ('Ahafo', 'Ahafo'), ('Bono', 'Bono'), ('Bono East', 'Bono East'), ('Upper East', 'Upper East'), ('Upper West', 'Upper West'), ('North East', 'North East')], max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='MyUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('username', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('nss_id', models.CharField(max_length=50, unique=True)),
                ('ghana_card', models.CharField(max_length=50, unique=True)),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female')], max_length=10)),
                ('date_of_birth', models.CharField(max_length=10)),
                ('assigned_institution', models.CharField(max_length=255)),
                ('start_date', models.CharField(max_length=10)),
                ('end_date', models.CharField(max_length=10)),
                ('phone', models.CharField(max_length=10)),
                ('resident_address', models.CharField(max_length=255)),
                ('groups', models.ManyToManyField(blank=True, related_name='myuser_set', to='auth.group')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='myuser_permissions_set', to='auth.permission')),
                ('region_of_posting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posted_users', to='digital360Api.region')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='OTPVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp_code', models.CharField(default='f3463a', max_length=6)),
                ('is_used', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otps', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UploadPDF',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_name', models.CharField(default='Untitled', max_length=30)),
                ('file', models.FileField(upload_to='documents/')),
                ('signature_image', models.ImageField(blank=True, null=True, upload_to='signatures/')),
                ('signature_drawing', models.TextField(blank=True, null=True)),
                ('is_signed', models.BooleanField(default=False)),
                ('signed_file', models.FileField(blank=True, null=True, upload_to='signed_docs/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
