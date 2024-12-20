from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import User, Transaction
from datetime import datetime, timedelta
import statistics
from ..services.mail import check_and_notify_alerts

transactions_bp = Blueprint(
    'transactions', __name__, url_prefix='/api/transactions')


def validate_non_empty_fields(data, fields):
    """Verifica que los campos requeridos no estén vacíos ni ausentes."""
    if not data:
        return "No data provided.", True
    for field in fields:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            return "No empty fields allowed.", True
    return None, False


@transactions_bp.route('/', methods=['POST'])
@jwt_required()
def add_transaction():
    """
    Crea una nueva transacción, evalúa si es fraude y la almacena.
    Body esperado:
    {
      "amount": float,
      "category": "string",
      "timestamp": "2024-11-20T10:30:00Z" (opcional, si no se provee usar tiempo actual)
    }
    """
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({"msg": "Invalid token."}), 401

    data = request.get_json()

    # Validar campos requeridos: amount, category
    error_msg, error_flag = validate_non_empty_fields(
        data, ["amount", "category"])
    if error_flag:
        return jsonify({"msg": error_msg}), 400

    # Convertir amount a float
    try:
        amount = float(data["amount"])
    except ValueError:
        return jsonify({"msg": "Amount must be a number."}), 400

    category = data["category"].strip().lower()

    # Timestamp opcional, si no está o es inválido usar datetime.utcnow()
    timestamp_str = data.get("timestamp", None)
    if timestamp_str is None or timestamp_str.strip() == "":
        tx_time = datetime.utcnow()
    else:
        # Intentar parsear el timestamp. Suponemos formato ISO8601
        try:
            tx_time = datetime.fromisoformat(
                timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            return jsonify({"msg": "Invalid timestamp format."}), 400

    # Obtener el usuario
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found."}), 404

    # Reglas de fraude
    fraud = False

    # 1) High Deviation from Average Spending - últimos 90 días
    ninety_days_ago = tx_time - timedelta(days=90)
    recent_transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.timestamp >= ninety_days_ago,
        Transaction.timestamp < tx_time
    ).all()

    amounts_90_days = [t.amount for t in recent_transactions]
    if amounts_90_days:
        daily_average_90, std_dev_90 = daily_average_and_std(
            amounts_90_days, recent_transactions, ref_time=tx_time
        )
        if std_dev_90 > 0 and amount > (daily_average_90 + 3 * std_dev_90):
            fraud = True
    else:
        # Si no hay historial, no se marca fraude por este punto.
        daily_average_90 = amount
        std_dev_90 = 0

    # 2) Unusual Spending Category - últimos 6 meses
    six_months_ago = tx_time - timedelta(days=180)
    category_transactions_6m = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.timestamp >= six_months_ago,
        Transaction.timestamp < tx_time
    ).all()

    used_categories = {t.category for t in category_transactions_6m}
    if category not in used_categories and len(category_transactions_6m) > 0:
        fraud = True

    # 3) Rapid Transactions - más de 3 transacciones en 5 min con sumatoria mayor que daily_average_90
    five_minutes_ago = tx_time - timedelta(minutes=5)
    recent_5min_transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.timestamp >= five_minutes_ago,
        Transaction.timestamp < tx_time
    ).all()

    recent_5min_count = len(recent_5min_transactions) + 1
    recent_5min_sum = sum(
        [t.amount for t in recent_5min_transactions]) + amount

    if recent_5min_count > 3 and recent_5min_sum > daily_average_90:
        fraud = True

    # Crear la transacción
    new_tx = Transaction(
        user_id=user_id,
        amount=amount,
        category=category,
        timestamp=tx_time,
        fraud=fraud
    )
    db.session.add(new_tx)

    # Actualizar balance del usuario (asumiendo que amount es un gasto)
    user.balance = (user.balance or 0) - amount
    db.session.commit()

    check_and_notify_alerts(user, new_tx)
    return jsonify({
        "msg": "Transaction added and evaluated for fraud.",
        "data": {
            "id": new_tx.id,
            "user_id": new_tx.user_id,
            "amount": new_tx.amount,
            "category": new_tx.category,
            "timestamp": new_tx.timestamp.isoformat(),
            "fraud": new_tx.fraud
        }
    }), 201


def daily_average_and_std(amounts, transactions, ref_time):
    if not transactions:
        return 0, 0
    start_date = min(t.timestamp for t in transactions)
    days = max((ref_time - start_date).days, 1)
    total_spent = sum(amounts)
    daily_avg = total_spent / days

    if len(amounts) > 1:
        std_dev = statistics.pstdev(amounts)
    else:
        std_dev = 0
    return daily_avg, std_dev
