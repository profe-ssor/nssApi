# digital360Api/management/commands/customcreatesuperuser.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from digital360Api.models import Region

class Command(BaseCommand):
    help = 'Create a superuser with all required fields'
    
    def handle(self, *args, **options):
        User = get_user_model()
        self.stdout.write('Enter the following details to create a superuser:')
        
        # Get user inputs
        email = input('Email: ')
        username = input('Username: ')
        password = input('Password: ')
        nss_id = input('NSS ID: ')
        ghana_card = input('Ghana Card: ')
        gender = input('Gender (M/F): ')
        date_of_birth = input('Date of Birth (YYYY-MM-DD): ')
        assigned_institution = input('Assigned Institution: ')
        start_date = input('Start Date (YYYY-MM-DD): ')
        end_date = input('End Date (YYYY-MM-DD): ')
        phone = input('Phone: ')
        
        # Show available regions
        regions = Region.objects.all()
        self.stdout.write('\nAvailable Regions:')
        for region in regions:
            self.stdout.write(f'{region.id}: {region.name}')
            
        region_id = input('\nSelect Region ID from above: ')
        resident_address = input('Resident Address: ')
        
        try:
            region = Region.objects.get(id=region_id)
            user = User.objects.create_superuser(
                email=email,
                username=username,
                password=password,
                nss_id=nss_id,
                ghana_card=ghana_card,
                gender=gender,
                date_of_birth=date_of_birth,
                assigned_institution=assigned_institution,
                start_date=start_date,
                end_date=end_date,
                phone=phone,
                region_of_posting=region,
                resident_address=resident_address
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser {username} created successfully!'))
        except Region.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Region with ID {region_id} does not exist.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}'))