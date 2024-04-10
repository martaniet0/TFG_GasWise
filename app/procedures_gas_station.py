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

        return 'Datos guardados correctamente en data_gas_stations.json'

    except requests.RequestException as e:
        return f"Error inesperado: {e}", 500   

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

# Insert location data of an EV station into the database
def insert_gas_station_location_data():
    data = open_file_gas_stations()   

    lista_estaciones = data["ListaEESSPrecio"]

    for estacion in lista_estaciones:
        cp = estacion["C.P."]
        direccion = estacion["Direcci\u00f3n"]
        latitud = estacion["Latitud"]
        localidad = estacion["Localidad"]
        longitud = estacion["Longitud (WGS84)"]
        municipio = estacion["Municipio"]
        provincia = estacion["Provincia"]

        db.insert_location_data_BD(longitud, latitud, provincia, municipio, localidad, cp, direccion)

    
def insertar_Distribuidora_BD(nombre, latitud, longitud, mail, idApi):
    conn, cur = db.conectar_BD()
    try:
        cur.execute(
            """INSERT INTO public."Distribuidora" ("Nombre", "Latitud", "Longitud", "MailPropietario", "IdAPI")
            VALUES (%s, %s, %s, %s, %s);""",
            (nombre, helpers.to_float(latitud), helpers.to_float(longitud), mail, idApi)
        )  
        conn.commit()  
    except psycopg2.IntegrityError:
        conn.rollback()
    finally:
        db.desconectar_BD(cur, conn)

    return "Datos insertados correctamente en la tabla Distribuidora"
    
def insertar_Gasolinera_BD(id, tipo_venta, horario, margen):
    conn, cur = db.conectar_BD()
    try: 
        cur.execute(
            """INSERT INTO public."Gasolinera" ("IdDistribuidora", "TipoVenta", "Horario", "Margen")
            VALUES (%s, %s, %s, %s);""",
            (id, tipo_venta, horario, margen)
            )  
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()  
    finally:
        db.desconectar_BD(cur, conn)

    return "Datos insertados correctamente en la tabla Gasolinera"

def insertar_SuministraGasolinera_BD(id_distribuidora, id_combustible, precio):
    conn, cur = db.conectar_BD()
    try:
        cur.execute(
            """INSERT INTO public."SuministraGasolinera" ("IdDistribuidora", "IdCombustible", "Precio")
            VALUES (%s, %s, %s);""",
            (id_distribuidora, id_combustible, helpers.to_float(precio))
            )  
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()  
    finally:
        db.desconectar_BD(cur, conn)

    return "Datos insertados correctamente en la tabla SuministraGasolinera"

def obtener_ID_distribuidora(idApi):
    conn, cur = db.conectar_BD()
    cur.execute(
        """SELECT "IdDistribuidora" FROM public."Distribuidora"
        WHERE "IdAPI" = %s;""",
        (idApi,)
    )
    result = cur.fetchone()
    db.desconectar_BD(cur, conn)

    if len(result)==1:
        return result[0]
    else:
        return None
    
    
def obtener_ID_combustible(combustible):
    conn, cur = db.conectar_BD()
    cur.execute(
        """SELECT "IdCombustible" FROM public."TipoCombustible"
        WHERE "Nombre" = %s;""",
        (combustible,)
    )
    result = cur.fetchone()
    db.desconectar_BD(cur, conn)
    
    if len(result)==1:
        return result[0]
    else:
        return None
    #return result[0] if len(result) == 1 else None
    
