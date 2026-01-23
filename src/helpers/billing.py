import stripe
from decouple import config
from . import date_utils

DJANGO_DEBUG=config("DJANGO_DEBUG", default=False, cast=bool)
STRIPE_SECRET_KEY=config("STRIPE_SECRET_KEY", default="", cast=str)

if "sk_test" in STRIPE_SECRET_KEY and not DJANGO_DEBUG:
    raise ValueError("Invalid stripe ke for production.")


stripe.api_key = STRIPE_SECRET_KEY


def serialize_subscription_data(subscription_response):
    status = subscription_response.status
    cancel_at_period_end = subscription_response.cancel_at_period_end

    item = subscription_response["items"]["data"][0]

    current_period_start = date_utils.timestamp_as_datetime(
        item.get("current_period_start")
    )
    current_period_end = date_utils.timestamp_as_datetime(
        item.get("current_period_end")
    )

    return {
        "current_period_start": current_period_start,
        "current_period_end": current_period_end,
        "status": status,
        "cancel_at_period_end": cancel_at_period_end,
    }




def create_customer(raw=False, name="", email="",metadata={}):
    customer = stripe.Customer.create(
        name=name,
        email=email,
        metadata=metadata,
    )
    if raw:
        return customer
    return customer.id

def create_product(raw=False,name="",metadata={}):
    product = stripe.Product.create(
        name=name,
        metadata=metadata,
    )
    if raw:
        return product
    return product.id

def create_price(currency="usd",unit_amount="9999",interval = 'month',raw=False,metadata={},product=None):
    if product is None:
        return None
    price = stripe.Price.create(currency=currency,unit_amount=unit_amount,recurring={'interval':interval},
                                metadata=metadata,
                                product=product)
    if raw:
        return price
    return price.id

def start_checkout_session(
        customer_id,
        success_url,
        cancel_url,
        # return_url,
        price_stripe_id,
        mode="subscription",
        raw=False,
):
    """
    Creates a Stripe Checkout Session and returns
    either the full session object or redirect URL.
    """

    if not success_url.endswith("?session_id={CHECKOUT_SESSION_ID}"):
        success_url = f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}"

    session = stripe.checkout.Session.create(
        customer=customer_id,
        success_url=success_url,
        cancel_url=cancel_url,
        # return_url=return_url,
        line_items=[
            {
                "price": price_stripe_id,
                "quantity": 1,
            }
        ],
        mode=mode,
    )
    if raw:
        return session

    return session.url
def get_checkout_session(session_id, raw=False):
    res = stripe.checkout.Session.retrieve(session_id)
    return res if raw else res.url

def get_subscription(stripe_id, raw=False):
    res = stripe.Subscription.retrieve(stripe_id)
    return serialize_subscription_data(res) if raw else res.id

def cancel_subscription(
        stripe_id,
        cancel_at_period_end=False,
        reason="",
        feedback="other",
        raw=False
):
    if cancel_at_period_end:
        # Cancel at period end
        res = stripe.Subscription.modify(
            stripe_id,
            cancel_at_period_end=cancel_at_period_end,
            cancellation_details={
                "comment": reason,
                "feedback": feedback
            }
        )
    else:
        # Cancel immediately
        res = stripe.Subscription.cancel(
            stripe_id,
            cancellation_details={
                "comment": reason,
                "feedback": feedback
            }
        )
    return serialize_subscription_data(res)


def get_checkout_customer_plan(session_id):
    checkout_r = get_checkout_session(session_id, raw=True)

    customer_id = checkout_r.customer
    sub_stripe_id = checkout_r.subscription

    sub_r = get_subscription(sub_stripe_id, raw=True)

    sub_plan = sub_r["items"]["data"][0]["plan"]

    subscription_data = serialize_subscription_data(sub_r)

    data = {
        "customer_id": customer_id,
        "plan_id": sub_plan.id,
        "sub_stripe_id": sub_stripe_id,
        **subscription_data,
    }
    return data

