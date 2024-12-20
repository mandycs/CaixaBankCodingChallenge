from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..models import User
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def validate_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validar datos de entrada
    if not data or not all(field in data for field in ['email', 'password', 'name']):
        return jsonify({'error': 'All fields are required.'}), 400

    if any(not data[field].strip() for field in ['email', 'password', 'name']):
        return jsonify({'error': 'No empty fields allowed.'}), 400

    if not validate_email(data['email']):
        return jsonify({'error': f'Invalid email: {data["email"]}'}), 400

    # Verificar si el email ya existe
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists.'}), 400

    # Crear nuevo usuario
    user = User(name=data['name'], email=data['email'])
    user.password_hash = generate_password_hash(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'name': user.name,
        'hashedPassword': user.password_hash,
        'email': user.email
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Validar datos de entrada
    if not data or not all(field in data for field in ['email', 'password']):
        return jsonify({'error': 'Bad credentials.'}), 401

    # Buscar usuario por email
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'error': f'User not found for the given email: {data["email"]}'}), 400

    # Verificar contraseña
    if not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Bad credentials.'}), 401

    # Crear token JWT utilizando solo el id del usuario como identidad (string)
    token = create_access_token(identity=str(user.id))

    return jsonify({'token': token}), 200
