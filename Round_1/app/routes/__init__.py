from .auth import auth_bp
from .recurring_expenses import recurring_expenses_bp
from .main import bp as main_bp
from .transfers import transfers_bp
from .alerts import alerts_bp
from .fraud import transactions_bp

__all__ = ["auth_bp", "recurring_expenses_bp", "main_bp", "transfers_bp", "alerts_bp", "transactions_bp"]
