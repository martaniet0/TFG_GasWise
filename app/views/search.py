from flask import request, jsonify, Blueprint, render_template
from flask_login import login_required

import app.views.database as db
import app.views.helpers as helpers
import json
import requests

search_bp = Blueprint('search', __name__)

headers = {
    'User-Agent': 'gasWise/1.0',
    'Referer': 'http://gaswise.com'
}

#Open JSON file with data of gas stations
def open_file_route_coordinates():
    try:
        with open('app/json_data/route_coordinates.json', 'r', encoding='utf-8') as file:
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

    points_sql = [f"ST_MakePoint({coord[0]}, {coord[1]})::geometry" for coord in coordinates]

    return points_sql

### NUEVO ###
def get_info_route_coordinates(origin_lon, origin_lat, destination_lon, destination_lat):
    url = f'https://router.project-osrm.org/route/v1/driving/{origin_lat},{origin_lon};{destination_lat},{destination_lon}?overview=full&geometries=geojson'
    
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()  # Esto lanzará un error si la solicitud falló

        datos = r.json()

        with open('app/json_data/route_coordinates.json', 'w') as archivo:
            json.dump(datos, archivo, indent=4)

    except requests.RequestException as e:
        return f"Error al intentar guardar los datos de la ruta: {e}", 500   


def get_coordinates(place_name):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={place_name}"
    response = requests.get(url, headers=headers)
    data = response.json()
    with open('app/json_data/locations.json', 'w') as file:
        file.write(json.dumps(data, indent=4))
    if data:
        return data[0]['lat'], data[0]['lon']
    return None, None

def get_country(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    response = requests.get(url, headers=headers)
    data = response.json()
    if data:
        return data['address']['country_code']
    return None

def get_CCAA_code(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    response = requests.get(url,headers=headers)
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
        return None  
    
############################################################################################################
#RUTAS
############################################################################################################

#Ruta para obtener el mapa
@search_bp.route('/mapa', methods=['GET'])
@login_required
@helpers.driver_required
def mapa():
    return render_template('map.html')

#Ruta para obtener la ruta entre dos puntos y las distribuidoras que se encuentran en ella
#param: tipo_distribuidora y filtros
#!!! Sin terminar
@search_bp.route('/get_route_with_distributors')
def get_route_with_distributors():
    origin = request.args.get('origin')
    destination = request.args.get('destination')

    if not origin or not destination:
        return jsonify({'error': 'Ruta no disponible: se deben proporcionar origen y destino'}), 400

    origin_coordinates = get_coordinates(origin)
    destination_coordinates = get_coordinates(destination)


    if origin_coordinates == (None, None) or destination_coordinates == (None, None):
        return jsonify({'error': 'Ruta no disponible: no se encontraron coordenadas para los puntos proporcionados'}), 400

    origin_country = get_country(*origin_coordinates)
    destination_country = get_country(*destination_coordinates)

    if origin_country != 'es' or destination_country != 'es':
        return jsonify({'error': 'Ruta no disponible: ruta fuera de España'}), 400
    
    water_route = check_route_on_water(*origin_coordinates, *destination_coordinates)
    if water_route:
        return jsonify({'error': 'Ruta no disponible: conexión marítima entre origen y destino.'}), 400

    get_info_route_coordinates(*origin_coordinates, *destination_coordinates)
    
    tipo = helpers.get_default_distributor()
    db.get_route_distributors(tipo)

    # Obtener todos los parámetros adicionales de forma dinámica
    extra_params = {key: value for key, value in request.args.items() if key.startswith('param')}

    if extra_params:
        tipo = db.get_route_distributors(tipo, **extra_params)
    else:
        db.get_route_distributors(tipo)

    try:
        with open('app/json_data/route_coordinates.json', 'r') as file:
            route = json.load(file)
        with open('app/json_data/route_distributors.json', 'r') as file:
            distributors = json.load(file)

        json_data = json.dumps({'route': route, 'tipo':tipo, 'distributors': distributors})

        return json_data
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
#Ruta para obtener las distribuidoras cercanas a un punto 
@search_bp.route('/get_nearest_distributors', methods=['GET'])
def get_nearest_distributors():
    origin = request.args.get('origin')

    if not origin:
        return jsonify({'error': 'Búsqueda errónea: se deben proporcionar origen'}), 400

    origin_coordinates = get_coordinates(origin)
    if origin_coordinates == (None, None):
        return jsonify({'error': 'Búsqueda errónea: no se encontraron coordenadas para los puntos proporcionados'}), 400

    origin_country = get_country(*origin_coordinates)
    if origin_country != 'es':
        return jsonify({'error': 'Búsqueda errónea: localización fuera de España'}), 400
    
    tipo = helpers.get_default_distributor()

    # Obtener todos los parámetros adicionales de forma dinámica
    extra_params = {key: value for key, value in request.args.items() if key.startswith('param')}

    if extra_params:
        tipo = db.get_nearest_distributors(origin_coordinates[0], origin_coordinates[1], tipo, **extra_params)
    else:
        db.get_nearest_distributors(origin_coordinates[0], origin_coordinates[1], tipo)

    try:
        with open('app/json_data/nearest_distributors.json', 'r') as file:
            distributors = json.load(file)

        json_data = json.dumps({'origin': origin_coordinates, 'tipo':tipo, 'distributors': distributors})

        return json_data
    except Exception as e:
        return jsonify({'error': str(e)}), 500



#Ruta para obtener la información (corta) de una distribuidora en el pop up del mapa
#param: latitud y longitud
@search_bp.route('/get_distributor_info/<lat>/<lon>')
def get_distributor_info(lat, lon):
    data, lat, lon = db.get_distributor_data(lat, lon, None)

    if data is None:
        return jsonify({'error': 'No se encontraron datos para la ubicación proporcionada'}), 400

    if data[2] == 'E':
        response = {
            'Nombre': data[0],
            'Tipo_venta': data[3],
            'Precio': data[4]
        }
    else:
        tipo_venta = 'Pública' if data[3] else 'Restringida a socios o cooperativistas'
        margen = 'Derecho' if data[5] == 'D' else 'Izquierdo' if data[5] == 'I' else None
        response = {
            'Nombre': data[0],
            'Tipo_venta': tipo_venta,
            'Email': data[1],
            'Horario': data[4],
            'Margen': margen
        }

    return jsonify(response)

#Ruta para obtener la info de un listado de distribuidoras
@search_bp.route('/get_distributors_list', methods=['GET'])
def get_distributors_list():
    with open('app/json_data/nearest_distributors.json', 'r') as file:
        data = json.load(file)

    distributors_info = []

    # Iterate through each coordinate set
    for distributor in data["coordinates"]:
        latitud = helpers.to_float(distributor[0])
        longitud = helpers.to_float(distributor[1])
        
        distributor_data, lat, lon = db.get_distributor_data(latitud, longitud, None)
        
        if distributor_data:
            distributors_info.append({
                'info': distributor_data,
                'lat': lat,
                'lon': lon
            })
        else:
            distributors_info.append({
                'info': None,
                'lat': lat,
                'lon': lon
            })

    final_distributors_info = []

    # Process each distributor info
    for distributor in distributors_info:
        info = distributor['info']
        if info:
            if info[2] == 'E':
                distributor_info = {
                    'Nombre': info[0],
                    'Tipo_venta': info[3],
                    'Precio': info[4], 
                    'lat': distributor['lat'],
                    'lon': distributor['lon']
                }
            else:
                tipo_venta = 'Pública' if info[3] else 'Restringida a socios o cooperativistas'
                margen = 'Derecho' if info[5] == 'D' else 'Izquierdo' if info[5] == 'I' else None
                distributor_info = {
                    'Nombre': info[0],
                    'Tipo_venta': tipo_venta,
                    'Email': info[1],
                    'Horario': info[4],
                    'Margen': margen,  
                    'lat': distributor['lat'],
                    'lon': distributor['lon']
                }
            
            final_distributors_info.append(distributor_info)

    return render_template('distributors_list.html', distributors=final_distributors_info)

#!!!NUEVO
#Ruta para obtener posibles localizaciones de un lugar
@search_bp.route('/get_locations', methods=['GET'])
def get_locations():
    place_name = request.args.get('origin') or request.args.get('destination')
    
    if not place_name:
        return jsonify({'error': 'Parámetro "origin" o "destination" es necesario'}), 400

    # Obtener locations.json
    get_coordinates(place_name)

    # Leer el archivo locations.json
    with open('app/json_data/locations.json', 'r', encoding='utf-8') as f:
        locations = json.load(f)
    
    filtered_places = []

    for location in locations:
        lat = location['lat']
        lon = location['lon']
        country = get_country(lat,lon)
        if country == 'es':
            filtered_places.append({
                'Nombre': location['display_name']
            })

    return jsonify({'places': filtered_places})
