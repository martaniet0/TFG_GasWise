from flask import request
import db as db
import json
import requests
from flask import jsonify
from routes import app

#Habría que hacer una función para guardar datos en json de la ruta

#Open JSON file with data of gas stations
def open_file_route_coordinates():
    try:
        with open('/app/distributor_search/route_coordinates.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    except FileNotFoundError:
        return "Archivo no encontrado", 404
    except json.JSONDecodeError:
        return "Error al decodificar el JSON", 500
    except Exception as e:
        return f"Error inesperado: {e}", 500

# Get the route coordinates to insert in a SQL query
def get_route_array():
    data = open_file_route_coordinates()  

    coordinates = data["routes"][0]["geometry"]["coordinates"]

    points_sql = [f"ST_MakePoint({coord[1]}, {coord[0]})::geometry" for coord in coordinates]

    return points_sql

### NUEVO ###
def get_info_route_coordinates(origin_lon, origin_lat, destination_lon, destination_lat):
    url = f'https://router.project-osrm.org/route/v1/driving/{origin_lon},{origin_lat};{destination_lon},{destination_lat}?overview=full&geometries=geojson'


    try:
        r = requests.get(url)
        r.raise_for_status()  # Esto lanzará un error si la solicitud falló

        datos = r.json()

        with open('/app/distributor_search/route_coordinates.json', 'w') as archivo:
            json.dump(datos, archivo, indent=4)

    except requests.RequestException as e:
        return f"Error al intentar guardar los datos de la ruta: {e}", 500   


def get_coordinates(place_name):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={place_name}"
    response = requests.get(url)
    data = response.json()
    if data:
        return data[0]['lat'], data[0]['lon']
    return None, None

def get_country(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    response = requests.get(url)
    data = response.json()
    if data:
        return data['address']['country_code']
    return None

def get_CCAA_code(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('address', {}).get('ISO3166-2-lvl4', None)
    else:
        raise Exception(f"Error al obtener código CCAA: HTTP {response.status_code}")

def check_route_on_water(origin_lat, origin_lon, destination_lat, destination_lon):
    try:
        origin_region = get_CCAA_code(origin_lat, origin_lon)
        destination_region = get_CCAA_code(destination_lat, destination_lon)

        not_peninsular = ['ES-CN', 'ES-CE', 'ES-ML', 'ES-IB']
        is_origin_not_peninsular = origin_region in not_peninsular
        is_destination_not_peninsular = destination_region in not_peninsular

        if is_origin_not_peninsular and is_destination_not_peninsular:
            if origin_region == destination_region:
                return False
            elif ((origin_region == 'ES-CE' and destination_region == 'ES-ML') or
                  (origin_region == 'ES-ML' and destination_region == 'ES-CE')):
                return False
            else:
                return True
        elif is_origin_not_peninsular or is_destination_not_peninsular:
            return True
        else:
            return False
    except Exception as e:
        print(str(e))
        return None  # or raise an error

@app.route('/get_route_with_distributors', methods=['GET'])
def get_route_with_distributors():
    origin = request.args.get('origin')
    destination = request.args.get('destination')

    origin_coordinates = get_coordinates(origin)
    destination_coordinates = get_coordinates(destination)

    if not origin_coordinates or not destination_coordinates:
        return "No se encontraron coordenadas para los puntos proporcionados", 404

    origin_country = get_country(*origin_coordinates)
    destination_country = get_country(*destination_coordinates)

    if origin_country != 'es' or destination_country != 'es':
        return "Solo se permiten rutas en España", 400
    
    water_route = check_route_on_water(*origin_coordinates, *destination_coordinates)
    if water_route:
        return "La ruta no puede ser sobre el agua", 400

    get_info_route_coordinates(*origin_coordinates, *destination_coordinates)
    db.get_route_distributors()

    try:
        with open('/app/distributor_search/route_coordinates.json', 'r') as file:
            route = json.load(file)
        with open('/app/distributor_search/route_distrbutors.json', 'r') as file:
            distributors = json.load(file)
        return jsonify({'route': route, 'distributors': distributors})
    except Exception as e:
        return jsonify({'error': str(e)}), 500