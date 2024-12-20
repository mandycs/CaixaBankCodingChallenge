from flask_mail import Message
from ..extensions import db, mail
from ..models import User, Alert, Transaction
from datetime import datetime, timedelta

SAVINGS_ALERT_TEMPLATE = """Dear {user_name},

Great news! Your savings are nearing the target amount of {alert_target_amount}.
Keep up the great work and stay consistent!

Best Regards,
The Management Team
"""

BALANCE_DROP_ALERT_TEMPLATE = """Dear {user_name},

We noticed a significant balance drop in your account more than {alert_balance_drop_threshold}.
If this wasn't you, please review your recent transactions to ensure everything is correct.

Best Regards,
The Management Team
"""


def send_alert_email(user, alert):
    """Envía un email al usuario según el tipo de alerta."""
    if alert.alert_type == 'amount_reached':
        subject = "Savings Goal Alert"
        body = SAVINGS_ALERT_TEMPLATE.format(
            user_name=user.name,
            alert_target_amount=alert.target_amount
        )
    elif alert.alert_type == 'balance_drop':
        subject = "Balance Drop Alert"
        body = BALANCE_DROP_ALERT_TEMPLATE.format(
            user_name=user.name,
            alert_balance_drop_threshold=alert.balance_drop_threshold
        )
    else:
        return  # No se reconoce el tipo de alerta, no enviar nada

    msg = Message(subject, recipients=[user.email])
    msg.body = body
    mail.send(msg)


def check_and_notify_alerts(user, last_transaction):
    """
    Verifica las alertas del usuario y envía notificaciones por email si corresponde.
    Se asume que:
    - amount_reached: Se dispara cuando el balance se acerca a target_amount.
      Por ejemplo, si el balance actual >= (target_amount - alert_threshold).
    - balance_drop: Se dispara si el balance actual es menor que (target_amount - balance_drop_threshold)
      o si de alguna forma se detecta una caída significativa.
    """
    alerts = Alert.query.filter_by(user_id=user.id).all()

    for alert in alerts:
        if alert.alert_type == 'amount_reached':
            # Verificar si el usuario está cerca de la meta
            if user.balance >= (alert.target_amount - alert.alert_threshold):
                send_alert_email(user, alert)
        elif alert.alert_type == 'balance_drop':
            # Asumiendo que 'balance_drop_threshold' es un valor absoluto por debajo del cual el balance cae
            # o una cantidad de dinero que indica una caída respecto a un valor anterior.
            # Ejemplo: si el balance es menor que balance_drop_threshold, enviar alerta.
            if user.balance < alert.balance_drop_threshold:
                send_alert_email(user, alert)
