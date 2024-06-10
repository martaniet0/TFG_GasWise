import json, csv, os
from app.models import Conductor, Propietario
from flask_login import current_user, login_required
from functools import wraps
from flask import redirect, url_for, flash

def to_float(n):    
    try:
        if n is None:
            return None
        # Reemplaza coma por punto y luego convierte el string a float
        n = str(n).replace(',', '.')
        n_float = float(n)
        return n_float
    except ValueError:
        return "No se pudo convertir el string a real", 400
      
def extract_usage_cost_EV():
    try:
        usage_costs = []

        # Abre y carga el JSON
        with open('app/data_EV_stations.json', 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)

        # Recorre cada elemento de la lista principal (cada estación)
        for elemento in datos:
            if "UsageCost" in elemento:
                usage_cost = elemento["UsageCost"]
                
                # Asegúrate de que el costo de uso no esté vacío o nulo antes de agregarlo
                if usage_cost and usage_cost not in usage_costs:
                    usage_costs.append(usage_cost)

        # Devuelve todos los costos de uso extraídos como respuesta JSON
        return {"usage_costs": usage_costs}
    
    except FileNotFoundError:
        return {"error": "Archivo no encontrado"}, 404
    except json.JSONDecodeError:
        return {"error": "Error al decodificar el JSON"}, 500
    except Exception as e:
        return {"error": str(e)}, 500

#Get the dictionary key based on the value
def get_key(val, dic):
    for key, value in dic.items():
         if val == value:
             return key
    return None

#Check if the user is a driver or owner
def user_type():
    if isinstance(current_user, Conductor):
        return "C"
    elif isinstance(current_user, Propietario):
        return "P"
    return None 

#Obtener el tipo de distribuidora por defecto dado el tipo de vehiculo del conductor actual
def get_default_distributor():
    if user_type() == "C":
        if current_user.TipoVehiculo == "E" or current_user.TipoVehiculo == "H":
            return "E"
        elif current_user.TipoVehiculo == "G" or current_user.TipoVehiculo == "D":
            return "G"
    return None

#Write data to a CSV file
def write_to_file(filename, data):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(data)

def read_csv_data(filename):
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        if os.path.getsize(filename) == 0:
            return None
        return [row for row in reader]

############################################################################################################
#DECORATORS
############################################################################################################
#Decorator to check if the user is a driver
def driver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or user_type() != "C":
            flash('Esa página solo es accesible para conductores.', 'warning')
            return redirect(url_for('users.home_owner'))
        return f(*args, **kwargs)
    return decorated_function

#Decorator to check if the user is an owner
def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or user_type() != "P":
            flash('Esa página solo es accesible para propietarios.', 'warning')
            return redirect(url_for('search.mapa'))
        return f(*args, **kwargs)
    return decorated_function

