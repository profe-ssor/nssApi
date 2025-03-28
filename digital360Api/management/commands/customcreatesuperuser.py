from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from digital360Api.models import Region, Administrator, Supervisor, GhanaCardRecord

class Command(BaseCommand):
    help = 'Create an Administrator or Supervisor user'

    def handle(self, *args, **options):
        User = get_user_model()

        self.stdout.write(self.style.NOTICE('==== CREATE USER Administrator ===='))
        
        # Get user inputs
        email = input('Email: ').strip()
        username = input('Username: ').strip()
        gender = input('Gender (M/F): ').strip().upper()
        password = input('Password: ').strip()
        full_name = input('Full Name: ').strip()
        ghana_card = input('Ghana Card Number: ').strip()
        contact = input('Contact Number: ').strip()
        date_of_birth = input('Date of Birth (YYYY-MM-DD): ').strip()
        user_type = input("Enter user type (admin/staff): ").strip().lower()

        if user_type not in ["admin", "staff"]:
            self.stdout.write(self.style.ERROR('Invalid user type! Choose "admin" or "staff".'))
            return

        # Validate user existence
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR('User with this email already exists.'))
            return

        # Show available regions
        regions = Region.objects.all()
        self.stdout.write('\nAvailable Regions:')
        for region in regions:
            self.stdout.write(f'{region.id}: {region.name}')
        
        region_id = input('\nSelect Region ID for this user: ').strip()
        
        try:
            region_id = int(region_id)
            region = Region.objects.get(id=region_id)
        except ValueError:
            self.stdout.write(self.style.ERROR('Invalid input! Region ID must be a number.'))
            return
        except Region.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Region with ID {region_id} does not exist.'))
            return

        try:
            with transaction.atomic():
                # Get or create Ghana Card record
                ghana_card_record, created = GhanaCardRecord.objects.get_or_create(
                    ghana_card_number=ghana_card,
                    defaults={
                        'full_name': full_name,
                        'date_of_birth': date_of_birth,
                        'nationality': 'Ghanaian',
                        'contact_number': contact,
                        'email': email,
                        'address': 'N/A'
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created new Ghana Card record for {full_name}'))

                # Create the user
                user = User.objects.create_user(
                    email=email,
                    gender=gender,
                    username=username,
                    password=password,
                    user_type=user_type,
                )

                # Explicitly set and save `is_staff`
                user.is_staff = (user_type == "staff")
                user.save()

                if user_type == "admin":
                    Administrator.objects.create(
                        user=user,
                        name=full_name,
                        ghana_card_record=ghana_card_record,
                        contact=contact,
                   
                    )
                    self.stdout.write(self.style.SUCCESS(f'Administrator {username} created successfully!'))
                else:
                    Supervisor.objects.create(
                        user=user,
                        full_name=full_name,
                        ghana_card_record=ghana_card_record,
                        contact=contact,
                       
                        assigned_region=region
                    )
                    self.stdout.write(self.style.SUCCESS(f'Supervisor {username} created successfully!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating user: {str(e)}'))
