from flask import Flask
from flask_sqlalchemy import SQLAlchemy 

db= SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://marta:maniro12@postgres:5432/GasWiseDB'

    db.init_app(app)

    # Importar aquí para evitar importaciones cíclicas
    from .routes import init_routes
    init_routes(app)

    from .views.search import init_search
    init_search(app)

    return app