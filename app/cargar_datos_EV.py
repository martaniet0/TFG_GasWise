import psycopg2
import helpers as helpers
import bd as bd
import json

def insert_location_data_BD_EV():
    try:
        with open('app/data_EV_stations.json', 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)

        for estacion in datos:
            address_info = estacion.get("AddressInfo", {})
            latitud = address_info.get("Latitude")
            longitud = address_info.get("Longitude")
            provincia = None
            municipio = None
            localidad = None
            cp = address_info.get("Postcode")
            direccion = address_info.get("AddressLine1")

            # Asegúrate de adaptar el nombre de la tabla y las columnas según tu esquema de base de datos.
            bd.insertar_Ubicacion_BD(longitud, latitud, provincia, municipio, localidad, cp, direccion)

        return "Datos cargados correctamente"

    except FileNotFoundError:
        return "Archivo no encontrado", 404
    except json.JSONDecodeError:
        return "Error al decodificar el JSON", 500
    except Exception as e:
        return f"Error inesperado: {e}", 500