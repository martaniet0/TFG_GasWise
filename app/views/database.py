import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from geoalchemy2 import functions as geo_func
from contextlib import contextmanager

from app.models import Ubicacion, Distribuidora, Gasolinera, EstacionRecarga, SuministraGasolinera, SuministraEstacionRecarga, PruebaUbicacion

import app.views.search as search

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

def insert_location_data_BD(longitud, latitud, provincia, municipio, localidad, cp, direccion):
    with session_scope() as session:
        new_location = Ubicacion(
            Longitud=longitud,
            Latitud=latitud,
            Provincia=provincia,
            Municipio=municipio,
            Localidad=localidad,
            CP=cp,
            Direccion=direccion
        )
        session.add(new_location)

def insert_location_data_BD2(longitud, latitud):
    with session_scope() as session:
        # Create a Point object using Shapely and insert it into the location column
        new_location = PruebaUbicacion(location=f'SRID=4326;POINT({longitud} {latitud})')
        session.add(new_location)

def insert_distributor_data_BD(nombre, latitud, longitud, mail, idApi):
    with session_scope() as session:
        new_distributor = Distribuidora(
            Nombre=nombre,
            Latitud=latitud,
            Longitud=longitud,
            MailPropietario=mail,
            IdAPI=idApi
        )
        session.add(new_distributor)

def insert_gas_station_data_BD(id, tipo_venta, horario, margen):
    with session_scope() as session:
        new_gas_station = Gasolinera(
            IdDistribuidora=id,
            TipoVenta=tipo_venta,
            Horario=horario,
            Margen=margen
        )
        session.add(new_gas_station)

def insert_station_EV_data_BD(id, tipo_venta, precio):
    with session_scope() as session:
        new_ev_station = EstacionRecarga(
            IdDistribuidora=id,
            TipoVenta=tipo_venta,
            Precio=precio
        )
        session.add(new_ev_station)

def insert_gas_station_supply_data_BD(id_distribuidora, id_combustible, precio):
    with session_scope() as session:
        new_supply = SuministraGasolinera(
            IdDistribuidora=id_distribuidora,
            IdCombustible=id_combustible,
            Precio=precio
        )
        session.add(new_supply)

def insert_station_EV_supply_data_BD(id_distribuidora, id_punto, carga_rapida, cantidad, voltaje, amperios, kW):
    with session_scope() as session:
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

############################################################################################################
# SELECT DATA FROM THE DB USING SQLALCHEMY
############################################################################################################

def get_distributor_ID(idApi):
    with session_scope() as session:
        distributor = session.query(Distribuidora).filter_by(IdAPI=idApi).first()
        return distributor.IdDistribuidora if distributor else None

"""
def get_route_distributors():
    puntos_sql = search.get_route_array()  # This should return an array of `(long, lat)` tuples.
    line = func.ST_MakeLine([func.ST_Point(lon, lat) for lon, lat in puntos_sql])
    buffered_line = line.ST_Buffer(2000)  # Buffer by 2000 meters

    query = Session.query(PruebaUbicacion.location.ST_AsText()).filter(
        PruebaUbicacion.location.ST_DWithin(buffered_line, 0)
    )

    results = query.all()
    coordinates_list = []

    for result in results:
        coords = re.findall(r"[-\d\.]+", result[0])
        if coords:
            coordinates_list.append([float(coords[1]), float(coords[0])])  # Append as [lat, lon]

    coordinates_dict = {"coordinates": coordinates_list}
    return coordinates_dict"""

def get_route_distributors():
    conn = psycopg2.connect("dbname='GasWiseDB' user='marta' host='postgres' password='maniro12'")
    cur = conn.cursor()

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
        with open('app/json_data/route_distributors.json', 'w') as file:
            json.dump(coordinates_dict, file, indent=4)
    except psycopg2.Error as e:
        print(f"Error al buscar las distribuidoras en la ruta: {e}")
    finally:
        cur.close()
        conn.close()

