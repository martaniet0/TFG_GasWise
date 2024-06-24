import psycopg2
import app.views.helpers as helpers
import app.views.database as db
import json
import requests

from flask import Blueprint, redirect, url_for, render_template
from flask_login import login_required

gas_bp = Blueprint('gas', __name__)

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
#https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/help
def get_info_gas_stations():
    url = 'https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres'

    try:
        request = requests.get(url)
        request.raise_for_status()  # Esto lanzará un error si la solicitud falló

        datos = request.json()

        with open('app/json_data/data_gas_stations.json', 'w') as archivo:
            json.dump(datos, archivo, indent=4)

    except requests.RequestException as e:
        return f"Error al intentar obtener los datos de las gasolineras: {e}", 500   

#Open JSON file with data of gas stations
def open_file_gas_stations():
    try:
        with open('app/json_data/data_gas_stations.json', 'r', encoding='utf-8') as file:
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

        db.insert_location_data_BD(longitud, latitud, provincia, municipio, localidad, cp, direccion)

    
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
        tipo = "G"

        db.insert_distributor_data_BD(nombre, latitud, longitud, mail, idApi, tipo)

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
        for combustible in gas_type.values():
            id_combustible = helpers.get_key(combustible, gas_type)
            precio = station["Precio {}".format(combustible)] if station["Precio {}".format(combustible)] != '' else 0.0
            if precio != 0.0:
                db.insert_gas_station_supply_data_BD(id_distribuidora, id_combustible, precio)

#Obtener los datos a insertar y actualizar en la base de datos
def generate_sql_statements():
    get_info_gas_stations()
    data = open_file_gas_stations()
    stations_list = data["ListaEESSPrecio"]

    ubicaciones = []
    distribuidoras = []
    gasolineras = []
    suministros_nuevos = []
    suministros_actualizados = []

    for station in stations_list:
        idApi = station["IDEESS"]
        id_distribuidora = db.get_distributor_ID(str(idApi))
        latitud = station["Latitud"]
        longitud = station["Longitud (WGS84)"]
        location = db.get_location(latitud, longitud)
        # Si no existe la distribuidora en la base de datos (es nueva)
        if id_distribuidora is None and location is False:
            # Ubicacion
            cp = station["C.P."]
            direccion = station["Dirección"]
            localidad = station["Localidad"]
            municipio = station["Municipio"]
            provincia = station["Provincia"]
            ubicaciones.append([helpers.to_float(longitud), helpers.to_float(latitud), provincia, municipio, localidad, cp, direccion])

            # Distribuidora
            nombre = station["Rótulo"]
            mail = None
            tipo = "G"
            nombre= station["R\u00f3tulo"]
            mail = None
            idAPI = station["IDEESS"]
            tipo = "G"
            distribuidoras.append([nombre, helpers.to_float(latitud), helpers.to_float(longitud), mail, idAPI, tipo])

            # Gasolinera
            if station["Tipo Venta"] == 'P':
                tipo_venta = True
            elif station["Tipo Venta"] == 'R':
                tipo_venta = False
            else:
                tipo_venta = None
            horario = station["Horario"]
            margen = station["Margen"]

            #En la insercción hay que buscar correspondencia entre idDistribuidora y idAPI
            gasolineras.append([idAPI, tipo_venta, horario, margen])

            # Suministro
            for combustible in gas_type.values():
                id_combustible = helpers.get_key(combustible, gas_type)
                precio = station["Precio {}".format(combustible)] if station["Precio {}".format(combustible)] != '' else 0.0
                if precio != 0.0:
                    #En la insercción hay que buscar correspondencia entre idDistribuidora y idAPI
                    suministros_nuevos.append([idAPI, id_combustible, precio])
        #Si solo tenemos que actualizar el precio
        else:
            # Suministro
            for combustible in gas_type.values():
                id_combustible = helpers.get_key(combustible, gas_type)
                precio = station["Precio {}".format(combustible)] if station["Precio {}".format(combustible)] != '' else 0.0
                if precio != 0.0:
                    #En la insercción hay que buscar correspondencia entre idDistribuidora y idAPI
                    suministros_actualizados.append([id_distribuidora, id_combustible, precio])

    # Escribir datos en archivos
    helpers.write_to_file('app/json_data/ubicaciones.csv', ubicaciones)
    helpers.write_to_file('app/json_data/distribuidoras.csv', distribuidoras)
    helpers.write_to_file('app/json_data/gasolineras.csv', gasolineras)
    helpers.write_to_file('app/json_data/suministros_nuevos.csv', suministros_nuevos)
    helpers.write_to_file('app/json_data/suministros_actualizados.csv', suministros_actualizados)

############################################################################################################
#RUTAS
############################################################################################################

#Ruta para obtener la información de una estación de servicio de la API del Ministerio de Industria, Energía y Turismo
@gas_bp.route('/get_data_gas_stations', methods=['GET'])
@login_required
@helpers.admin_required
def get_data_gas_stations():
    get_info_gas_stations()

#Ruta para insertar los datos de las estaciones de servicio en la base de datos
@gas_bp.route('/insert_gas_station_data', methods=['GET'])
@login_required
@helpers.admin_required
def insert_gas_BD_station_data():
    insert_gas_station_location_data()
    insert_gas_station_distributor_data()
    insert_gas_station_data()
    insert_gas_station_supply_data()

#Insertar los precios acutualizado y las nuevas distribuidoras en la base de datos
@gas_bp.route('/update_gas_station_data', methods=['GET', 'POST'])
@login_required
@helpers.admin_required
def update_gas_stations_data():
    generate_sql_statements()
    db.update_gas_stations_data_BD()
    return render_template('admin.html')

    
    

    
