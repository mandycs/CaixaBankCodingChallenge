from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Alert

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

def validate_non_empty_fields(data, fields):
    """Verifica que los campos requeridos no estén vacíos ni ausentes."""
    if not data:
        return "No empty fields allowed.", True
    for field in fields:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            return "No empty fields allowed.", True
    return None, False

@alerts_bp.route('/amount_reached', methods=['POST'])
@jwt_required()
def create_amount_reached_alert():
    """
    Crea una alerta de ahorro (amount reached).
    Body: { "target_amount": float, "alert_threshold": float }
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    
    error_msg, error_flag = validate_non_empty_fields(data, ["target_amount", "alert_threshold"])
    if error_flag:
        return jsonify({"msg": error_msg}), 400

    try:
        target_amount = float(data["target_amount"])
        alert_threshold = float(data["alert_threshold"])
    except ValueError:
        return jsonify({"msg": "Fields must be numeric."}), 400

    # Crear alerta
    alert = Alert(
        user_id=user_id,
        alert_type='amount_reached',
        target_amount=target_amount,
        alert_threshold=alert_threshold
    )
    db.session.add(alert)
    db.session.commit()

    return jsonify({"msg": "Correctly added savings alert!",
                    "data": alert.to_dict()}), 201


@alerts_bp.route('/balance_drop', methods=['POST'])
@jwt_required()
def create_balance_drop_alert():
    """
    Crea una alerta de caída de balance (balance_drop).
    Body: { "balance_drop_threshold": float }
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    error_msg, error_flag = validate_non_empty_fields(data, ["balance_drop_threshold"])
    if error_flag:
        return jsonify({"msg": error_msg}), 400

    try:
        balance_drop_threshold = float(data["balance_drop_threshold"])
    except ValueError:
        return jsonify({"msg": "Fields must be numeric."}), 400

    # Crear alerta
    alert = Alert(
        user_id=user_id,
        alert_type='balance_drop',
        balance_drop_threshold=balance_drop_threshold
    )
    db.session.add(alert)
    db.session.commit()

    return jsonify({"msg": "Correctly added balance drop alert!",
                    "data": alert.to_dict()}), 201


@alerts_bp.route('/delete', methods=['POST'])
@jwt_required()
def delete_alert():
    """
    Elimina una alerta dado su alert_id.
    Body: { "alert_id": int }
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"msg": "No empty fields allowed."}), 400
    if "alert_id" not in data or data["alert_id"] is None:
        return jsonify({"msg": "Missing alert ID."}), 400

    try:
        alert_id = int(data["alert_id"])
    except ValueError:
        return jsonify({"msg": "Alert ID must be numeric."}), 400

    alert = Alert.query.filter_by(id=alert_id, user_id=user_id).first()
    if not alert:
        return jsonify({"msg": "Alert not found."}), 404

    db.session.delete(alert)
    db.session.commit()
    return jsonify({"msg": "Alert deleted successfully."}), 200


@alerts_bp.route('/list', methods=['GET'])
@jwt_required()
def list_alerts():
    """
    Retorna la lista de todas las alertas del usuario autenticado.
    """
    user_id = get_jwt_identity()
    alerts = Alert.query.filter_by(user_id=user_id).all()

    # Dependiendo de la lógica de negocio, aquí podría implementarse lógica de cálculo
    # de progreso hacia el target u otras métricas. De momento, devolvemos la data sin modificar.
    return jsonify({"data": [alert.to_dict() for alert in alerts]}), 200
