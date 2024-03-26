import psycopg2
import helpers as helpers

def conectar_BD():
    try:
        conn = psycopg2.connect("dbname='GasWiseDB' user='marta' host='postgres' password='maniro12'")
        cur = conn.cursor()
        return conn, cur
    except psycopg2.Error as e:
        return {"error": str(e)}, 500
    except Exception as e:
        return {"error": str(e)}, 500
    
def desconectar_BD(cur, conn):
    try:
        cur.close()
        conn.close()
    except psycopg2.Error as e:
        return {"error": str(e)}, 500
    except Exception as e:
        return {"error": str(e)}, 500

def insertar_Ubicacion_BD(longitud, latitud, provincia, municipio, localidad, cp, direccion):
    conn, cur = conectar_BD()
    try:
        cur.execute(
            """INSERT INTO public."Ubicacion" ("Longitud", "Latitud", "Provincia", "Municipio", "Localidad", "CP", "Direccion")
            VALUES (%s, %s, %s, %s, %s, %s, %s);""",
            (helpers.to_float(longitud), helpers.to_float(latitud), provincia, municipio, localidad, cp, direccion)
        )
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
    finally:
        desconectar_BD(cur, conn)

    return "Datos insertados correctamente en la tabla Ubicación"

    
def insertar_Distribuidora_BD(nombre, latitud, longitud, mail, ideess):
    conn, cur = conectar_BD()
    try:
        cur.execute(
            """INSERT INTO public."Distribuidora" ("Nombre", "Latitud", "Longitud", "MailPropietario", "IDEESS")
            VALUES (%s, %s, %s, %s, %s);""",
            (nombre, helpers.to_float(latitud), helpers.to_float(longitud), mail, ideess)
        )  
        conn.commit()  
    except psycopg2.IntegrityError:
        conn.rollback()
    finally:
        desconectar_BD(cur, conn)

    return "Datos insertados correctamente en la tabla Distribuidora"
    
def insertar_Gasolinera_BD(id, tipo_venta, horario, margen):
    conn, cur = conectar_BD()
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
        desconectar_BD(cur, conn)

    return "Datos insertados correctamente en la tabla Gasolinera"

def insertar_SuministraGasolinera_BD(id_distribuidora, id_combustible, precio):
    conn, cur = conectar_BD()
    cur.execute(
        """INSERT INTO public."SuministraGasolinera" ("IdDistribuidora", "IdCombustible", "Precio")
        VALUES (%s, %s, %s);""",
        (id_distribuidora, id_combustible, precio)
        )  
    conn.commit()  

    desconectar_BD(cur, conn)

    return "Datos insertados correctamente en la tabla SuministraGasolinera"

def obtener_ID_distribuidora(ideess):
    conn, cur = conectar_BD()
    cur.execute(
        """SELECT "IdDistribuidora" FROM public."Distribuidora"
        WHERE "IDEESS" = %s;""",
        (ideess)
    )
    result = cur.fetchone()
    desconectar_BD(cur, conn)
    if len(result)==1:
        return result
    else:
        return None
    
def obtener_ID_combustible(combustible):
    conn, cur = conectar_BD()
    cur.execute(
        """SELECT "IdCombustible" FROM public."TipoCombustible"
        WHERE "Nombre" = %s;""",
        (combustible)
    )
    result = cur.fetchone()
    desconectar_BD(cur, conn)
    if len(result)==1:
        return result
    else:
        return None