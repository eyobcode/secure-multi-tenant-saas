from django.contrib import admin
from .models import Subscriptions, UserSubscriptions, SubscriptionsPrice


class SubscriptionPrice(admin.TabularInline):
    model = SubscriptionsPrice
    readonly_fields = ['stripe_id']
    can_delete = False
    extra = 0


class SubscriptionAdmin(admin.ModelAdmin):
    inlines = [SubscriptionPrice]
    list_display = ['name', 'active']


admin.site.register(Subscriptions, SubscriptionAdmin)
admin.site.register(UserSubscriptions)
