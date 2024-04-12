from flask import Flask, jsonify
import requests
import json
import psycopg2
import procedures_gas_station as procedures_gas_station
import procedures_EV_station as procedures_EV_station
import helpers as helpers

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
    procedures_gas_station.insert_gas_station_distributor_data()
    procedures_gas_station.insert_gas_station_data()
    procedures_gas_station.insert_gas_station_supply_data()
    
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

@app.route('/total', methods=['GET'])
def total():
    procedures_EV_station.insert_EV_station_location_data()
    procedures_EV_station.insert_EV_station_distributor_data()
    procedures_EV_station.insert_EV_station_data()
    procedures_EV_station.insert_EV_station_supply_data()
    procedures_gas_station.insert_gas_station_location_data()
    procedures_gas_station.insert_gas_station_distributor_data()
    procedures_gas_station.insert_gas_station_data()
    procedures_gas_station.insert_gas_station_supply_data()
    
    return "Datos cargados correctamente"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=4000, debug=True)

