from ctypes import cast
from email.policy import default

import stripe
from decouple import config

DJANGO_DEBUG=config("DJANGO_DEBUG", default=False, cast=bool)
STRIPE_SECRET_KEY=config("STRIPE_SECRET_KEY", default="", cast=str)

if "sk_test" in STRIPE_SECRET_KEY and not DJANGO_DEBUG:
    raise ValueError("Invalid stripe ke for production.")


stripe.api_key = STRIPE_SECRET_KEY

# customer = stripe.Customer.create(
#     name="Jenny Rosen",
#     email="jennyrosen@example.com",
# )