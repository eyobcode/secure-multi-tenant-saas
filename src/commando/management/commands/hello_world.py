from django.core.management import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        print('This is the base command for commando management commands.')