from django.core.management.base import BaseCommand
from typing import Any
from subscriptions import utils as sync_subs

class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any):
        sync_subs.sync_subs_group_permissions()

