from django.core.management.base import BaseCommand
from customers.models import Customer
import helpers.billing
from subscriptions.models import UserSubscriptions


class Command(BaseCommand):
    help = "Sync subscription permissions to groups"

    def handle(self, *args, **options):
        qs = Customer.objects.filter(stripe_id__isnull=False)

        for obj in qs:
            user = obj.user
            customer_stripe_id = obj.stripe_id
            self.stdout.write(
                self.style.SUCCESS(
                    f"Synced {user} → {customer_stripe_id} subs and remove old ones."
                )
            )
            res = helpers.billing.get_customer_active_subscriptions(customer_stripe_id)
            for r in res:
                existing_user_sub_qs = UserSubscriptions.objects.filter(stripe_id__iexact=f"{r.id}".strip())
                if existing_user_sub_qs.exists():
                    continue
                print(r.id,"===> ",existing_user_sub_qs.exists())
