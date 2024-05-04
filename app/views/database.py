import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from geoalchemy2 import functions as geo_func
from contextlib import contextmanager
from sqlalchemy.exc import IntegrityError
from geoalchemy2 import Geography, WKTElement



from app.models import Ubicacion, Distribuidora, Gasolinera, EstacionRecarga, SuministraGasolinera, SuministraEstacionRecarga

import app.views.search as search
import app.views.helpers as helpers

import psycopg2
import json
# Database configuration
DATABASE_URL = "postgresql://marta:maniro12@postgres/GasWiseDB"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
        raise
    finally:
        session.close()

############################################################################################################
# INSERT DATA INTO THE DB USING SQLALCHEMY
############################################################################################################

# Gas station and EV: Insert location data into the database  
def insert_location_data_BD(longitud, latitud, provincia, municipio, localidad, cp, direccion):
    with session_scope() as session:
        try:
            new_location = Ubicacion(
                Provincia=provincia,
                Municipio=municipio,
                Localidad=localidad,
                CP=cp,
                Direccion=direccion,
                Location=f'SRID=4326;POINT({helpers.to_float(longitud)} {helpers.to_float(latitud)})'
            )
            session.add(new_location)
            session.commit()
        except IntegrityError:
            session.rollback()  

# Gas station and EV: Insert distributor data into the database
def insert_distributor_data_BD(nombre, latitud, longitud, mail, idApi, tipo):
    with session_scope() as session:
        try:
            new_distributor = Distribuidora(
                Nombre=nombre,
                MailPropietario=mail,
                IdAPI=idApi,
                Location=f'SRID=4326;POINT({helpers.to_float(longitud)} {helpers.to_float(latitud)})',
                Tipo=tipo
            )
            session.add(new_distributor)
            session.commit()
        except IntegrityError:
            session.rollback()

# Gas station: Insert gas station data into the database
def insert_gas_station_data_BD(id, tipo_venta, horario, margen):
    with session_scope() as session:
        try:
            new_gas_station = Gasolinera(
                IdDistribuidora=id,
                TipoVenta=tipo_venta,
                Horario=horario,
                Margen=margen
            )
            session.add(new_gas_station)
            session.commit()
        except IntegrityError:
            session.rollback()

#EV: Insert EV station data into the database
def insert_station_EV_data_BD(id, tipo_venta, precio):
    with session_scope() as session:
        try:
            new_ev_station = EstacionRecarga(
                IdDistribuidora=id,
                TipoVenta=tipo_venta,
                Precio=precio
            )
            session.add(new_ev_station)
            session.commit()
        except IntegrityError:
            session.rollback()

# Gas station: Insert gas station supply data into the database
def insert_gas_station_supply_data_BD(id_distribuidora, id_combustible, precio):
    with session_scope() as session:
        try:
            new_supply = SuministraGasolinera(
                IdDistribuidora=id_distribuidora,
                IdCombustible=id_combustible,
                Precio=helpers.to_float(precio)
            )
            session.add(new_supply)
            session.commit()
        except IntegrityError:
            session.rollback()

# EV: Insert EV station supply data into the database
def insert_station_EV_supply_data_BD(id_distribuidora, id_punto, carga_rapida, cantidad, voltaje, amperios, kW):
    with session_scope() as session:
        try:
            new_ev_supply = SuministraEstacionRecarga(
                IdDistribuidora=id_distribuidora,
                IdPunto=id_punto,
                CargaRapida=carga_rapida,
                Cantidad=cantidad,
                Voltaje=voltaje,
                Amperios=amperios,
                kW=kW
            )
            session.add(new_ev_supply)
            session.commit()
        except IntegrityError:
            session.rollback()

############################################################################################################
# SELECT DATA FROM THE DB USING SQLALCHEMY
############################################################################################################
# Gas station and EV : Get distributor ID
def get_distributor_ID(idApi):
    with session_scope() as session:
        distributor = session.query(Distribuidora).filter_by(IdAPI=idApi).first()
        return distributor.IdDistribuidora if distributor else None

#!!!Debo modificarlo para que busque en tabla Distribuidora y seleccione por tipo de distribuidora
# Get gas stations and EV stations in a given route
def get_route_distributors(tipo):
    conn = psycopg2.connect("dbname='GasWiseDB' user='marta' host='postgres' password='maniro12'")#!!!
    cur = conn.cursor()

    # Crear la consulta SQL
    puntos_sql = search.get_route_array()
    puntos_str = ',\n      '.join(puntos_sql)
    if tipo == "A":
        query = f"""
        WITH ruta AS (
        SELECT ST_Buffer(ST_MakeLine(ARRAY[{puntos_str}])::geography, 2000) AS geom
        )
        SELECT ST_AsText(g."Location")
        FROM public."Distribuidora" g, ruta r
        WHERE ST_DWithin(g."Location"::geography, r.geom, 0);
        """
    else:
        query = f"""
        WITH ruta AS (
        SELECT ST_Buffer(ST_MakeLine(ARRAY[{puntos_str}])::geography, 2000) AS geom
        )
        SELECT ST_AsText(g."Location")
        FROM public."Distribuidora" g, ruta r
        WHERE ST_DWithin(g."Location"::geography, r.geom, 0)
        AND g."Tipo" = '{tipo}';

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
        with open('app/json_data/route_distributors.json', 'w') as file:
            json.dump(coordinates_dict, file, indent=4)
    except psycopg2.Error as e:
        print(f"Error al buscar las distribuidoras en la ruta: {e}")
    finally:
        cur.close()
        conn.close()

#Get distributor info 
#!!! Con SQL pq con GeoAlchemy no me sale
def get_distributor_data(lat, lon):
    conn = psycopg2.connect("dbname='GasWiseDB' user='marta' host='postgres' password='maniro12'")#!!!
    cur = conn.cursor()

    query = f"""
    SELECT 
    d."Nombre",
    d."MailPropietario", 
    d."Tipo"
    FROM "Distribuidora" d
    WHERE ST_Equals(d."Location"::geometry, ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)::geometry);
    """

    try:
        cur.execute(query)
        results = cur.fetchone()
        if results:
            return results 
        else:
            return None
    except psycopg2.Error as e:
        print(f"Error al extraer información de la distribuidora: {e}")
        return None
    finally:
        cur.close()
        conn.close()
