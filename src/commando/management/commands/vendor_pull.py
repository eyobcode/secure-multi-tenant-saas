from django.core.management import BaseCommand
from django.conf import settings
import helpers


VENDOR_ASSETS_PATHS = {
    "flowbite.min.css":"https://cdn.jsdelivr.net/npm/flowbite@4.0.1/dist/flowbite.min.css",
    "flowbite.min.js":"https://cdn.jsdelivr.net/npm/flowbite@4.0.1/dist/flowbite.min.js",
    "flowbite.min.js.map":"https://cdn.jsdelivr.net/npm/flowbite@4.0.1/dist/flowbite.min.js.map",
}

STATICFILES_VENDOR_DIR = getattr(settings, 'STATICFILES_VENDOR_DIR')

class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write('Pulling vendor assets...')
        completed_url = []
        for filename, url in VENDOR_ASSETS_PATHS.items():
            dl_path = STATICFILES_VENDOR_DIR / filename
            dl_success = helpers.download_file_to_local(url=url,local_path=dl_path)
            if dl_success:
                completed_url.append(url)
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to download {url} to {dl_path}')
                )
        if set(completed_url) == set(VENDOR_ASSETS_PATHS.values()):
            self.stdout.write(
                self.style.SUCCESS('All vendor assets updated successfully.')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Some vendor assets failed to update.')
            )
