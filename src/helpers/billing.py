import stripe
from decouple import config

DJANGO_DEBUG=config("DJANGO_DEBUG", default=False, cast=bool)
STRIPE_SECRET_KEY=config("STRIPE_SECRET_KEY", default="", cast=str)

if "sk_test" in STRIPE_SECRET_KEY and not DJANGO_DEBUG:
    raise ValueError("Invalid stripe ke for production.")


stripe.api_key = STRIPE_SECRET_KEY

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
    return res if raw else res.id
