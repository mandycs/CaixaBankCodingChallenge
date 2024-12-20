from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from .utils import get_market_price
from .models import Subscription, Transaction, AutoInvest, UserAsset
from decimal import Decimal

@shared_task
def process_subscriptions():
    """Procesa las suscripciones activas descontando el monto establecido en cada intervalo de tiempo."""
    subscriptions = Subscription.objects.filter(is_active=True)
    current_time = timezone.now()

    for subscription in subscriptions:
        user = subscription.user

        # Verificar si el intervalo de tiempo ha pasado
        if (current_time - subscription.last_executed).total_seconds() >= subscription.interval_seconds:
            if user.account.balance >= subscription.amount:
                # Actualizar el balance del usuario
                user.account.balance -= subscription.amount
                user.account.save()

                # Registrar la transacción
                Transaction.objects.create(
                    amount=subscription.amount,
                    transactionType="SUBSCRIPTION",
                    sourceAccount=user.account,
                    transactionDate=current_time
                )

                # Actualizar el último tiempo de ejecución de la suscripción
                subscription.last_executed = current_time
                subscription.save()
            else:
                # Desactivar la suscripción si no hay saldo suficiente
                subscription.is_active = False
                subscription.save()

@shared_task
def auto_invest_bot():
    """Automatiza la compra y venta de activos para todos los usuarios con auto-inversión activa."""

    # Obtenemos el modelo de usuario personalizado
    CustomUser = get_user_model()

    # Filtramos todos los usuarios con auto-inversión activa
    auto_invest_users = AutoInvest.objects.filter(is_active=True)

    for auto_invest in auto_invest_users:
        user = auto_invest.user

        # Procesar cada activo del usuario
        assets = user.assets.all()
        for asset in assets:
            try:
                # Obtenemos el precio de mercado actual del activo y lo convertimos a Decimal
                current_price = Decimal(get_market_price(asset.assetSymbol))

                # Condición de compra: Si el precio cae un 20% por debajo del precio de compra original
                if current_price < asset.purchase_price * Decimal('0.8'):
                    amount_to_buy = asset.quantity * Decimal('0.1')
                    total_cost = amount_to_buy * current_price
                    if user.account.balance >= total_cost:
                        # Actualizar el balance y la cantidad del activo
                        asset.quantity += amount_to_buy
                        asset.save()
                        user.account.balance -= total_cost
                        user.account.save()

                        # Registrar la transacción de compra
                        Transaction.objects.create(
                            amount=total_cost,
                            transactionType="ASSET_PURCHASE",
                            sourceAccount=user.account,
                            transactionDate=timezone.now()
                        )

                # Condición de venta: Si el precio sube un 20% por encima del precio de compra original
                elif current_price > asset.purchase_price * Decimal('1.2'):
                    amount_to_sell = asset.quantity * Decimal('0.1')
                    total_revenue = amount_to_sell * current_price
                    if amount_to_sell > 0:
                        # Actualizar la cantidad del activo y el balance del usuario
                        asset.quantity -= amount_to_sell
                        asset.save()
                        user.account.balance += total_revenue
                        user.account.save()

                        # Registrar la transacción de venta
                        Transaction.objects.create(
                            amount=total_revenue,
                            transactionType="ASSET_SELL",
                            sourceAccount=user.account,
                            transactionDate=timezone.now()
                        )

            except ValueError as e:
                print(f"Error al obtener el precio de mercado para {asset.assetSymbol}: {e}")
            except Exception as e:
                print(f"Error inesperado al procesar {asset.assetSymbol} para el usuario {user.id}: {e}")

        # Registrar la última ejecución del bot de inversión automática para este usuario
        auto_invest.last_executed = timezone.now()
        auto_invest.save()