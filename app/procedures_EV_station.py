import psycopg2
import helpers as helpers
import db as db
import json
import requests

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

#Get the dictionary key based on the value
def get_key(val):
    for key, value in connector_type.items():
         if val == value:
             return key
    return None

# Get EV stations data from the API and save it in a JSON file
def get_info_EV_stations():
    #!!!info sensible: API key
    url = 'https://api.openchargemap.io/v3/poi/?output=json&countrycode=ES&maxresults=14000&key=ae697db0-2646-47e3-b30b-9fc784d9b408'

    try:
        request = requests.get(url)
        request.raise_for_status()  # Esto lanzará un error si la solicitud falló

        data = request.json()

        with open('/app/data_EV_stations.json', 'w') as file:
            json.dump(data, file, indent=4)

    except requests.RequestException as e:
        return f"Error inesperado: {e}", 500   

#Open JSON file with data of EV stations
def open_file_EV_stations():
    try:
        with open('/app/data_EV_stations.json', 'r', encoding='utf-8') as file:
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
        cp = address_info.get("Postcode") if len(address_info.get("Postcode")) == 5 else None
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

        db.insert_distributor_data_BD(nombre, latitud, longitud, mail, idApi)


# Insert EV station data into the database   
def insert_EV_station_data():
    data = open_file_EV_stations()

    for station in data:
        idApi =  "EV" + str(station.get("ID"))
        id = db.get_distributor_ID(str(idApi))
        usage_info = station.get("UsageType", {})
        precio = station.get("UsageCost")
        tipo_venta = usage_info.get("Title")
        
        db.insert_station_EV_data_BD(id, tipo_venta, precio)

#Insert EV station supply data into the database 
def insert_EV_station_supply_data():
    data = open_file_EV_stations()  
    for station in data:
        idApi = "EV" + str(station["ID"])
        id_distribuidora = db.get_distributor_ID(str(idApi))
        connections = station.get("Connections", [])
        
        for connection in connections:
            id_punto = get_key(connection["ConnectionType"]["Title"]) if "ConnectionType" in connection and "Title" in connection["ConnectionType"] else None
            
            if id_punto is not None:
                cantidad = connection.get("Quantity", 0)
                voltaje = connection.get("Voltage", 0)
                amperios = connection.get("Amps", 0)
                kW = connection.get("PowerKW", 0)
                carga_rapida = connection["Level"]["IsFastChargeCapable"] if "Level" in connection and "IsFastChargeCapable" in connection["Level"] else False

                with open('/app/log.txt', 'a') as file:
                    file.write(f"ID Distribuidora: {id_distribuidora}, ID Punto: {id_punto}, Carga rápida: {carga_rapida}, Cantidad: {cantidad}, Voltaje: {voltaje}, Amperios: {amperios}, kW: {kW}\n")
                
                db.insert_station_EV_supply_data_BD(id_distribuidora, id_punto, carga_rapida, cantidad, voltaje, amperios, kW)