from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
import helpers.billing
from subscriptions.models import SubscriptionsPrice,Subscriptions,UserSubscriptions
from customers.models import Customer
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
    session_id = request.GET.get('session_id')
    if not session_id:
        return HttpResponseBadRequest("No checkout session found")

    checkout_data = helpers.billing.get_checkout_customer_plan(session_id)
    plan_id = checkout_data.pop('plan_id')
    customer_id = checkout_data.pop('customer_id')
    sub_stripe_id = checkout_data.pop("sub_stripe_id")
    subscription_data = {**checkout_data}

    try:
        sub_obj = Subscriptions.objects.get(subscriptionsprice__stripe_id=plan_id)
    except Subscriptions.DoesNotExist:
        return HttpResponseBadRequest("Invalid plan selected")

    try:
        customer_obj = Customer.objects.get(stripe_id=customer_id)
        user_obj = customer_obj.user
    except Customer.DoesNotExist:
        return HttpResponseBadRequest("User not found")

    updated_sub_options = {
        "subscription": sub_obj,
        "stripe_id": sub_stripe_id,
        "user_cancelled": False,
        **subscription_data,
    }

    _user_sub_exists = False
    try:
        _user_sub_obj = UserSubscriptions.objects.get(user=user_obj)
        _user_sub_exists = True
    except UserSubscriptions.DoesNotExist:
        _user_sub_obj = UserSubscriptions.objects.create(
            user=user_obj,
            **updated_sub_options
        )

    if _user_sub_exists:
        old_stripe_id = _user_sub_obj.stripe_id
        if old_stripe_id and old_stripe_id != sub_stripe_id:
            try:
                helpers.billing.cancel_subscription(old_stripe_id, reason="Auto ended, new membership")
            except Exception:
                pass

        for k, v in updated_sub_options.items():
            setattr(_user_sub_obj, k, v)
        _user_sub_obj.save()

        messages.success(request, "Success! Thank you for joining.")
        return redirect(_user_sub_obj.get_absolute_url())

    context = {"subscription": _user_sub_obj, "checkout_data": checkout_data}
    return render(request, "checkout/success.html", context)

