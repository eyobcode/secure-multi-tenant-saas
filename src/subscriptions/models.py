from django.db import models
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import settings

from django.db.models.signals import post_save
from django.dispatch import receiver

User = settings.AUTH_USER_MODEL
ALLOW_CUSTOM_USER = True


SUBSCRIPTIONS_PERMISSIONS = [
    ("advanced", "Advanced Per"),
    ("pro", "Pro Per"),
    ("basic", "Basic Per")
]


class Subscriptions(models.Model):
    name = models.CharField(max_length=120)
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group)
    permissions = models.ManyToManyField(Permission,
                                             limit_choices_to = {
                                                 "content_type__app_label": "subscriptions",
                                                 "codename__in": [x[0] for x in SUBSCRIPTIONS_PERMISSIONS]
                                             }
                                         )
    class Meta:
        permissions = SUBSCRIPTIONS_PERMISSIONS

    def __str__(self):
        return self.name


class UserSubscriptions(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscriptions, on_delete=models.SET_NULL, blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} - {self.subscription}" if self.subscription else str(self.user)



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
        subs_qs = Subscription.objects.filter(active=True)
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

