from django.contrib import admin

from prepaid_mate.models import Account, Drink, MoneyLog


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'view_saldo',
    )

    @admin.display(empty_value='0.00€', description='saldo')
    def view_saldo(self, obj):
        return f'{obj.saldo/100:1.2f}€'


@admin.register(Drink)
class DrinkAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'content_ml',
        'view_price',
    )

    @admin.display(empty_value='0.00€', description='price')
    def view_price(self, obj):
        return f'{obj.price/100:1.2f}€'


@admin.register(MoneyLog)
class MoneyLogAdmin(admin.ModelAdmin):
    list_display = (
        'account',
        'amount',
        'timestamp',
    )
