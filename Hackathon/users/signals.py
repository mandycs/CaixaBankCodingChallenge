from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, BankAccount

@receiver(post_save, sender=CustomUser)
def create_bank_account(sender, instance, created, **kwargs):
    """
    Crea automáticamente una cuenta bancaria para cada nuevo usuario.
    """
    if created:
        BankAccount.objects.create(user=instance, accountNumber=instance.accountNumber)
