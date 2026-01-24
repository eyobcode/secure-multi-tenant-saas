from django.core.management.base import BaseCommand
from typing import Any
from subscriptions import utils as sub_utils


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear-dangling",
            action="store_true",
            default=False,
        )
    def handle(self, *args: Any, **options: Any):
        if options.get("clear_dangling"):
            sub_utils.clear_dangling_subs()
