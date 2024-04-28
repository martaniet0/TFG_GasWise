import psycopg2
import app.views.helpers as helpers
import app.views.search as search
import json
import re

############################################################################################################
#CONNECTION AND DISCONNECTION TO THE DB
############################################################################################################

def connect_BD():
    try:
        conn = psycopg2.connect("dbname='GasWiseDB' user='marta' host='postgres' password='maniro12'")
        cur = conn.cursor()
        return conn, cur
    except psycopg2.Error as e:
        return {"error": str(e)}, 500
    except Exception as e:
        return {"error": str(e)}, 500
    
def disconnect_BD(cur, conn):
    try:
        cur.close()
        conn.close()
    except psycopg2.Error as e:
        return {"error": str(e)}, 500
    except Exception as e:
        return {"error": str(e)}, 500
    
############################################################################################################
#INSERT DATA INTO THE DB
############################################################################################################

# Gas station and EV: Insert location data into the database  
def insert_location_data_BD(longitud, latitud, provincia, municipio, localidad, cp, direccion):
    conn, cur = connect_BD()
    try:
        cur.execute(
            """INSERT INTO public."Ubicacion"("Longitud", "Latitud", "Provincia", "Municipio", "Localidad", "CP", "Direccion")
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (helpers.to_float(longitud), helpers.to_float(latitud), provincia, municipio, localidad, cp, direccion)
        )
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error al insertar en la BD: {e}")
        conn.rollback()
    finally:
        disconnect_BD(cur, conn)

# !!!Gas station and EV: Insert location data into the database  
def insert_location_data_BD2(longitud, latitud, provincia, municipio, localidad, cp, direccion):
    conn, cur = connect_BD()
    try:
        cur.execute(
            """INSERT INTO public."Prueba_ubicacion" ("location")
            VALUES (ST_MakePoint(%s, %s)::geography)""",
            (helpers.to_float(longitud), helpers.to_float(latitud))
        )        
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error al insertar en la BD: {e}")
        conn.rollback()
    finally:
        disconnect_BD(cur, conn)


# Gas station and EV: Insert distributor data into the database
def insert_distributor_data_BD(nombre, latitud, longitud, mail, idApi):
    conn, cur = connect_BD()
    try:
        cur.execute(
            """INSERT INTO public."Distribuidora"("Nombre", "Latitud", "Longitud", "MailPropietario", "IdAPI")
            VALUES (%s, %s, %s, %s, %s)""",
            (nombre, helpers.to_float(latitud), helpers.to_float(longitud), mail, idApi)
        )
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error al insertar en la BD: {e}")
        conn.rollback()
    finally:
        disconnect_BD(cur, conn)

# Gas station: Insert gas station data into the database
def insert_gas_station_data_BD(id, tipo_venta, horario, margen):
    conn, cur = connect_BD()
    try:
        cur.execute(
            """INSERT INTO public."Gasolinera" ("IdDistribuidora", "TipoVenta", "Horario", "Margen")
            VALUES (%s, %s, %s, %s);""",
            (id, tipo_venta, horario, margen)
        )
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error al insertar en la BD: {e}")
        conn.rollback()
    finally:
        disconnect_BD(cur, conn)

#EV: Insert EV station data into the database
def insert_station_EV_data_BD(id, tipo_venta, precio):
    conn, cur = connect_BD()
    try:
        cur.execute(
            """INSERT INTO public."EstacionRecarga"("IdDistribuidora", "TipoVenta", "Precio")
            VALUES (%s, %s, %s)""",
            (id, tipo_venta, precio)
        )
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error al insertar en la BD: {e}")
        conn.rollback()
    finally:
        disconnect_BD(cur, conn)

# Gas station: Insert gas station supply data into the database
def insert_gas_station_supply_data_BD(id_distribuidora, id_combustible, precio):
    conn, cur = connect_BD()
    try:
        cur.execute(
            """INSERT INTO public."SuministraGasolinera" ("IdDistribuidora", "IdCombustible", "Precio")
            VALUES (%s, %s, %s);""",
            (id_distribuidora, id_combustible, helpers.to_float(precio))
        )
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error al insertar en la BD: {e}")
        conn.rollback()
    finally:
        disconnect_BD(cur, conn)
    
# EV: Insert EV station supply data into the database
def insert_station_EV_supply_data_BD(id_distribuidora, id_punto, carga_rapida, cantidad, voltaje, amperios, kW):
    conn, cur = connect_BD()
    try:
        cur.execute(
            """INSERT INTO public."SuministraEstacionRecarga" ("IdDistribuidora", "IdPunto", "CargaRapida", "Cantidad", "Voltaje", "Amperios", "kW")
            VALUES (%s, %s, %s, %s, %s, %s, %s);""",
            #!!! Mirar si es necesario cambiar a int o float
            (id_distribuidora, id_punto, carga_rapida, cantidad, voltaje, amperios, kW)
        )
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error al insertar en la BD: {e}")
        conn.rollback()
    finally:
        disconnect_BD(cur, conn)

############################################################################################################
#SELECT DATA FROM THE DB
############################################################################################################
# Gas station and EV : Get distributor ID
def get_distributor_ID(idApi):
    conn, cur = connect_BD()
    try:
        cur.execute(
            """SELECT "IdDistribuidora" FROM public."Distribuidora"
            WHERE "IdAPI" = %s;""",
            (idApi,)
        )
        result = cur.fetchone()
        return result[0] if result is not None and len(result) == 1 else None
    
    except psycopg2.Error as e:
        print(f"Error al obtener datos de la BD: {e}")
    finally:
        disconnect_BD(cur, conn)

# Get gas stations and EV stations in a given route
#!!! Devuelve las coordenadas en orden contrario!!! 
def get_route_distributors():
    conn, cur = connect_BD()
    # Crear la consulta SQL
    puntos_sql = search.get_route_array()
    puntos_str = ',\n      '.join(puntos_sql)
    query = f"""
    WITH ruta AS (
      SELECT ST_Buffer(ST_MakeLine(ARRAY[{puntos_str}])::geography, 2000) AS geom
    )
    SELECT ST_AsText(g.location)
    FROM public."Prueba_ubicacion" g, ruta r
    WHERE ST_DWithin(g.location::geography, r.geom, 0);
    """

    try:
        cur.execute(query)
        results = cur.fetchall()
        coordinates_list = []
        for result in results:
            # Extraer coordenadas usando regex
            coords = re.findall(r"[-\d\.]+", result[0])
            if coords:
                # Agregar como lista de flotantes [latitud, longitud]
                coordinates_list.append([float(coords[1]), float(coords[0])])

        # Preparar el diccionario con la clave "coordinates"
        coordinates_dict = {"coordinates": coordinates_list}

        # Escribe el diccionario de coordenadas en un archivo JSON
        with open('/app/distributor_search/route_distributors.json', 'w') as file:
            json.dump(coordinates_dict, file, indent=4)
    except psycopg2.Error as e:
        print(f"Error al buscar las distribuidoras en la ruta: {e}")
    finally:
        disconnect_BD(cur, conn)


