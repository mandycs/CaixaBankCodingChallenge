from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import RecurringExpense
from datetime import datetime, date

recurring_expenses_bp = Blueprint('recurring_expenses', __name__, url_prefix='/api/recurring-expenses')


def validate_recurring_expense_data(data):
    """Auxiliary function to validate recurring expense data."""
    print("Starting validation for data:", data)  # Debug log
    
    # Verificar que data es un diccionario
    if not isinstance(data, dict):
        return "Invalid data format - expected JSON object.", 400
    
    required_fields = ["expense_name", "amount", "frequency", "start_date"]
    
    # Verificar campos requeridos
    for field in required_fields:
        if field not in data:
            return f"Missing required field: {field}", 400
        if data[field] is None:
            return f"Field {field} cannot be null", 400
    
    # Validar expense_name
    if not isinstance(data["expense_name"], str):
        return "expense_name must be a string", 400
    if len(data["expense_name"].strip()) == 0:
        return "expense_name cannot be empty", 400
    
    # Validar amount
    try:
        amount = float(data["amount"])
        if amount <= 0:
            return "Amount must be greater than 0", 400
    except (ValueError, TypeError):
        return "Amount must be a valid number", 400
    
    # Validar frequency
    valid_frequencies = ["monthly", "yearly"]
    if not isinstance(data["frequency"], str) or data["frequency"] not in valid_frequencies:
        return f"Frequency must be one of {valid_frequencies}", 400
    
    # Validar start_date
    try:
        if not isinstance(data["start_date"], str):
            return "start_date must be a string in YYYY-MM-DD format", 400
        datetime.strptime(data["start_date"], '%Y-%m-%d')
    except ValueError:
        return "Invalid date format. Use YYYY-MM-DD", 400

    print("Validation passed successfully")  # Debug log
    return None, 200

@recurring_expenses_bp.route('', methods=['POST'])
@jwt_required()
def add_expense():
    """Endpoint to add a recurring expense."""
    try:
        # Añadimos logs para depuración
        print("Headers:", dict(request.headers))
        print("Content-Type:", request.content_type)
        
        # Verificamos si hay datos en el cuerpo
        if not request.data:
            print("No request data found")
            return jsonify({"msg": "No data provided in request body"}), 400
            
        # Intentamos obtener el JSON
        try:
            data = request.get_json()
            print("Received JSON data:", data)
        except Exception as e:
            print("Error parsing JSON:", str(e))
            return jsonify({"msg": "Invalid JSON format"}), 400

        if not data:
            return jsonify({"msg": "No data provided or invalid JSON."}), 400

        # Validación de datos
        validation_error, status_code = validate_recurring_expense_data(data)
        if validation_error:
            print("Validation error:", validation_error)
            return jsonify({"msg": validation_error}), status_code

        # Verificación del usuario
        user_id = get_jwt_identity()
        print("User ID:", user_id)
        
        if not user_id:
            return jsonify({"msg": "Invalid token or user not authenticated."}), 401

        # Creación del gasto
        try:
            expense = RecurringExpense(
                user_id=user_id,
                expense_name=data["expense_name"],
                amount=data["amount"],
                frequency=data["frequency"],
                start_date=datetime.strptime(data["start_date"], '%Y-%m-%d')
            )
            print("Created expense object:", expense.__dict__)
            
            db.session.add(expense)
            db.session.commit()
            print("Successfully committed to database")

            return jsonify({"msg": "Recurring expense added successfully.", "data": expense.to_dict()}), 201
            
        except Exception as e:
            print("Error creating expense:", str(e))
            db.session.rollback()
            return jsonify({"msg": f"Error creating expense: {str(e)}"}), 400
            
    except Exception as e:
        print("Unexpected error:", str(e))
        return jsonify({"msg": f"Unexpected error: {str(e)}"}), 500

@recurring_expenses_bp.route('', methods=['GET'])
@jwt_required()
def get_expenses():
    """Retrieve all recurring expenses for the authenticated user."""
    user_id = get_jwt_identity()
    try:
        expenses = RecurringExpense.query.filter_by(user_id=user_id).all()
        if not expenses:
            return jsonify({"data": [], "msg": "No recurring expenses found."}), 200

        return jsonify({"data": [expense.to_dict() for expense in expenses]}), 200
    except Exception as e:
        return jsonify({"msg": f"Error: {str(e)}"}), 400


@recurring_expenses_bp.route('/<int:expense_id>', methods=['PUT'])
@jwt_required()
def update_expense(expense_id):
    """Update an existing recurring expense."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No data provided."}), 400

        validation_error, status_code = validate_recurring_expense_data(data)
        if validation_error:
            return jsonify({"msg": validation_error}), status_code

        user_id = get_jwt_identity()
        expense = RecurringExpense.query.filter_by(id=expense_id, user_id=user_id).first()
        if not expense:
            return jsonify({"msg": "Expense not found."}), 404

        expense.expense_name = data["expense_name"]
        expense.amount = data["amount"]
        expense.frequency = data["frequency"]
        expense.start_date = datetime.strptime(data["start_date"], '%Y-%m-%d')
        
        db.session.commit()
        return jsonify({"msg": "Recurring expense updated successfully.", "data": expense.to_dict()}), 200
    except db.IntegrityError as e:
        db.session.rollback()
        return jsonify({"msg": "Database integrity error occurred."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error: {str(e)}"}), 400


@recurring_expenses_bp.route('/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    """Delete a recurring expense by ID."""
    try:
        user_id = get_jwt_identity()
        expense = RecurringExpense.query.filter_by(id=expense_id, user_id=user_id).first()
        if not expense:
            return jsonify({"msg": "Expense not found."}), 404
        
        db.session.delete(expense)
        db.session.commit()
        return jsonify({"msg": "Recurring expense deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error: {str(e)}"}), 400


@recurring_expenses_bp.route('/projection', methods=['GET'])
@jwt_required()
def get_projection():
    """Calculate and retrieve a 12-month projection of recurring expenses."""
    user_id = get_jwt_identity()
    try:
        expenses = RecurringExpense.query.filter_by(user_id=user_id).all()
        if not expenses:
            return jsonify({"data": [], "msg": "No recurring expenses found."}), 200

        projections = {}
        today = datetime.today().date()  # Convertimos hoy a date para ser consistentes

        for expense in expenses:
            start_date = expense.start_date  # Es un objeto date
            for i in range(12):  # Próximos 12 meses
                month = (today.month + i - 1) % 12 + 1
                year = today.year + (today.month + i - 1) // 12
                date_key = f"{year}-{month:02d}"
                
                # Aquí usamos date(...) en vez de datetime(...)
                if start_date <= date(year, month, 1):
                    projections[date_key] = projections.get(date_key, 0) + expense.amount

        projection_list = [{"month": k, "recurring_expenses": v} for k, v in sorted(projections.items())]
        return jsonify({"data": projection_list}), 200

    except Exception as e:
        return jsonify({"msg": f"Error: {str(e)}"}), 400