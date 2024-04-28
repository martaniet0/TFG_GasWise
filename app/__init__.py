from flask import Flask
from flask_sqlalchemy import SQLAlchemy 

db= SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://marta:maniro12@postgres:5432/GasWiseDB'

    db.init_app(app)

    # Aquí para evitar importaciones cíclicas
    #from .routes import init_routes
    #init_routes(app)

    #from .views.search import init_search
    #init_search(app)

    from app.routes import routes_bp
    from .views.search import search_bp

    app.register_blueprint(routes_bp, url_prefix='/routes')
    app.register_blueprint(search_bp, url_prefix='/search')

    return app