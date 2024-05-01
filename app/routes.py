#from app import app
from app.views import procedures_gas_station, procedures_EV_station
from app.views import database as db
from flask import Blueprint, render_template

routes_bp = Blueprint('routes', __name__)

#def init_routes(app):
@routes_bp.route('/', methods=['GET'])
def hola_mundo():
    return "Hola mundo"

#https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/help

#Insert gas stations data into the database
@routes_bp.route('/insert_data_BD_gas_stations', methods=['GET'])
def insert_location_data_BD_gas_stations():
    #procedures_gas_station.get_info_gas_stations()
    #procedures_gas_station.insert_gas_station_location_data()
    #procedures_gas_station.insert_gas_station_distributor_data()
    #procedures_gas_station.insert_gas_station_data()
    #procedures_gas_station.insert_gas_station_supply_data()
    
    return "Datos cargados correctamente"    

#Insert EV stations data into the database
@routes_bp.route('/insert_data_BD_EV_stations', methods=['GET'])
def insert_location_data_BD_EV_stations():
    #procedures_EV_station.get_info_EV_stations()
    #procedures_EV_station.insert_EV_station_location_data()
    #procedures_EV_station.insert_EV_station_distributor_data()
    #procedures_EV_station.insert_EV_station_data()
    #procedures_EV_station.insert_EV_station_supply_data()
    
    return "Datos cargados correctamente"

@routes_bp.route('/mapa', methods=['GET'])
def mapa():
    return render_template('map.html')

