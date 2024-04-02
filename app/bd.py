import psycopg2
import helpers

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
            """INSERT INTO public."Ubicacion"(latitud, longitud, provincia, municipio, localidad, cp, direccion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (helpers.to_float(longitud), helpers.to_float(latitud), provincia, municipio, localidad, cp, direccion)
        )
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error al insertar en la BD: {e}")
        conn.rollback()
    finally:
        desconectar_BD(cur, conn)