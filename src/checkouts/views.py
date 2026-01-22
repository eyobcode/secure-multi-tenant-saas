from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import helpers.billing
from subscriptions.models import SubscriptionsPrice
from django.conf import settings


def product_price_redirect_view(request, price_id=None, *args, **kwargs):
    request.session['checkout_subscription_price_id'] = price_id
    return redirect("/checkout/start/")


@login_required
def checkout_redirect_view(request):
    # 1. Validate session price ID
    price_id = request.session.get("checkout_subscription_price_id")
    if not price_id:
        return redirect("pricing")

    # 2. Fetch price object safely
    try:
        price_obj = SubscriptionsPrice.objects.get(id=price_id)
    except SubscriptionsPrice.DoesNotExist:
        return redirect("pricing")

    # 3. Ensure customer + stripe_id exists
    customer = request.user.customer
    if not customer.stripe_id:
        customer.create_stripe_customer()

    if not customer.stripe_id:
        # Stripe customer creation failed
        return redirect("pricing")

    # 4. Build URLs
    base_url = settings.BASE_URL
    success_url = f"{base_url}{reverse('stripe-checkout-end')}"
    cancel_url = f"{base_url}{reverse('pricing')}"

    # 5. Create Stripe checkout session
    checkout_url = helpers.billing.start_checkout_session(
        customer_id=customer.stripe_id,
        success_url=success_url,
        cancel_url=cancel_url,
        price_stripe_id=price_obj.stripe_id,
        raw=False,
        # return_url=
    )

    # 6. Redirect user to Stripe
    return redirect(checkout_url)


@login_required
def checkout_finalize_view(request):
    checkout_subscription_price_id = request.session.get(
        "checkout_subscription_price_id"
    )

    if checkout_subscription_price_id is None:
        return redirect("/pricing")

    customer_stripe_id = request.user.customer.stripe_id

    # continue Stripesu logic here
    return redirect("/success")
