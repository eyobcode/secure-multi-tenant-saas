from customers.models import Customer
import helpers.billing
from subscriptions.models import UserSubscriptions,Subscriptions


def clear_dangling_subs():
    qs = Customer.objects.filter(stripe_id__isnull=False)

    for obj in qs:
        user = obj.user
        customer_stripe_id = obj.stripe_id
        print(f"Synced {user} → {customer_stripe_id} subs and remove old ones.")
        res = helpers.billing.get_customer_active_subscriptions(customer_stripe_id)
        for sub in res:
            existing_user_sub_qs = UserSubscriptions.objects.filter(stripe_id__iexact=f"{sub.id}".strip())
            if existing_user_sub_qs.exists():
                continue
            helpers.billing.cancel_subscription(
                sub.id,
                reason="Dangling active subscription.",
                cancel_at_period_end=False)


def sync_subs_group_permissions():
    qs = Subscriptions.objects.filter(active=True).prefetch_related(
        "groups",
        "permissions",
    )
    for obj in qs:
        groups = obj.groups.all()
        permissions = obj.permissions.all()

        for group in groups:
            group.permissions.set(permissions)

        print(f"Synced {obj.name} → "
              f"{len(groups)} groups, {len(permissions)} permissions")
