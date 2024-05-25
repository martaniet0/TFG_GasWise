from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager

db= SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://marta:maniro12@postgres:5432/GasWiseDB'
    app.config['SECRET_KEY'] = '5017636134de96da7773b784d3cb7d01'

    db.init_app(app)

    #Encriptar las contraseñas
    bcrypt.init_app(app)

    #Para gestionar las sesiones de usuario
    login_manager.init_app(app)
    login_manager.login_view = 'users.login'
    login_manager.login_message_category = 'info'
    
    from app.routes_borrar import routes_bp
    from .views.search import search_bp
    from .views.users import users_bp
    from .views.procedures_EV_station import EV_bp
    from .views.procedures_gas_station import gas_bp
    from .views.distributor_info import distributor_bp

    app.register_blueprint(routes_bp)
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(EV_bp, url_prefix='/EV')
    app.register_blueprint(gas_bp, url_prefix='/gas')
    app.register_blueprint(distributor_bp, url_prefix='/distributor')

    return app