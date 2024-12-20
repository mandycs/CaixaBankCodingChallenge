import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from decimal import Decimal


class CustomUser(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    email = models.EmailField(unique=True, verbose_name=_("Email"))
    phoneNumber = models.CharField(max_length=15, unique=True, verbose_name=_("Phone Number"))
    address = models.CharField(max_length=255, verbose_name=_("Address"))
    countryCode = models.CharField(max_length=10, verbose_name=_("Country Code"))
    accountNumber = models.CharField(max_length=6, unique=True, verbose_name=_("Account Number"))
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    password_reset_token = models.UUIDField(null=True, blank=True)
    encrypted_pin = models.CharField(max_length=128, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def set_pin(self, raw_pin):
        self.encrypted_pin = make_password(raw_pin)
        self.save()
    
    def check_pin(self, raw_pin):
        return check_password(raw_pin, self.encrypted_pin)

    def save(self, *args, **kwargs):
        if not self.accountNumber:
            while True:
                # Genera un número de cuenta de 6 caracteres único
                new_account_number = uuid.uuid4().hex[:6]
                if not CustomUser.objects.filter(accountNumber=new_account_number).exists():
                    self.accountNumber = new_account_number
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class BankAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='account')
    accountNumber = models.CharField(max_length=6, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Account {self.accountNumber} for {self.user.name}"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("CASH_WITHDRAWAL", "Cash Withdrawal"),
        ("CASH_DEPOSIT", "Cash Deposit"),
        ("CASH_TRANSFER", "Cash Transfer"),
        ("SUBSCRIPTION", "Subscription"),
        ("ASSET_PURCHASE", "Asset Purchase"),
        ("ASSET_SELL", "Asset Sell"),
    ]

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transactionType = models.CharField(choices=TRANSACTION_TYPES, max_length=20)
    transactionDate = models.DateTimeField(default=timezone.now)
    sourceAccount = models.ForeignKey(
        "BankAccount", related_name="outgoingTransactions", on_delete=models.CASCADE
    )
    targetAccount = models.ForeignKey(
        "BankAccount", related_name="incomingTransactions", on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"{self.transactionType} of {self.amount} on {self.transactionDate}"



class UserAsset(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assets")
    assetSymbol = models.CharField(max_length=10)
    quantity = models.DecimalField(max_digits=15, decimal_places=8, default=Decimal('0.0'))
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.0'))

    class Meta:
        unique_together = ('user', 'assetSymbol')

    def __str__(self):
        return f"{self.user}'s holdings of {self.assetSymbol}"

class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interval_seconds = models.IntegerField()
    last_executed = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Subscription for {self.user} every {self.interval_seconds} seconds"


class AutoInvest(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AutoInvest bot for {self.user.email}"