import os

class Config:
    # Clave secreta para sesiones y seguridad
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key_123')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev_jwt_secret_key_123')
    # Configuración de base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI', 
        'mysql+pymysql://root:root@mysql:3306/bankingapp'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuraciones de desarrollo
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Muestra las consultas SQL
    
    # Configuración de correo
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 1025))
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    MAIL_DEFAULT_SENDER = 'noreply@company.com'