from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import csv
import os

transfers_bp = Blueprint('transfers', __name__, url_prefix='/api/transfers')

rates_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'exchange_rates.csv')
fees_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'exchange_fees.csv')

exchange_rates = {}
exchange_fees = {}

# Carga de tasas de cambio
with open(rates_file, 'r', newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader, None)  # Saltar la cabecera (currency_from,currency_to,rate)
    for row in reader:
        if not row or row[0].startswith('#'):  # Permite comentarios o líneas vacías
            continue
        source, target, rate = row
        exchange_rates[(source.strip().upper(), target.strip().upper())] = float(rate)

# Carga de tarifas
with open(fees_file, 'r', newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader, None)  # Saltar la cabecera (currency_from,currency_to,fee)
    for row in reader:
        if not row or row[0].startswith('#'):
            continue
        source, target, fee = row
        exchange_fees[(source.strip().upper(), target.strip().upper())] = float(fee)


def validate_non_empty_fields(data, fields):
    """Verifica que los campos requeridos no estén vacíos ni ausentes."""
    if not data:
        return "No empty fields allowed.", True
    for field in fields:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            return "No empty fields allowed.", True
    return None, False

@transfers_bp.route('/simulate', methods=['POST'])
@jwt_required()
def simulate_transfer():
    """
    Simula una transferencia internacional. 
    Body: { "amount": float, "source_currency": str, "target_currency": str }
    Retorna la cantidad resultante en la moneda destino.
    """
    try:
        data = request.get_json()
        error_msg, error_flag = validate_non_empty_fields(data, ["amount", "source_currency", "target_currency"])
        if error_flag:
            return jsonify({"msg": error_msg}), 400

        amount = data["amount"]
        source = data["source_currency"].strip().upper()
        target = data["target_currency"].strip().upper()

        # Validar que amount sea numérico
        try:
            amount = float(amount)
        except ValueError:
            return jsonify({"msg": "Amount must be a number."}), 400

        # Verificar existencia de tasa de cambio
        rate_key = (source, target)
        if rate_key not in exchange_rates:
            return jsonify({"msg": "Invalid currencies or no exchange data available."}), 404
        
        rate = exchange_rates[rate_key]

        # Verificar existencia de tarifa
        fee_key = (source, target)
        if fee_key not in exchange_fees:
            return jsonify({"msg": "Invalid currencies or no exchange data available."}), 404
        
        fee = exchange_fees[fee_key]

        # Calcular monto resultante
        total_amount = amount * (1 - fee) * rate

        return jsonify({"msg": f"Amount in target currency: {total_amount:.2f}."}), 201
    except Exception as e:
        return jsonify({"msg": f"Error: {str(e)}"}), 400

@transfers_bp.route('/fees', methods=['GET'])
@jwt_required()
def get_fees():
    """
    Retorna la información sobre la tarifa aplicable entre dos monedas.
    Parámetros en la URL: ?source_currency=XXX&target_currency=YYY
    """
    source = request.args.get('source_currency', '').strip().upper()
    target = request.args.get('target_currency', '').strip().upper()

    # Validar campos no vacíos
    if not source or not target:
        return jsonify({"msg": "No empty fields allowed."}), 400

    fee_key = (source, target)
    if fee_key not in exchange_fees:
        return jsonify({"msg": "No fee information available for these currencies."}), 404

    fee = exchange_fees[fee_key]
    return jsonify({"fee": fee}), 200

@transfers_bp.route('/rates', methods=['GET'])
@jwt_required()
def get_rates():
    """
    Retorna la tasa de cambio actual entre dos monedas.
    Parámetros en la URL: ?source_currency=XXX&target_currency=YYY
    """
    source = request.args.get('source_currency', '').strip().upper()
    target = request.args.get('target_currency', '').strip().upper()

    if not source or not target:
        return jsonify({"msg": "No empty fields allowed."}), 400

    rate_key = (source, target)
    if rate_key not in exchange_rates:
        return jsonify({"msg": "No exchange rate available for these currencies."}), 404

    rate = exchange_rates[rate_key]
    return jsonify({"rate": rate}), 200
