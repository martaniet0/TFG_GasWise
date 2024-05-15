import re

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy.exc import IntegrityError


from app.models import Ubicacion, Distribuidora, Gasolinera, EstacionRecarga, SuministraGasolinera, SuministraEstacionRecarga, Conductor, Propietario, Administrador

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

############################################################################################################
# Gas station and EV
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
# Drivers, owners and admins
############################################################################################################

def insert_driver_data_BD(mail, contrasenia, nombre, apellidos, tipo_vehiculo):
    with session_scope() as session:
        try:
            new_driver = Conductor(
                MailConductor=mail,
                Contrasenia=contrasenia,
                Nombre=nombre,
                Apellidos=apellidos,
                TipoVehiculo=tipo_vehiculo
            )
            session.add(new_driver)
            session.commit()
        except IntegrityError:
            session.rollback()

def update_driver_data_BD(mail, nombre, apellidos, tipo_vehiculo, contrasenia):
    with session_scope() as session:
        try:
            driver = session.query(Conductor).filter_by(MailConductor=mail).first()
            driver.Nombre = nombre
            driver.Apellidos = apellidos
            driver.TipoVehiculo = tipo_vehiculo
            if contrasenia:
                driver.Contrasenia = contrasenia
            session.commit()
        except IntegrityError:
            session.rollback()

def insert_owner_data_BD(mail, contrasenia, nombre, apellidos, documento, activo):
    with session_scope() as session:
        try:
            new_owner = Propietario(
                MailPropietario=mail,
                Contrasenia=contrasenia,
                Nombre=nombre,
                Apellidos=apellidos,
                Documento=documento, 
                Activo = activo
            )
            session.add(new_owner)
            session.commit()
        except IntegrityError:
            session.rollback()

def update_owner_data_BD(mail, nombre, apellidos, contrasenia):
    with session_scope() as session:
        try:
            owner = session.query(Propietario).filter_by(MailPropietario=mail).first()
            owner.Nombre = nombre
            owner.Apellidos = apellidos
            if contrasenia:
                owner.Contrasenia = contrasenia
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
    #!!! ESto por el momento no lo uso
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



# Get the nearest gas stations and EV stations to a given location
def get_nearest_distributors(lat, lon, tipo):
    with session_scope() as session:
        sql = text("""
            SELECT ST_AsText(g."Location") 
            FROM "Distribuidora" g
            WHERE "Tipo" = :tipo AND ST_Distance("Location", ST_MakePoint(:lon, :lat)::geography) <= 2000
        """)

        # Ejecutar la consulta pasando los parámetros lat, lon y tipo
        results = session.execute(sql, {'lat': lat, 'lon': lon, 'tipo': tipo}).fetchall()

        
        coordinates_list = []
        for result in results:
            coords = re.findall(r"[-\d\.]+", result[0])
            if coords:
                coordinates_list.append([float(coords[1]), float(coords[0])])

        coordinates_dict = {"coordinates": coordinates_list}

        with open('app/json_data/nearest_distributors.json', 'w') as file:
            json.dump(coordinates_dict, file, indent=4)

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
