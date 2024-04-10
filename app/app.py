from flask import Flask, jsonify
import requests
import json
import psycopg2
import procedures_gas_station as procedures_gas_station
import app.procedures_EV_station as procedures_EV_station
import helpers as helpers
from app.procedures_EV_station import insert_location_data

app = Flask(__name__)

@app.route('/', methods=['GET'])
def hola_mundo():
    return "Hola mundo"

#https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/help

############################################################################################################
#GASOLINERAS
############################################################################################################

#Insert gas stations data into the database
@app.route('/insert_data_BD_gas_stations', methods=['GET'])
def insert_location_data_BD_gas_stations():
    procedures_gas_station.insert_gas_station_location_data()
    procedures_gas_station.insert_gas_station_distributor_data()
    procedures_gas_station.insert_gas_station_data()
    procedures_gas_station.insert_gas_station_supply_data()
    
    return "Datos cargados correctamente"

@app.route('/cargar_datos_BD_distribuidora', methods=['GET'])
def cargar_datos_BD_distribuidora():
    try:
        with open('app/datos_carburantes.json', 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)

        lista_estaciones = datos["ListaEESSPrecio"]

        for estacion in lista_estaciones:
            nombre= estacion["R\u00f3tulo"]
            latitud = estacion["Latitud"]
            longitud = estacion["Longitud (WGS84)"]
            mail = None
            idApi = estacion["IDEESS"]
            procedures_gas_station.insertar_Distribuidora_BD(nombre, latitud, longitud, mail, idApi)


        return "Datos cargados correctamente"
    
    except FileNotFoundError:
        return "Archivo no encontrado", 404
    except json.JSONDecodeError:
        return "Error al decodificar el JSON", 500
    except psycopg2.Error as e:
        return str(e), 500
    except Exception as e:
        return str(e), 500

@app.route('/cargar_datos_BD_gasolinera', methods=['GET'])
def cargar_datos_BD_gasolinera():
    try:
        with open('app/datos_carburantes.json', 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)

        lista_estaciones = datos["ListaEESSPrecio"]

        for estacion in lista_estaciones:
            idApi = estacion["IDEESS"]
            id = procedures_gas_station.obtener_ID_distribuidora(idApi)
            if estacion["Tipo Venta"] == 'P':
                tipo_venta = True
            elif estacion["Tipo Venta"] == 'R':
                tipo_venta = False
            else:
                tipo_venta = None
            horario = estacion["Horario"]
            margen = estacion["Margen"]
            procedures_gas_station.insertar_Gasolinera_BD(id, tipo_venta, horario, margen)


        return "Datos cargados correctamente"
    
    except FileNotFoundError:
        return "Archivo no encontrado", 404
    except json.JSONDecodeError:
        return "Error al decodificar el JSON", 500
    except psycopg2.Error as e:
        return str(e), 500
    except Exception as e:
        return str(e), 500

@app.route('/cargar_datos_BD_precios', methods=['GET'])
def cargar_datos_BD_precios():
    try:
        with open('app/datos_carburantes.json', 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)

        lista_estaciones = datos["ListaEESSPrecio"]

        for estacion in lista_estaciones:
            idApi = estacion["IDEESS"]
            id_distribuidora = procedures_gas_station.obtener_ID_distribuidora(str(idApi))
            i=0
            for combustible in lista_combustibles:
                id_combustible = procedures_gas_station.obtener_ID_combustible(lista_combustibles[i]) 
                precio = estacion["Precio {}".format(combustible)] if estacion["Precio {}".format(combustible)] != '' else 0.0
                if precio != 0.0:
                    procedures_gas_station.insertar_SuministraGasolinera_BD(id_distribuidora, id_combustible, precio)
                i+=1

        return "Datos cargados correctamente"
    
    except FileNotFoundError:
        return "Archivo no encontrado", 404
    except json.JSONDecodeError:
        return "Error al decodificar el JSON", 500
    except psycopg2.Error as e:
        return str(e), 500
    except Exception as e:
        return str(e), 500

############################################################################################################ 
#ESTACIONES DE RECARGA
############################################################################################################
    

#Insert EV stations data into the database
@app.route('/insert_data_BD_EV_stations', methods=['GET'])
def insert_location_data_BD_EV_stations():
    procedures_EV_station.insert_EV_station_location_data()
    procedures_EV_station.insert_EV_station_distributor_data()
    procedures_EV_station.insert_EV_station_data()
    procedures_EV_station.insert_EV_station_supply_data()
    
    return "Datos cargados correctamente"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=4000, debug=True)

