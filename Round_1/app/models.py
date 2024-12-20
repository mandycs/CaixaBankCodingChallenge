from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=0.0)  # Agregar este campo

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # 'amount_reached' o 'balance_drop'
    target_amount = db.Column(db.Float, nullable=True)
    alert_threshold = db.Column(db.Float, nullable=True)
    balance_drop_threshold = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "alert_type": self.alert_type,
            "target_amount": self.target_amount,
            "alert_threshold": self.alert_threshold,
            "balance_drop_threshold": self.balance_drop_threshold
        }

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))  # Agregar este campo
    timestamp = db.Column(db.DateTime, default=db.func.now())
    fraud = db.Column(db.Boolean, default=False)


class RecurringExpense(db.Model):
    __tablename__ = 'recurring_expenses'  # Especificar nombre de la tabla si es necesario
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Asociado al usuario autenticado
    expense_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(50), nullable=False)  # 'monthly' u otros
    start_date = db.Column(db.Date, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "expense_name": self.expense_name,
            "amount": self.amount,
            "frequency": self.frequency,
            "start_date": self.start_date.strftime('%Y-%m-%d')
        }