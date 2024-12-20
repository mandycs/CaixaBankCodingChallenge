from flask import Flask
from .config import Config
from flask_migrate import Migrate
from .extensions import db, mail
from flask_jwt_extended import JWTManager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensiones
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    email = mail.init_app(app)

    # Registrar blueprints
    from .routes.auth import auth_bp
    from .routes import main
    from .routes import recurring_expenses_bp
    from .routes import transfers_bp
    from .routes import alerts_bp
    from .routes import transactions_bp
    app.register_blueprint(main.bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(recurring_expenses_bp)
    app.register_blueprint(transfers_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(transactions_bp)
    
    return app
