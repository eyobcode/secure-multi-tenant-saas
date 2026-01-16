from django.core.management.base import BaseCommand
from subscriptions.models import Subscriptions


class Command(BaseCommand):
    help = "Sync subscription permissions to groups"

    def handle(self, *args, **options):
        qs = Subscriptions.objects.filter(active=True).prefetch_related(
            "groups",
            "permissions",
        )

        for obj in qs:
            groups = obj.groups.all()
            permissions = obj.permissions.all()

            for group in groups:
                group.permissions.set(permissions)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Synced {obj.name} → "
                    f"{len(groups)} groups, {len(permissions)} permissions"
                )
            )
