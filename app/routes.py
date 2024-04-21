from flask import Flask
import requests
import json
import psycopg2
import procedures_gas_station as procedures_gas_station
import procedures_EV_station as procedures_EV_station
import helpers as helpers
import db as db
import distributor_search.search as search
from flask import render_template

app = Flask(__name__)

@app.route('/', methods=['GET'])
def hola_mundo():
    return "Hola mundo"

#https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/help

#Insert gas stations data into the database
@app.route('/insert_data_BD_gas_stations', methods=['GET'])
def insert_location_data_BD_gas_stations():
    #procedures_gas_station.get_info_gas_stations()
    procedures_gas_station.insert_gas_station_location_data()
    #procedures_gas_station.insert_gas_station_distributor_data()
    #procedures_gas_station.insert_gas_station_data()
    #procedures_gas_station.insert_gas_station_supply_data()
    
    return "Datos cargados correctamente"    

#Insert EV stations data into the database
@app.route('/insert_data_BD_EV_stations', methods=['GET'])
def insert_location_data_BD_EV_stations():
    #procedures_EV_station.get_info_EV_stations()
    procedures_EV_station.insert_EV_station_location_data()
    procedures_EV_station.insert_EV_station_distributor_data()
    procedures_EV_station.insert_EV_station_data()
    procedures_EV_station.insert_EV_station_supply_data()
    
    return "Datos cargados correctamente"

@app.route('/mapa', methods=['GET'])
def mapa():
    return render_template('map.html')

@app.route('/search_gas_stations_on_route', methods=['GET']) #PRUEBA
def search_gas_stations_on_route():
    db.get_route_distributors()
    
    return "Exito"

@app.route('/ver_rutas', methods=['GET'])
def ver_rutas():
    return str(app.url_map)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=4000, debug=True)
