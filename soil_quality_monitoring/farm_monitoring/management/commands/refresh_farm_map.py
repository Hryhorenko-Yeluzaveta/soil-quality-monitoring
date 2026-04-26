from django.core.management.base import BaseCommand

from farm_monitoring.services.farm_map_image import _cache_path, _download


class Command(BaseCommand):
    help = 'Force re-download the farm satellite map image from Google Static Maps API.'

    def handle(self, *args, **options):
        target = _cache_path()
        if target.exists():
            target.unlink()
            self.stdout.write(f'Removed cached image: {target}')

        if _download(target):
            self.stdout.write(self.style.SUCCESS(f'Successfully downloaded: {target}'))
        else:
            self.stdout.write(self.style.ERROR('Failed to download farm map. Check logs.'))
