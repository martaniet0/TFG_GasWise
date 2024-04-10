import json

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

