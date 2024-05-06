from flask import Blueprint

routes_bp = Blueprint('routes', __name__)

#def init_routes(app):
@routes_bp.route('/', methods=['GET'])
def hola_mundo():
    return "Hola mundo"






