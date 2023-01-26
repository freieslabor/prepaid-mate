from django.db import models


class Account(models.Model):
    name = models.TextField()
    password_hash = models.TextField(blank=True, null=True)
    barcode = models.TextField(blank=True, null=True)
    saldo = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'accounts'

    def __str__(self):
        return f'{self.name}'


class Drink(models.Model):
    name = models.TextField()
    content_ml = models.IntegerField(blank=True, null=True)
    price = models.IntegerField()
    barcode = models.TextField()

    class Meta:
        managed = False
        db_table = 'drinks'

    def __str__(self):
        return f'{self.name}'


class MoneyLog(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.IntegerField()
    timestamp = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'money_logs'
