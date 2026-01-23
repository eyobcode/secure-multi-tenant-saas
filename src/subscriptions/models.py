from django.db import models
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import settings
import helpers.billing

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

User = settings.AUTH_USER_MODEL
ALLOW_CUSTOM_GROUPS = True


SUBSCRIPTIONS_PERMISSIONS = [
    ("advanced", "Advanced Per"),
    ("pro", "Pro Per"),
    ("basic", "Basic Per")
]


class Subscriptions(models.Model):
    """
    Subscriptions Plan = Stripe Product
    """
    name = models.CharField(max_length=120)
    subtitle = models.CharField(null=True,blank=True)
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group)
    permissions = models.ManyToManyField(
        Permission,
        limit_choices_to = {
            "content_type__app_label": "subscriptions",
            "codename__in": [x[0] for x in SUBSCRIPTIONS_PERMISSIONS]
        })
    stripe_id = models.CharField(max_length=150,null=True,blank=True)
    order = models.IntegerField(default=-1)
    featured = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    features = models.TextField(null=True, blank=True,help_text="Features for pricing, separated by new line.")


    class Meta:
        ordering = ["order","featured", "-updated"]
        permissions = SUBSCRIPTIONS_PERMISSIONS

    def get_features_as_list(self):
        if not self.features:
            return []
        return [x.strip() for x in self.features.split("\n")]

    def save(self,*args, **kwargs):
        if not self.stripe_id:
            self.stripe_id = helpers.billing.create_product(
                raw=False,
                name=self.name,
                metadata={"subscription_plan_id": self.id},
            )
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name

class SubscriptionsPrice(models.Model):
    """
    Subscriptions Price = Stripe Price
    """
    class IntervalChoices(models.TextChoices):
        MONTHLY = 'month', 'Monthly'
        YEARLY = 'year', 'Yearly'

    subscription = models.ForeignKey(Subscriptions,on_delete=models.SET_NULL,null=True,blank=True)
    stripe_id = models.CharField(max_length=150,null=True,blank=True)
    interval = models.CharField(max_length=10, choices=IntervalChoices, default=IntervalChoices.MONTHLY)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=99.99)
    order = models.IntegerField(default=-1)
    featured = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["subscription__order","order","featured", "-updated"]
    @property
    def display_features_list(self):
        if not self.subscription:
            return []
        return self.subscription.get_features_as_list()

    @property
    def stripe_currency(self):
        return "usd"
    @property
    def stripe_price(self):
        # remove decimal place
        return int(self.price * 100)

    @property
    def product_stripe_id(self):
        if not self.subscription:
            return None
        return self.subscription.stripe_id

    @property
    def get_checkout_url(self):
        return reverse("sub-price-checkout",kwargs={"price_id": self.id})

    def save(self,*args, **kwargs):
        if not self.stripe_id and self.product_stripe_id is not None:
            stripe_id = helpers.billing.create_price(
                currency=self.stripe_currency,
                unit_amount=self.stripe_price,
                interval=self.interval,
                metadata={"subscription_plan_price_id": self.id},
                product=self.product_stripe_id,
                raw=False
            )
            self.stripe_id = stripe_id

        super().save(*args, **kwargs)
        if self.featured and self.subscription:
            qs = SubscriptionsPrice.objects.filter(
                subscription=self.subscription,
                interval=self.interval
            ).exclude(id=self.id)
            qs.update(featured=False)

    @property
    def display_sub_name(self):
        if not self.subscription:
            return "Plan"
        return self.subscription.name

    @property
    def display_sub_subtitle(self):
        if not self.subscription:
            return "Plan"
        return self.subscription.subtitle

class SubscriptionStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    TRIALING = 'trialing', 'Trialing'
    INCOMPLETE = 'incomplete', 'Incomplete'
    INCOMPLETE_EXPIRED = 'incomplete_expired', 'Incomplete Expired'
    PAST_DUE = 'past_due', 'Past Due'
    CANCELED = 'canceled', 'Canceled'
    UNPAID = 'unpaid', 'Unpaid'
    PAUSED = 'paused', 'Paused'

class UserSubscriptions(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscriptions, on_delete=models.SET_NULL, blank=True, null=True)
    stripe_id = models.CharField(max_length=150,null=True,blank=True)
    active = models.BooleanField(default=True)
    user_cancelled = models.BooleanField(default=False)
    original_period_start = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    cancel_at_period_end = models.BooleanField(default=False)
    current_period_start = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    current_period_end = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, null=True, blank=True)

    @property
    def is_active_status(self):
        return self.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING
        ]
    @property
    def plan_name(self):
        if not self.subscription:
            return None
        return self.subscription.name

    def serializer(self):
        return {
            "plan_name":self.plan_name,
            "current_period_start":self.current_period_start,
            "current_period_end":self.current_period_end,
            "status": self.status
        }


    def __str__(self):
            return f"{self.user} - {self.subscription}" if self.subscription else str(self.user)

    def save(self, *args, **kwargs):
        if self.original_period_start is None and self.current_period_start is not None:
            self.original_period_start = self.current_period_start
        super().save(*args, **kwargs)

    # @property
    # def billing_cycle_anchor(self):
    #     """
    #     https://docs.stripe.com/payments/checkout/billing-cycle
    #     Optional delay to start new subscription in
    #     Stripe checkout
    #     """
    #     if not self.current_period_end:
    #         return None
    #     return int(self.current_period_end.timestamp())

    def get_absolute_url(self):
        return reverse("user_subscription")

    def get_cancel_url(self):
        return reverse("user_subscription_cancel")




@receiver(post_save, sender=UserSubscriptions)
def user_sub_post_save(sender, instance, **kwargs):
    if not instance.subscription:
        return

    user_sub_instance = instance
    user = user_sub_instance.user
    subscription_obj = user_sub_instance.subscription
    groups_ids = []
    if subscription_obj is not None:
        groups = subscription_obj.groups.all()
        groups_ids = groups.values_list('id', flat=True)
    if not ALLOW_CUSTOM_GROUPS:
        user.groups.set(groups_ids)
    else:
        subs_qs = Subscriptions.objects.filter(active=True)
        if subscription_obj is not None:
            subs_qs = subs_qs.exclude(id=subscription_obj.id)
        subs_groups = subs_qs.values_list("groups__id", flat=True)
        subs_groups_set = set(subs_groups)
        # groups_ids = groups.values_list('id', flat=True) # [1, 2, 3]
        current_groups = user.groups.all().values_list('id', flat=True)
        groups_ids_set = set(groups_ids)
        current_groups_set = set(current_groups) - subs_groups_set
        final_group_ids = list(groups_ids_set | current_groups_set)
        user.groups.set(final_group_ids)

