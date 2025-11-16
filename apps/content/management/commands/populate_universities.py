"""
Management command to populate universities from API or static data.
"""
from django.core.management.base import BaseCommand
from apps.content.models import University
import requests
import json


class Command(BaseCommand):
    help = 'Populate universities in Lazio region from API or static data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-url',
            type=str,
            help='API URL to fetch universities from',
            default=None,
        )
        parser.add_argument(
            '--use-static',
            action='store_true',
            help='Use static data for Lazio universities instead of API',
        )

    def handle(self, *args, **options):
        """Main command handler."""
        if options['use_static'] or not options['api_url']:
            self.populate_from_static_data()
        else:
            self.populate_from_api(options['api_url'])

    def populate_from_static_data(self):
        """Populate universities with known Lazio region universities."""
        self.stdout.write('Populating universities from static data...')
        
        # Known universities in Lazio region
        universities_data = [
            {
                'name': 'Sapienza University of Rome',
                'url': 'https://www.uniroma1.it',
                'location': 'Rome',
                'description': 'La Sapienza is the largest university in Europe and one of the oldest universities in the world.',
            },
            {
                'name': 'University of Rome Tor Vergata',
                'url': 'https://www.uniroma2.it',
                'location': 'Rome',
                'description': 'A public research university located in Rome, Italy.',
            },
            {
                'name': 'University of Rome Tre',
                'url': 'https://www.uniroma3.it',
                'location': 'Rome',
                'description': 'A public research university in Rome, Italy.',
            },
            {
                'name': 'Foro Italico University',
                'url': 'https://www.uniroma4.it',
                'location': 'Rome',
                'description': 'University of Sport and Movement Sciences.',
            },
            {
                'name': 'LUISS Guido Carli',
                'url': 'https://www.luiss.edu',
                'location': 'Rome',
                'description': 'Libera Università Internazionale degli Studi Sociali Guido Carli.',
            },
            {
                'name': 'University of Cassino and Southern Lazio',
                'url': 'https://www.unicas.it',
                'location': 'Cassino',
                'description': 'Public university in Cassino, Lazio region.',
            },
            {
                'name': 'University of Tuscia',
                'url': 'https://www.unitus.it',
                'location': 'Viterbo',
                'description': 'Public university located in Viterbo, Lazio.',
            },
            {
                'name': 'Tor Vergata University of Rome',
                'url': 'https://web.uniroma2.it',
                'location': 'Rome',
                'description': 'Second largest university in Rome.',
            },
            {
                'name': 'LUMSA University',
                'url': 'https://www.lumsa.it',
                'location': 'Rome',
                'description': 'Libera Università Maria SS. Assunta.',
            },
            {
                'name': 'Campus Bio-Medico University of Rome',
                'url': 'https://www.unicampus.it',
                'location': 'Rome',
                'description': 'Private university focused on medicine and biomedical sciences.',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for uni_data in universities_data:
            university, created = University.objects.update_or_create(
                name=uni_data['name'],
                defaults={
                    'url': uni_data.get('url', ''),
                    'location': uni_data.get('location', ''),
                    'description': uni_data.get('description', ''),
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {university.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated: {university.name}'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully populated universities: {created_count} created, {updated_count} updated'
            )
        )

    def populate_from_api(self, api_url):
        """Populate universities from an API."""
        self.stdout.write(f'Fetching universities from API: {api_url}')
        
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Adapt this based on your API response structure
            # Example structure:
            # [
            #     {
            #         "name": "University Name",
            #         "url": "https://...",
            #         "location": "City",
            #         "description": "..."
            #     }
            # ]
            
            created_count = 0
            updated_count = 0
            
            for item in data:
                university, created = University.objects.update_or_create(
                    name=item.get('name', ''),
                    defaults={
                        'url': item.get('url', ''),
                        'location': item.get('location', ''),
                        'description': item.get('description', ''),
                        'is_active': True,
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully fetched from API: {created_count} created, {updated_count} updated'
                )
            )
            
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'Error fetching from API: {e}')
            )
            self.stdout.write(self.style.WARNING('Falling back to static data...'))
            self.populate_from_static_data()

