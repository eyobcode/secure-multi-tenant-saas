from allauth.account.signals import (
    user_signed_up as allauth_user_signed_up,
    email_confirmed as allauth_email_confirmed,
)
from django.dispatch import receiver
from .models import Customer


@receiver(allauth_user_signed_up)
def allauth_user_signed_up_handler(request, user, *args, **kwargs):
    """
    Create Customer object immediately on signup.
    Stripe customer is NOT created yet.
    """
    Customer.objects.get_or_create(
        user=user,
        defaults={
            "init_email": user.email,
            "init_email_confirmed": False,
        },
    )


@receiver(allauth_email_confirmed)
def allauth_email_confirmed_handler(request, email_address, *args, **kwargs):
    """
    When email is confirmed, mark it confirmed
    and explicitly create Stripe customer.
    """
    qs = Customer.objects.filter(
        init_email=email_address.email,
        init_email_confirmed=False,
    )

    for customer in qs:
        customer.init_email_confirmed = True
        customer.save(update_fields=["init_email_confirmed"])
        customer.create_stripe_customer()
