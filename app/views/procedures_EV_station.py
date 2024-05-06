import psycopg2
import app.views.helpers as helpers
import app.views.database as db
import json
import requests

from flask import Blueprint
from flask_login import login_required

EV_bp = Blueprint('EV', __name__)

#Dictionary for the type of connectors
connector_type = {
    1: "CCS (Type 2)",
    2: "CHAdeMO",
    3: "Type 2 (Tethered Connector)",
    4: "Type 2 (Socket Only)",
    5: "CEE 7/4 - Schuko - Type F",
    6: "IEC 60309 5-pin",
    7: "Tesla (Model S/X)",
    8: "CEE 5 Pin",
    9: "CEE 3 Pin",
    10: "Type 1 (J1772)",
    11: "CCS (Type 1)",
    12: "Type I (AS 3112)",
    13: "Europlug 2-Pin (CEE 7/16)",
    14: "NACS / Tesla Supercharger",
    15: "CEE+ 7 Pin",
    16: "Blue Commando (2P+E)"
}

# Get EV stations data from the API and save it in a JSON file
def get_info_EV_stations():
    #!!!info sensible: API key
    url = 'https://api.openchargemap.io/v3/poi/?output=json&countrycode=ES&maxresults=14000&key=ae697db0-2646-47e3-b30b-9fc784d9b408'

    try:
        request = requests.get(url)
        request.raise_for_status()  # Esto lanzará un error si la solicitud falló

        data = request.json()

        with open('app/json_data/data_EV_stations.json', 'w') as file:
            json.dump(data, file, indent=4)

    except requests.RequestException as e:
        return f"Error inesperado: {e}", 500   

#Open JSON file with data of EV stations
def open_file_EV_stations():
    try:
        with open('app/json_data/data_EV_stations.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    except FileNotFoundError:
        return "Archivo no encontrado", 404
    except json.JSONDecodeError:
        return "Error al decodificar el JSON", 500
    except Exception as e:
        return f"Error inesperado: {e}", 500

# Insert location data of an EV station into the database
def insert_EV_station_location_data():
    data = open_file_EV_stations()   

    for station in data:
        address_info = station.get("AddressInfo", {})
        latitud = address_info.get("Latitude")
        longitud = address_info.get("Longitude")
        provincia = None
        municipio = None
        localidad = None
        cp = address_info.get("Postcode") if address_info.get("Postcode") is not None and len(address_info.get("Postcode")) == 5 else None
        direccion = address_info.get("AddressLine1")

        db.insert_location_data_BD(longitud, latitud, provincia, municipio, localidad, cp, direccion)

# Insert distributor data of an EV station into the database 
def insert_EV_station_distributor_data():
    data = open_file_EV_stations()

    for station in data:
        address_info = station.get("AddressInfo", {})
        nombre = address_info.get("Title")
        latitud = address_info.get("Latitude")
        longitud = address_info.get("Longitude")
        mail = None
        idApi = "EV" + str(station.get("ID"))
        tipo = "E"

        db.insert_distributor_data_BD(nombre, latitud, longitud, mail, idApi, tipo)


# Insert EV station data into the database   
def insert_EV_station_data():
    data = open_file_EV_stations()

    for station in data:
        idApi =  "EV" + str(station.get("ID"))
        id = db.get_distributor_ID(str(idApi))
        usage_info = station.get("UsageType", {})
        precio = station.get("UsageCost")
        tipo_venta = usage_info.get("Title") if usage_info is not None else None
        if id is not None:
            db.insert_station_EV_data_BD(id, tipo_venta, precio)

#Insert EV station supply data into the database 
def insert_EV_station_supply_data():
    data = open_file_EV_stations()  
    for station in data:
        idApi = "EV" + str(station["ID"])
        id_distribuidora = db.get_distributor_ID(str(idApi))
        connections = station.get("Connections", [])
        
        if id_distribuidora is not None:
            for connection in connections:
                id_punto = helpers.get_key(connection["ConnectionType"]["Title"], connector_type) if "ConnectionType" in connection and "Title" in connection["ConnectionType"] else None
                
                if id_punto is not None:
                    cantidad = connection.get("Quantity", 0)
                    voltaje = connection.get("Voltage", 0)
                    amperios = connection.get("Amps", 0)
                    kW = connection.get("PowerKW", 0)
                    if connection is not None and connection.get("Level") is not None:
                        carga_rapida = connection["Level"].get("IsFastChargeCapable")
                    else:
                        carga_rapida = None


                    db.insert_station_EV_supply_data_BD(id_distribuidora, id_punto, carga_rapida, cantidad, voltaje, amperios, kW)

############################################################################################################
#RUTAS
############################################################################################################

#Ruta para obtener la información de una estación de carga de OpenChargeMap
@EV_bp.route('/get_data_EV_stations', methods=['GET'])
@login_required
def get_data_EV_stations():
    get_info_EV_stations()

#Ruta para insertar los datos de las estaciones de carga de vehículos eléctricos en la base de datos
@EV_bp.route('/insert_EV_BD_station_data', methods=['GET'])
@login_required
def insert_EV_BD_station_data():
    insert_EV_station_location_data()
    insert_EV_station_distributor_data()
    insert_EV_station_data()
    insert_EV_station_supply_data()