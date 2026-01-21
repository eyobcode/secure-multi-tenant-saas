from django.db import models
from django.conf import settings
import helpers.billing

User = settings.AUTH_USER_MODEL


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    init_email = models.EmailField(blank=True, null=True)
    init_email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def create_stripe_customer(self):
        """
        Explicit Stripe customer creation.
        Safe to call multiple times.
        """
        if self.stripe_id:
            return self.stripe_id

        if not self.init_email_confirmed or not self.init_email:
            return None

        stripe_id = helpers.billing.create_customer(
            email=self.init_email,
            metadata={
                "user_id": self.user.id,
                "username": self.user.username,
            },
            raw=False,
        )

        self.stripe_id = stripe_id
        self.save(update_fields=["stripe_id"])
        return stripe_id
