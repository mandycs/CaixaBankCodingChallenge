from flask import Blueprint

# Crea un blueprint
bp = Blueprint('main', __name__)

# Ejemplo de una ruta simple
@bp.route('/')
def index():
    return "¡Hola, mundo!"