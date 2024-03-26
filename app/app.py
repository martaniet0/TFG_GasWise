from flask import Flask, jsonify
import requests
import json
import psycopg2
import cargar_datos_gasolineras

app = Flask(__name__)

# Prueba
@app.route('/', methods=['GET'])
def hola_mundo():
    return jsonify({"response": "hello world"})

# Obtiene datos de la API de Gasolineras y los guarda en un archivo JSON
@app.route('/obtenerdatos', methods=['GET'])
def obtener_datos():
    # URL de la API - Reemplaza [Operacion] con la operación específica que deseas realizar
    url = 'https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres'

    try:
        # Realiza la solicitud GET a la API
        respuesta = requests.get(url)
        respuesta.raise_for_status()  # Esto lanzará un error si la solicitud falló

        # Convierte la respuesta en JSON
        datos = respuesta.json()

        # Guarda los datos en un archivo JSON
        with open('/app/datos_carburantes.json', 'w') as archivo:
            json.dump(datos, archivo, indent=4)

        return jsonify({'mensaje': 'Datos guardados correctamente en datos_carburantes.json'})

    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

# Carga los datos del archivo JSON y los devuelve como respuesta
@app.route('/cargar_datos', methods=['GET'])
def cargar_datos():
    try:
        # Abre el archivo JSON para leer los datos
        with open('app/datos_carburantes.json', 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)
        
        # Extrae la lista de estaciones de servicio
        lista_estaciones = datos["ListaEESSPrecio"]

        for estacion in lista_estaciones:
            nombre = estacion["R\u00f3tulo"]

        # Devuelve la lista procesada como respuesta JSON
        return nombre
    
    except FileNotFoundError:
        return jsonify({"error": "Archivo no encontrado"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Error al decodificar el JSON"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Inserta datos en la base de datos
@app.route('/insertar_BD', methods=['GET'])
def insertar_BD():
    try:
        # Conexión a la base de datos
        conn = psycopg2.connect("dbname='GasWiseDB' user='marta' host='postgres' password='maniro12'")
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO public."Distribuidora" ("Nombre", "Latitud", "Longitud", "MailPropietario")
            VALUES ('LOLA', 39.211417, -1.539167, NULL);"""
            )  
        conn.commit()  # Confirma los cambios en la base de datos

        cur.close()
        conn.close()

        return "Datos insertados correctamente"
    except psycopg2.Error as e:
        return {"error": str(e)}, 500
    except Exception as e:
        return {"error": str(e)}, 500

# Carga los datos del archivo JSON en la base de datos
@app.route('/cargar_datos_BD', methods=['GET'])
def cargar_datos_BD():
    try:
        # Abre el archivo JSON para leer los datos
        with open('app/datos_carburantes.json', 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)
        
        # Conexión a la base de datos
        conn = psycopg2.connect("dbname='GasWiseDB' user='marta' host='postgres' password='maniro12'")
        cur = conn.cursor()
        
        # Extrae la lista de estaciones de servicio
        lista_estaciones = datos["ListaEESSPrecio"]

        for estacion in lista_estaciones:
            nombre = estacion["R\u00f3tulo"]
            
            # Inserta o actualiza el horario en la base de datos para cada estación
            cur.execute(
                """INSERT INTO public."Distribuidora" ("Nombre", "Latitud", "Longitud", "MailPropietario")
                VALUES (%s, %s, %s, %s);
                """,
                (nombre, 39.211417, -1.539167, None)
            )

        conn.commit()  # Confirma los cambios en la base de datos
        
        # Cierra la conexión
        cur.close()
        conn.close()

        return jsonify({"mensaje": "Datos cargados correctamente"})
    
    except FileNotFoundError:
        return jsonify({"error": "Archivo no encontrado"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Error al decodificar el JSON"}), 500
    except psycopg2.Error as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/cargar_datos_BD_ubicacion', methods=['GET'])
def cargar_datos_BD_ubicacion():
    try:
        with open('app/datos_carburantes.json', 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)

        lista_estaciones = datos["ListaEESSPrecio"]

        for estacion in lista_estaciones:
            cp = estacion["C.P."]
            direccion = estacion["Direcci\u00f3n"]
            latitud = estacion["Latitud"]
            localidad = estacion["Localidad"]
            longitud = estacion["Longitud (WGS84)"]
            municipio = estacion["Municipio"]
            provincia = estacion["Provincia"]
            cargar_datos_gasolineras.insertar_Ubicacion_BD(longitud, latitud, provincia, municipio, localidad, cp, direccion)


        return "Datos cargados correctamente"
    
    except FileNotFoundError:
        return "Archivo no encontrado", 404
    except json.JSONDecodeError:
        return "Error al decodificar el JSON", 500
    except psycopg2.Error as e:
        return str(e), 500
    except Exception as e:
        return str(e), 500   

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
            ideess = estacion["IDEESS"]
            cargar_datos_gasolineras.insertar_Distribuidora_BD(nombre, latitud, longitud, mail, ideess)


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
            ideess = estacion["IDEESS"]
            id = cargar_datos_gasolineras.obtener_ID_distribuidora(ideess)
            if estacion["Tipo Venta"] == 'P':
                tipo_venta = True
            elif estacion["Tipo Venta"] == 'R':
                tipo_venta = False
            else:
                tipo_venta = None
            horario = estacion["Horario"]
            margen = estacion["Margen"]
            cargar_datos_gasolineras.insertar_Gasolinera_BD(id, tipo_venta, horario, margen)


        return "Datos cargados correctamente"
    
    except FileNotFoundError:
        return "Archivo no encontrado", 404
    except json.JSONDecodeError:
        return "Error al decodificar el JSON", 500
    except psycopg2.Error as e:
        return str(e), 500
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=4000, debug=True)

