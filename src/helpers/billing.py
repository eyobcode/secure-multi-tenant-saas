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

def create_product(
        raw=False,
        name="",
        metadata={}):
    product = stripe.Product.create(
        name=name,
        metadata=metadata,
    )
    if raw:
        return product
    return product.id

def create_price(currency="usd",unit_amount="9999",
                 interval = 'month',raw=False,
                 metadata={},product=None):
    if product is None:
        return None
    price = stripe.Price.create(currency=currency,
                                  unit_amount=unit_amount,
                                  recurring={'interval':interval},
                                  metadata=metadata,
                                  product=product)
    if raw:
        return price
    return price.id