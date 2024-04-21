import psycopg2
import helpers as helpers
import db as db
import json
import requests

gas_type = {
    1: "Biodiesel",
    2: "Bioetanol",
    3: "Gas Natural Comprimido",
    4: "Gas Natural Licuado",
    5: "Gases licuados del petróleo",
    6: "Gasoleo A",
    7: "Gasoleo B",
    8: "Gasoleo Premium",
    9: "Gasolina 95 E10",
    10: "Gasolina 95 E5",
    11: "Gasolina 95 E5 Premium",
    12: "Gasolina 98 E10",
    13: "Gasolina 98 E5",
    14: "Hidrogeno"
}

# Get gas stations data from the API and save it in a JSON file
def get_info_gas_stations():
    url = 'https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres'

    try:
        request = requests.get(url)
        request.raise_for_status()  # Esto lanzará un error si la solicitud falló

        datos = request.json()

        with open('/app/data_gas_stations.json', 'w') as archivo:
            json.dump(datos, archivo, indent=4)

    except requests.RequestException as e:
        return f"Error al intentar obtener los datos de las gasolineras: {e}", 500   

#Open JSON file with data of gas stations
def open_file_gas_stations():
    try:
        with open('/app/data_gas_stations.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    except FileNotFoundError:
        return "Archivo no encontrado", 404
    except json.JSONDecodeError:
        return "Error al decodificar el JSON", 500
    except Exception as e:
        return f"Error inesperado: {e}", 500

# Insert location data of an gas station into the database
def insert_gas_station_location_data():
    data = open_file_gas_stations()   

    stations_list = data["ListaEESSPrecio"]

    for estacion in stations_list:
        cp = estacion["C.P."]
        direccion = estacion["Direcci\u00f3n"]
        latitud = estacion["Latitud"]
        localidad = estacion["Localidad"]
        longitud = estacion["Longitud (WGS84)"]
        municipio = estacion["Municipio"]
        provincia = estacion["Provincia"]

        db.insert_location_data_BD2(longitud, latitud, provincia, municipio, localidad, cp, direccion) ###!!!

    
# Insert distributor data of an gas station into the database 
def insert_gas_station_distributor_data():
    data = open_file_gas_stations()

    stations_list = data["ListaEESSPrecio"]

    for station in stations_list:
        nombre= station["R\u00f3tulo"]
        latitud = station["Latitud"]
        longitud = station["Longitud (WGS84)"]
        mail = None
        idApi = station["IDEESS"]

        db.insert_distributor_data_BD(nombre, latitud, longitud, mail, idApi)

# Insert gas station data into the database   
def insert_gas_station_data():
    data = open_file_gas_stations()

    stations_list = data["ListaEESSPrecio"]

    for station in stations_list:
        idApi = station["IDEESS"]
        id = db.get_distributor_ID(str(idApi))
        if station["Tipo Venta"] == 'P':
            tipo_venta = True
        elif station["Tipo Venta"] == 'R':
            tipo_venta = False
        else:
            tipo_venta = None
        horario = station["Horario"]
        margen = station["Margen"]
    
        db.insert_gas_station_data_BD(id, tipo_venta, horario, margen)
    
#Insert gas station supply data into the database 
def insert_gas_station_supply_data():
    data = open_file_gas_stations()  

    stations_list = data["ListaEESSPrecio"]

    for station in stations_list:
        idApi = station["IDEESS"]
        id_distribuidora = db.get_distributor_ID(str(idApi))
        i=1
        for combustible in gas_type.values():
            id_combustible = helpers.get_key(combustible, gas_type)
            precio = station["Precio {}".format(combustible)] if station["Precio {}".format(combustible)] != '' else 0.0
            if precio != 0.0:
                db.insert_gas_station_supply_data_BD(id_distribuidora, id_combustible, precio)
            i+=1
                


    
    

    
