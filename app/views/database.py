import re

from flask import flash

from sqlalchemy import create_engine, text, select, func, cast, and_
from sqlalchemy.orm import sessionmaker, aliased, joinedload
from contextlib import contextmanager
from sqlalchemy.exc import IntegrityError
from geoalchemy2 import functions as geofuncs
from geoalchemy2 import Geography
from flask_login import current_user
from transformers import pipeline

from app.models import Ubicacion, Distribuidora, Gasolinera, EstacionRecarga, SuministraGasolinera, SuministraEstacionRecarga, Conductor, Propietario, Administrador, TipoCombustible, TipoPunto, Servicio, ServiciosGasolinera, Pregunta, Respuesta, Valoracion, IndicaServicioConductor, PoseeDistribuidora, MarcaFavorita

import app.views.search as search
import app.views.helpers as helpers
import app.views.procedures_gas_station as gas
import app.views.procedures_EV_station as ev

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
#DICCTIONARIES
############################################################################################################
services = {
    4: "hospedaje",
    5: "lavado_coches",
    6: "lavado_camiones",
    7: "parking_camiones",
    8: "cambiapaniales",
    9: "duchas",
    10: "supermercado",
    11: "amazon_locker",
    12: "citypaq",
    13: "vaciado_aguas_negras",
    14: "estacion_accesible", 
    15: "cafeteria"
}

service_icons = {v: k for k, v in services.items()}

services_names = {
    "hospedaje": "Hospedaje",
    "lavado_coches": "Lavado de coches",
    "lavado_camiones": "Lavado de camiones",
    "parking_camiones": "Parking para camiones",
    "cambiapaniales": "Cambiador de pañales",
    "duchas": "Duchas",
    "supermercado": "Supermercado",
    "amazon_locker": "Amazon Locker",
     "citypaq": "Correos CityPaq",
    "vaciado_aguas_negras": "Vaciado de aguas negras",
    "estacion_accesible": "Estación accesible", 
    "cafeteria": "Cafetería" #le he quitado una coma
}

fuel = {
    'Biodiesel': 'biodiesel',
    'Bioetanol': 'bioetanol',
    'Gas Natural Comprimido': 'gas_comprimido', 
    'Gas Natural Licuado': 'gas_licuado', 
    'Gases licuados del petróleo': 'gas_petroleo', 
    'Gasoleo A': 'gasoleoA', 
    'Gasoleo B': 'gasoleoB', 
    'Gasoleo Premium': 'gasoleo_premium', 
    'Gasolina 95 E10': 'gasolina95_E10', 
    'Gasolina 95 E5': 'gasolina95_E5', 
    'Gasolina 95 E5 Premium': 'gasolina95_E5_premium', 
    'Gasolina 98 E10': 'gasolina98_E10', 
    'Gasolina 98 E5': 'gasolina98_E5', 
    'Hidrogeno': 'hidrogeno'
}

connector =  {
    'CCS (Type 2)': 'ccs2',
    'CHAdeMO' : 'chademo',
    'Type 2 (Tethered Connector)' : 'tipo2thetered',
    'Type 2 (Socket Only)' : 'tipo2socket',
    'CEE 7/4 - Schuko - Type F' : '74p',
    'IEC 60309 5-pin' : '60309',
    'Tesla (Model S/X)' : 'teslaSX',
    'CEE 5 Pin' : '5p',
    'CEE 3 Pin' : '3p',
    'Type 1 (J1772)' : 'J1772',
    'CCS (Type 1)' : 'ccs1',
    'Type I (AS 3112)' : 'ASNZS3112',
    'Europlug 2-Pin (CEE 7/16)' : 'Europlug',
    'NACS / Tesla Supercharger' : 'NACS',
    'CEE+ 7 Pin' : '7p',
    'Blue Commando (2P+E)' : 'Commando'
}

connector_processed =  {
    'CCS (Type 2)': 'CCS (Tipo 2)',
    'CHAdeMO': 'CHAdeMO',
    'Type 2 (Tethered Connector)': 'Tipo 2 (Thetered Connector)',
    'Type 2 (Socket Only)': 'Tipo 2 (Socket)',
    'CEE 7/4 - Schuko - Type F': 'CEE 7/4',
    'IEC 60309 5-pin': 'IEC 60309 5-pines',
    'Tesla (Model S/X)': 'Tesla (Modelo S/X)',
    'CEE 5 Pin': 'CEE 5 pines',
    'CEE 3 Pin': 'CEE 3 pines',
    'Type 1 (J1772)': 'Tipo 1 (J1772)',
    'CCS (Type 1)': 'CCS (Tipo 1)',
    'Type I (AS 3112)': 'Tipo 1 (AS/NZS 3112 )',
    'Europlug 2-Pin (CEE 7/16)': 'Europlug 2 pines',
    'NACS / Tesla Supercharger': 'NACS (Tesla Supercharger)',
    'CEE+ 7 Pin': 'CEE+ 7 pines',
    'Blue Commando (2P+E)': 'Blue Commando (2P+E)'
}


brands = {'repsol', 'bp', 'cepsa', 'galp', 'shell'}

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
                Margen=margen,
                ServiciosVerificados=False
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
                Activo = activo
            )
            session.add(new_owner)
            session.commit()
            new_owner_document = PoseeDistribuidora(
                MailPropietario=mail,
                Documento=documento,
                IdDistribuidora=None,
                Confirmado=False,
                Revisado=False
            )
            session.add(new_owner_document)
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

# Obtiene las distribuidoras de la BD según los filtros dados
def set_filters(lat, lon, puntos_str, tipo, **kwargs):
    if 'estacion_recarga' in kwargs.values():
        tipo = 'E'
    elif 'gasolinera' in kwargs.values():
        tipo = 'G'

    if puntos_str == []:
        select = """SELECT ST_AsText(g."Location") 
                    FROM "Distribuidora" g"""

        distributor_conditions = """
                    WHERE g."Tipo" = :tipo AND ST_Distance("Location", ST_MakePoint(:lon, :lat)::geography) <= 2000
                """
        sql = select + distributor_conditions
        params = {'lat': lat, 'lon': lon, 'tipo': tipo} 

    elif(lat == 0 and lon == 0):
        select = f"""
        WITH ruta AS (
        SELECT ST_Buffer(ST_MakeLine(ARRAY[{puntos_str}])::geography, 2000) AS geom
        )
        SELECT ST_AsText(g."Location")
        FROM public."Distribuidora" g 
        """
        #NUEVO: FROM public."Distribuidora" g
        #FROM public."Distribuidora" g, ruta r"""

        distributor_conditions = """
                        JOIN ruta r ON ST_DWithin(g."Location"::geography, r.geom, 0)
                        WHERE g."Tipo" = :tipo
                    """
                    #WHERE ST_DWithin(g."Location"::geography, r.geom, 0)
                    #AND g."Tipo" = :tipo
                        
        
        sql = select + distributor_conditions
        params = {'lat': lat, 'lon': lon, 'tipo': tipo} 

    
    if tipo == 'G':
        #!!!AND
        #Servicios (solo hay para gasolineras) 
        service_ids = []
        services_join, services_conditions, services_group_by ,services_count = None, None, None, None
        for key, value in kwargs.items():
            matching_keys_services = [k for k, v in services.items() if v == value]
            service_ids.extend(matching_keys_services)

        if(service_ids):
            count_service_ids = len(service_ids)
            services_join = """ JOIN public."ServiciosGasolinera" sg ON g."IdDistribuidora" = sg."IdDistribuidora" """
            services_conditions = """ AND sg."IdServicio" IN :service_ids AND sg."Existe" = true """
            services_group_by = """ GROUP BY g."IdDistribuidora", g."Location" """
            services_count = """ HAVING COUNT(DISTINCT sg."IdServicio") = :count_service_ids"""
            
            sql = select + services_join + distributor_conditions + services_conditions + services_group_by + services_count
            params = {'lat': lat, 'lon': lon, 'tipo': tipo, 'service_ids': tuple(service_ids), 'count_service_ids': count_service_ids}  
            
        #!!!AND
        #Combustibles (solo hay para gasolineras)
        fuel_type = []
        fuel_ids= []
        fuels_join, fuels_conditions, fuels_group_by, fuels_count= None, None, None, None
        for key, value in kwargs.items():
            matching_keys_type = [k for k, v in fuel.items() if v == value]
            fuel_type.extend(matching_keys_type)

        for value in fuel_type:
            matching_keys_fuel = [k for k, v in gas.gas_type.items() if v == value]
            fuel_ids.extend(matching_keys_fuel)
        
        if(fuel_ids):
            count_fuel_ids = len(fuel_ids)
            fuels_join = """ JOIN public."SuministraGasolinera" sumg ON g."IdDistribuidora" = sumg."IdDistribuidora" """
            fuels_conditions = """ AND sumg."IdCombustible" IN :fuel_ids """
            fuels_group_by = """ GROUP BY g."IdDistribuidora", g."Location" """
            fuels_count = """ COUNT(DISTINCT sumg."IdCombustible") = :count_fuel_ids"""
            
            if(services_conditions):
                sql = select + services_join + fuels_join + distributor_conditions + services_conditions + fuels_conditions + services_group_by + services_count + """ AND """ + fuels_count
                params = {'lat': lat, 'lon': lon, 'tipo': tipo, 'service_ids': tuple(service_ids), 'count_service_ids': count_service_ids, 'fuel_ids': tuple(fuel_ids), 'count_fuel_ids': count_fuel_ids}
            else:
                sql = select + fuels_join + distributor_conditions + fuels_conditions + fuels_group_by + """ HAVING """ + fuels_count
                params = {'lat': lat, 'lon': lon, 'tipo': tipo, 'fuel_ids': tuple(fuel_ids), 'count_fuel_ids': count_fuel_ids}


        #!!!OR
        #Marcas (solo hay para gasolineras)
        matching_brands= []
        brand_join, brand_conditions, brand_group_by ,brand_count = None, None, None, None

        #Busca las marcas pasadas por parámetros (brands es lista no dic)
        matching_brands = brands.intersection(kwargs.values())
        if (matching_brands):
            brand_conditions = " OR ".join([
                f"(g.\"Nombre\" ILIKE :marca{index} OR g.\"Nombre\" ILIKE :marca{index}_post OR g.\"Nombre\" ILIKE :marca{index}_pre OR g.\"Nombre\" ILIKE :marca{index}_around)"
                for index, _ in enumerate(matching_brands)
            ])

            if(services_conditions and fuels_conditions):
                sql = select + services_join + fuels_join + distributor_conditions + services_conditions + fuels_conditions + services_group_by + services_count + """ AND """ + fuels_count + """ AND ( """ +  brand_conditions + """ )"""
                params = {'lat': lat, 'lon': lon, 'tipo': tipo, 'service_ids': tuple(service_ids), 'count_service_ids': count_service_ids, 'fuel_ids': tuple(fuel_ids), 'count_fuel_ids': count_fuel_ids}
                for index, marca in enumerate(matching_brands):
                    params[f"marca{index}"] = f"%{marca}%"
                    params[f"marca{index}_post"] = f"%{marca} %"
                    params[f"marca{index}_pre"] = f"% {marca}%"
                    params[f"marca{index}_around"] = f"% {marca} %"
            elif(services_conditions):
                sql = select + services_join + distributor_conditions + services_conditions + services_group_by + services_count + """ AND ( """ +  brand_conditions + """ )"""
                params = {'lat': lat, 'lon': lon, 'tipo': tipo, 'service_ids': tuple(service_ids), 'count_service_ids': count_service_ids}  
                for index, marca in enumerate(matching_brands):
                    params[f"marca{index}"] = f"%{marca}%"
                    params[f"marca{index}_post"] = f"%{marca} %"
                    params[f"marca{index}_pre"] = f"% {marca}%"
                    params[f"marca{index}_around"] = f"% {marca} %"
            elif(fuels_conditions):
                sql = select + fuels_join + distributor_conditions + fuels_conditions + fuels_group_by + """ HAVING """ + fuels_count + """ AND ( """ +  brand_conditions + """ )"""
                params = {'lat': lat, 'lon': lon, 'tipo': tipo, 'fuel_ids': tuple(fuel_ids), 'count_fuel_ids': count_fuel_ids}
                for index, marca in enumerate(matching_brands):
                    params[f"marca{index}"] = f"%{marca}%"
                    params[f"marca{index}_post"] = f"%{marca} %"
                    params[f"marca{index}_pre"] = f"% {marca}%"
                    params[f"marca{index}_around"] = f"% {marca} %"
            else:
                sql = select + distributor_conditions + """ AND ( """ +  brand_conditions + """ )"""
                params = {'lat': lat, 'lon': lon, 'tipo': tipo}
                for index, marca in enumerate(matching_brands):
                    params[f"marca{index}"] = f"%{marca}%"
                    params[f"marca{index}_post"] = f"%{marca} %"
                    params[f"marca{index}_pre"] = f"% {marca}%"
                    params[f"marca{index}_around"] = f"% {marca} %"



    elif tipo == 'E':
        #!!!AND
        #Conectores (solo hay para estaciones de recarga) 
        connector_type = []
        connector_ids= []
        connector_join, connector_conditions, connector_group_by, connector_count= None, None, None, None
        for key, value in kwargs.items():
            matching_keys_connector_type = [k for k, v in  connector.items() if v == value]
            connector_type.extend(matching_keys_connector_type)

        for value in connector_type:
            matching_keys_connector_type = [k for k, v in ev.connector_type.items() if v == value]
            connector_ids.extend(matching_keys_connector_type)
   
        if(connector_ids):
            count_connector_ids = len(connector_ids)
            connector_join = """ JOIN public."SuministraEstacionRecarga" sumer ON g."IdDistribuidora" = sumer."IdDistribuidora" """
            connector_conditions = """ AND sumer."IdPunto" IN :connector_ids """
            connector_group_by = """ GROUP BY g."IdDistribuidora", g."Location" """
            connector_count = """ COUNT(DISTINCT sumer."IdPunto") = :count_connector_ids"""

            sql = select + connector_join + distributor_conditions + connector_conditions + connector_group_by + """ HAVING """ + connector_count
            params = {'lat': lat, 'lon': lon, 'tipo': tipo, 'connector_ids': tuple(connector_ids), 'count_connector_ids': count_connector_ids}




    return sql, params, tipo

# Get gas stations and EV stations in a given route
def get_route_distributors(tipo, **kwargs):
    puntos_sql = search.get_route_array()
    puntos_str = ',\n      '.join(puntos_sql)

    with session_scope() as session:
        # Llamar a set_filters para obtener la consulta SQL y los parámetros
        sql, params , tipo = set_filters(0, 0, puntos_str, tipo, **kwargs)

        # Ejecutar la consulta SQL
        results = session.execute(text(sql), params).fetchall()

        query = f"""
        WITH ruta AS (
        SELECT ST_Buffer(ST_MakeLine(ARRAY[{puntos_str}])::geography, 2000) AS geom
        )
        SELECT ST_AsText(g."Location")
        FROM public."Distribuidora" g, ruta r
        WHERE ST_DWithin(g."Location"::geography, r.geom, 0)
        AND g."Tipo" = '{tipo}';

            """
        
        coordinates_list = []
        for result in results:
            coords = re.findall(r"[-\d\.]+", result[0])
            if coords:
                coordinates_list.append([float(coords[1]), float(coords[0])])

        coordinates_dict = {"coordinates": coordinates_list}

        with open('app/json_data/route_distributors.json', 'w') as file:
            json.dump(coordinates_dict, file, indent=4)

        return tipo


# Get the nearest gas stations and EV stations to a given location
def get_nearest_distributors(lat, lon, tipo, **kwargs):
    with session_scope() as session:
        # Llamar a set_filters para obtener la consulta SQL y los parámetros
        sql, params , tipo = set_filters(lat, lon, [], tipo, **kwargs)

        # Ejecutar la consulta SQL
        results = session.execute(text(sql), params).fetchall()

        coordinates_list = []
        for result in results:
            coords = re.findall(r"[-\d\.]+", result[0])
            if coords:
                coordinates_list.append([float(coords[1]), float(coords[0])])

        coordinates_dict = {"coordinates": coordinates_list}
        search.sort_nearest_distributors_distance(coordinates_dict, lat, lon)

        with open('app/json_data/nearest_distributors.json', 'w') as file:
            json.dump(coordinates_dict, file, indent=4)

        return tipo

#Get distributor info 
def get_distributor_data(lat, lon, id):
    conn = psycopg2.connect("dbname='GasWiseDB' user='marta' host='postgres' password='maniro12'")#!!!
    cur = conn.cursor()
    lat=lat
    lon=lon

    if id != None:
        query_location = """
                        SELECT
                        ST_Y("Location"::geometry) AS latitude,
                        ST_X("Location"::geometry) AS longitude
                        FROM
                            public."Distribuidora"
                        WHERE
                            "IdDistribuidora" = %s;"""
        cur.execute(query_location, (id,))
        results_location = cur.fetchone()
        lat = results_location[0]
        lon = results_location[1]

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
        if (results and results[2] == 'G'):
            query_gas_station = f"""
            SELECT 
            g."TipoVenta",
            g."Horario",
            g."Margen",
            g."IdDistribuidora",
            g."ServiciosVerificados"
            FROM "Gasolinera" g
            WHERE g."IdDistribuidora" = (SELECT "IdDistribuidora" FROM "Distribuidora" WHERE ST_Equals("Location"::geometry, ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)::geometry));
            """ 
            cur.execute(query_gas_station)
            results_gas_station = cur.fetchone()
            results += results_gas_station
        elif (results and results[2] == 'E'):
            query_ev_station = f"""
            SELECT 
            e."TipoVenta",
            e."Precio",
            e."IdDistribuidora"
            FROM "EstacionRecarga" e
            WHERE e."IdDistribuidora" = (SELECT "IdDistribuidora" FROM "Distribuidora" WHERE ST_Equals("Location"::geometry, ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)::geometry));
            """            
            cur.execute(query_ev_station)
            results_ev_station = cur.fetchone()
            results += results_ev_station
        else:
            query =f"""
                SELECT 
                    d."Nombre",
                    d."MailPropietario", 
                    d."Tipo",
                    e."TipoVenta",
                    e."Precio",
                    e."IdDistribuidora"
                FROM 
                    "EstacionRecarga" e
                JOIN 
                    "Distribuidora" d ON e."IdDistribuidora" = d."IdDistribuidora"
                WHERE 
                    ST_DWithin(d."Location"::geography, ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)::geography, 1);
            """
            cur.execute(query)
            results = cur.fetchone()
        if results:
            return results, lat, lon 
        else:
            return None
    except psycopg2.Error as e:
        print(f"Error al extraer información de la distribuidora: {e}")
        return None
    finally:
        cur.close()
        conn.close()

#Obtener los combustibles y precios de una gasolinera
def get_gas_station_prices(lat, lon):
    with session_scope() as session:
        # Subconsulta para encontrar la gasolinera más cercana a las coordenadas dadas
        gasolinera_alias = aliased(Distribuidora)
        subquery = (session.query(
                        gasolinera_alias.IdDistribuidora,
                        func.ST_Distance(
                            gasolinera_alias.Location,
                            func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
                        ).label('distance')
                    )
                    .order_by('distance')
                    .limit(1)
                    .subquery())
        
        
        # Consulta principal para obtener los tipos de combustibles y sus precios
        results = (session.query(
                        TipoCombustible.Nombre.label('combustible'),
                        SuministraGasolinera.Precio.label('precio')
                    )
                    .join(SuministraGasolinera, SuministraGasolinera.IdCombustible == TipoCombustible.IdCombustible)
                    .join(subquery, subquery.c.IdDistribuidora == SuministraGasolinera.IdDistribuidora)
                    .all())
        
        return [{'combustible': result.combustible, 'precio': result.precio} for result in results]

#Obtener los conectores y precios de una estación de recarga
def get_charge_points(lat, lon):
    with session_scope() as session:
        recarga_alias = aliased(Distribuidora)
        subquery = (session.query(
                        recarga_alias.IdDistribuidora,
                        func.ST_Distance(
                            recarga_alias.Location,
                            func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
                        ).label('distance')
                    )
                    .order_by('distance')
                    .limit(1)
                    .subquery())
        
        results = (session.query(
                        TipoPunto.Nombre.label('punto'),
                        SuministraEstacionRecarga.CargaRapida.label('carga_rapida'),
                        SuministraEstacionRecarga.Cantidad.label('cantidad'),
                        SuministraEstacionRecarga.Voltaje.label('voltaje'),
                        SuministraEstacionRecarga.Amperios.label('amperios'),
                        SuministraEstacionRecarga.kW.label('kW')
                    )
                    .join(SuministraEstacionRecarga, SuministraEstacionRecarga.IdPunto == TipoPunto.IdPunto)
                    .join(subquery, subquery.c.IdDistribuidora == SuministraEstacionRecarga.IdDistribuidora)
                    .all())
        
        puntos_list = []

        for result in results:
            cantidad = result.cantidad if result.cantidad else "-"
            voltaje = result.voltaje if result.voltaje else "-"
            amperios = result.amperios if result.amperios else "-"
            kW = result.kW if result.kW else "-"
            punto_clave = connector_processed.get(result.punto, "-")
            puntos_list.append({
                'punto': punto_clave, 
                'carga_rapida': result.carga_rapida, 
                'cantidad': cantidad, 
                'voltaje': voltaje, 
                'amperios': amperios, 
                'kW': kW})

        return puntos_list
        


#Obtener los servicios de una gasolinera
def get_gas_station_services(lat, lon):
    with session_scope() as session:
        #Consulta la gasolinera correspondiente a la coordenadas dadas
        #Obtener los servicios de esa gasolinera, si estan verificados y si tienen porcentaje cual es
        gasolinera_alias = aliased(Distribuidora)
        subquery = (session.query(
                        gasolinera_alias.IdDistribuidora,
                        func.ST_Distance(
                            gasolinera_alias.Location,
                            func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
                        ).label('distance')
                    )
                    .order_by('distance')
                    .limit(1)
                    .subquery())
        
        # Consulta principal para obtener los servicios
        results = (session.query(
                        Servicio.Nombre.label('servicio'),
                        ServiciosGasolinera.Verificado.label('verificado'),
                        ServiciosGasolinera.Porcentaje.label('porcentaje'),
                        ServiciosGasolinera.Existe.label('existe')
                    )
                    .join(ServiciosGasolinera, ServiciosGasolinera.IdServicio == Servicio.IdServicio)
                    .join(subquery, subquery.c.IdDistribuidora == ServiciosGasolinera.IdDistribuidora)
                    .filter(ServiciosGasolinera.Existe == True)
                    .all())
        
        #return [{'servicio': services_names.get(result.servicio, result.servicio), 'verificado': result.verificado, 'porcentaje': result.porcentaje, 'icono': services.get(result.servicio, result.servicio)} for result in results]
        result_list = [
            {
                'servicio': services_names.get(result.servicio, result.servicio),
                'verificado': result.verificado,
                'porcentaje': round(result.porcentaje, 2) if result.porcentaje else None,
                'icono': service_icons.get(result.servicio), 
                'existe': result.existe
            } 
            for result in results
        ]

        return result_list
    
#Obtener las preguntas y respuestas de una distribuidora
def get_questions(lat, lon):
    with session_scope() as session:
        distribuidora_alias = aliased(Distribuidora)
        subquery = (session.query(
                        distribuidora_alias.IdDistribuidora,
                        func.ST_Distance(
                            distribuidora_alias.Location,
                            func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
                        ).label('distance')
                    )
                    .order_by('distance')
                    .limit(1)
                    .subquery())
        
        preguntas = (session.query(
                        Pregunta.IdPregunta,
                        Pregunta.MailConductor.label('mail_pregunta'),
                        Pregunta.TextoPregunta.label('pregunta'),
                        Pregunta.Fecha.label('fecha_pregunta'),
                        Pregunta.Hora.label('hora_pregunta')
                    )
                    .join(subquery, subquery.c.IdDistribuidora == Pregunta.IdDistribuidora)
                    .all())
        
        pregunta_list = []
        respuesta_list = []

        for pregunta in preguntas:
            conductor_pregunta = session.query(Conductor).filter(Conductor.MailConductor == pregunta.mail_pregunta).first()
            nombre_completo_pregunta = f"{conductor_pregunta.Nombre} {conductor_pregunta.Apellidos}" if conductor_pregunta.Apellidos else f"{conductor_pregunta.Nombre}"
            
            pregunta_list.append({
                'id_pregunta': pregunta.IdPregunta,
                'mail_pregunta': nombre_completo_pregunta,
                'pregunta': pregunta.pregunta,
                'fecha_pregunta': pregunta.fecha_pregunta,
                'hora_pregunta': pregunta.hora_pregunta
            })
            
            respuestas = (session.query(
                            Respuesta.MailPropietario.label('mail_propietario_respuesta'),
                            Respuesta.MailConductor.label('mail_conductor_respuesta'),
                            Respuesta.TextoRespuesta.label('respuesta'),
                            Respuesta.Fecha.label('fecha_respuesta'),
                            Respuesta.Hora.label('hora_respuesta'),
                            Respuesta.Verificada.label('verificada'),
                            Respuesta.IdPregunta.label('id_pregunta')
                        )
                        .filter(Respuesta.IdPregunta == pregunta.IdPregunta)
                        .all())
            
            for respuesta in respuestas:
                if respuesta.mail_conductor_respuesta:
                    conductor_respuesta = session.query(Conductor).filter(Conductor.MailConductor == respuesta.mail_conductor_respuesta).first()
                    nombre_completo_respuesta = f"{conductor_respuesta.Nombre} {conductor_respuesta.Apellidos}" if conductor_respuesta.Apellidos else f"{conductor_respuesta.Nombre}"
                else:
                    propietario_respuesta = session.query(Propietario).filter(Propietario.MailPropietario == respuesta.mail_propietario_respuesta).first()
                    nombre_completo_respuesta = f"{propietario_respuesta.Nombre} {propietario_respuesta.Apellidos}" if propietario_respuesta.Apellidos else f"{propietario_respuesta.Nombre}"

                respuesta_list.append({
                    'id_pregunta': respuesta.id_pregunta,
                    'mail_respuesta': nombre_completo_respuesta,
                    'respuesta': respuesta.respuesta,
                    'fecha_respuesta': respuesta.fecha_respuesta,
                    'hora_respuesta': respuesta.hora_respuesta,
                    'verificada': respuesta.verificada
                })
        
        return pregunta_list, respuesta_list
    
#Obtener las valoraciones de una distribuidora
def get_ratings2(lat, lon):
    with session_scope() as session:
        distribuidora_alias = aliased(Distribuidora)
        subquery = (session.query(
                        distribuidora_alias.IdDistribuidora,
                        func.ST_Distance(
                            distribuidora_alias.Location,
                            func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
                        ).label('distance')
                    )
                    .order_by('distance')
                    .limit(1)
                    .subquery())
        
        valoraciones = (session.query(
                        Valoracion.Puntuacion.label('puntuacion'),
                        Valoracion.Texto.label('texto'),
                        Valoracion.MailConductor.label('mail_valoracion')
                    )
                    .join(subquery, subquery.c.IdDistribuidora == Valoracion.IdDistribuidora)
                    .all())
        
        valoracion_list = []
        
        for valoracion in valoraciones:
            local_session = Session()
            conductor_valoracion = local_session.query(Conductor).filter(Conductor.MailConductor == valoracion.mail_valoracion).first()
            local_session.close()
            nombre_completo_valoracion = f"{conductor_valoracion.Nombre} {conductor_valoracion.Apellidos}" if conductor_valoracion.Apellidos else f"{conductor_valoracion.Nombre}"
            valoracion_list.append({
                'puntuacion': valoracion.puntuacion,
                'texto': valoracion.texto,
                'nombre': nombre_completo_valoracion
            })

        valoracion_media = session.query(func.avg(Valoracion.Puntuacion)).filter(subquery.c.IdDistribuidora == Valoracion.IdDistribuidora).scalar()
        valoracion_media = round(valoracion_media, 2) if valoracion_media else None

        return valoracion_list, valoracion_media

def get_ratings(lat, lon, sort_by='rating_desc'):
    with session_scope() as session:
        distribuidora_alias = aliased(Distribuidora)
        subquery = (session.query(
                        distribuidora_alias.IdDistribuidora,
                        func.ST_Distance(
                            distribuidora_alias.Location,
                            func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
                        ).label('distance')
                    )
                    .order_by('distance')
                    .limit(1)
                    .subquery())
        
        query = session.query(
                    Valoracion.Puntuacion.label('puntuacion'),
                    Valoracion.Texto.label('texto'),
                    Valoracion.MailConductor.label('mail_valoracion')
                ).join(subquery, subquery.c.IdDistribuidora == Valoracion.IdDistribuidora)
        
        if sort_by == 'rating_desc':
            query = query.order_by(Valoracion.Puntuacion.desc())
        elif sort_by == 'rating_asc':
            query = query.order_by(Valoracion.Puntuacion.asc())
        elif sort_by == 'comment_best':
            query = query.order_by(Valoracion.ClasificacionTexto.desc())
        elif sort_by == 'comment_worst':
            query = query.order_by(Valoracion.ClasificacionTexto.asc())
        
        valoraciones = query.all()
        
        valoracion_list = []
        
        for valoracion in valoraciones:
            local_session = Session()
            conductor_valoracion = local_session.query(Conductor).filter(Conductor.MailConductor == valoracion.mail_valoracion).first()
            local_session.close()
            nombre_completo_valoracion = f"{conductor_valoracion.Nombre} {conductor_valoracion.Apellidos}" if conductor_valoracion.Apellidos else f"{conductor_valoracion.Nombre}"
            valoracion_list.append({
                'puntuacion': valoracion.puntuacion,
                'texto': valoracion.texto,
                'nombre': nombre_completo_valoracion
            })

        valoracion_media = session.query(func.avg(Valoracion.Puntuacion)).filter(subquery.c.IdDistribuidora == Valoracion.IdDistribuidora).scalar()
        valoracion_media = round(valoracion_media, 2) if valoracion_media else None

        return valoracion_list, valoracion_media


#Insertar valoración de un conductor en la BD 
def insert_rating(id_distribuidora, puntuacion, texto, mail_conductor):
    with session_scope() as session:
        try: 
            # Analizar el sentimiento del texto
            pipe = pipeline('sentiment-analysis', model='pysentimiento/robertuito-sentiment-analysis')
            
            resultado = pipe(texto)
            clasificacion = resultado[0]['label']
            
            if clasificacion == 'NEG':
                clasificacion_valor = -1
            elif clasificacion == 'NEU':
                clasificacion_valor = 0
            elif clasificacion == 'POS':
                clasificacion_valor = 1
            else:
                clasificacion_valor = None  

            nueva_valoracion = Valoracion(
                Puntuacion=puntuacion,
                Texto=texto,
                IdDistribuidora=id_distribuidora,
                MailConductor=mail_conductor, 
                ClasificacionTexto=clasificacion_valor
            )

            session.add(nueva_valoracion)
            session.commit()
        except IntegrityError:
            session.rollback()

def insert_db_services_driver(distributor_id, selected_services):
    with session_scope() as session:
        try:
            # Insertar los servicios indicados en IndicaServicioConductor
            for service_key, service_value in selected_services.items():
                existe = True if service_value == 'yes' else False
                service_id = next(key for key, value in services.items() if value == service_key)

                new_service = IndicaServicioConductor(
                    IdServicio=service_id,
                    MailConductor=current_user.MailConductor,
                    IdDistribuidora=distributor_id,
                    Existe=existe
                )
                session.add(new_service)

            session.commit()

            # !!! Si solo un usuario indica un servicio en una gasolinera aparece que el 100% de los usuarios lo asegura aun que otros haya puesto que no saben
            for service_key, service_value in selected_services.items():
                service_id = next(key for key, value in services.items() if value == service_key)

                # Calcular los valores de Existe y Porcentaje
                #Busca todas las tuplas que tengan hayan sido indicadas para ese servicio en esa gasolinera
                total_tuples = session.query(IndicaServicioConductor).filter(
                    and_(
                        IndicaServicioConductor.IdServicio == service_id,
                        IndicaServicioConductor.IdDistribuidora == distributor_id
                    )
                ).count()

                #Busca todas los "existe" para ese servicio en esa gasolinera
                x_counter = session.query(IndicaServicioConductor).filter(
                    and_(
                        IndicaServicioConductor.IdServicio == service_id,
                        IndicaServicioConductor.IdDistribuidora == distributor_id,
                        IndicaServicioConductor.Existe == True
                    )
                ).count()

                #Busca todos los "no existe" para ese servicio en esa gasolinera
                x_counter -= session.query(IndicaServicioConductor).filter(
                    and_(
                        IndicaServicioConductor.IdServicio == service_id,
                        IndicaServicioConductor.IdDistribuidora == distributor_id,
                        IndicaServicioConductor.Existe == False
                    )
                ).count()

                if x_counter > 0:
                    existe = True
                    porcentaje = (x_counter / total_tuples) * 100
                elif x_counter < 0:
                    existe = False
                    porcentaje = None
                else:
                    existe = None
                    porcentaje = None

                # Buscar si ya existe la entrada en ServiciosGasolinera
                existing_service = session.query(ServiciosGasolinera).filter(
                    and_(
                        ServiciosGasolinera.IdServicio == service_id,
                        ServiciosGasolinera.IdDistribuidora == distributor_id
                    )
                ).first()

                if existing_service:
                    # Si existe, actualizar la entrada
                    existing_service.Verificado = False
                    existing_service.Existe = existe
                    existing_service.Porcentaje = porcentaje
                else:
                    # Si no existe, crear una nueva entrada
                    new_gas_station_service = ServiciosGasolinera(
                        IdServicio=service_id,
                        IdDistribuidora=distributor_id,
                        Verificado=False,
                        Existe=existe,
                        Porcentaje=porcentaje
                    )
                    session.add(new_gas_station_service)

            session.commit()
            flash('Servicios indicados correctamente', 'success')

        except IntegrityError:
            flash('Ya has indicado anteriormente los servicios para esta gasolinera. Solo se puede hacer una vez', 'danger')
            session.rollback()

def insert_db_services_owner(distributor_id, selected_services):
    with session_scope() as session:
        try:
            # Insertar los servicios indicados ServiciosGasolinera
            for service_key, service_value in selected_services.items():
                existe = True if service_value == 'yes' else False
                service_id = next(key for key, value in services.items() if value == service_key)

                existing_service = session.query(ServiciosGasolinera).filter(
                    and_(
                        ServiciosGasolinera.IdServicio == service_id,
                        ServiciosGasolinera.IdDistribuidora == distributor_id
                    )
                ).first()

                if existing_service:
                    # Si existe, actualizar la entrada
                    existing_service.Verificado = True
                    existing_service.Existe = existe
                    existing_service.Porcentaje = None
                else:
                    new_service = ServiciosGasolinera(
                        IdServicio=service_id,
                        IdDistribuidora=distributor_id,
                        Verificado=True,
                        Existe=existe,
                        Porcentaje=None
                    )
                    session.add(new_service)

            #Eliminar de IndicaServicioConductor los servicios indicados anteriormente para ese idServicio y idDistribuidora
            session.query(IndicaServicioConductor).filter_by(IdDistribuidora=distributor_id).delete()
            session.query(Gasolinera).filter_by(IdDistribuidora=distributor_id).first().ServiciosVerificados = True

            session.commit()

        except IntegrityError:
            flash('Ya has indicado anteriormente los servicios para esta gasolinera. Solo se puede hacer una vez', 'danger')
            session.rollback()


def insert_db_question(texto_pregunta, fecha_pregunta, hora_pregunta, id_distribuidora, mail_conductor):
    with session_scope() as session:
        try:
            nueva_pregunta = Pregunta(
                TextoPregunta=texto_pregunta,
                Fecha=fecha_pregunta,
                Hora=hora_pregunta,
                IdDistribuidora=id_distribuidora,
                MailConductor=mail_conductor
            )

            session.add(nueva_pregunta)
            session.commit()
            flash('Pregunta enviada con éxito', 'success')
        except IntegrityError:
            session.rollback()

#Insertar una respuesta en la BD
def insert_db_answer(texto_respuesta, fecha_respuesta, hora_respuesta, verificada, id_pregunta, mail_conductor, mail_propietario):
    with session_scope() as session:
        try:
            nueva_respuesta = Respuesta(
                IdPregunta=id_pregunta,
                TextoRespuesta=texto_respuesta,
                MailConductor=mail_conductor,
                MailPropietario=mail_propietario,
                Fecha=fecha_respuesta,
                Hora=hora_respuesta,
                Verificada=verificada
            )

            session.add(nueva_respuesta)
            session.commit()
            flash('Respuesta enviada con éxito', 'success')
        except IntegrityError:
            session.rollback()

#Obtener las gasolineras que posee un conductor
def get_gas_stations_owner():
    with session_scope() as session:
        # Filtrar primero por distribuidoras que pertenecen al usuario actual y están verificadas
        distribuidoras_validadas = (session.query(PoseeDistribuidora.IdDistribuidora)
                                    .filter(PoseeDistribuidora.MailPropietario == current_user.MailPropietario,
                                            PoseeDistribuidora.Confirmado == True)
                                    .subquery())

        # Unir con la tabla Distribuidora para obtener detalles y ubicaciones, utilizando funciones ST_X y ST_Y
        # con una conversión de geography a geometry
        gasolineras = (session.query(
                        Gasolinera.IdDistribuidora,
                        Gasolinera.TipoVenta,
                        Gasolinera.Horario,
                        Gasolinera.Margen,
                        func.ST_Y(func.ST_GeomFromWKB(Distribuidora.Location)).label('latitud'),
                        func.ST_X(func.ST_GeomFromWKB(Distribuidora.Location)).label('longitud'), 
                        Distribuidora.Nombre,
                        Distribuidora.MailPropietario
                    )
                    .join(Distribuidora, Gasolinera.IdDistribuidora == Distribuidora.IdDistribuidora)
                    .join(distribuidoras_validadas, Distribuidora.IdDistribuidora == distribuidoras_validadas.c.IdDistribuidora)
                    .all())
        
        gasolinera_list = []

        for gasolinera in gasolineras:
            tipo_venta = 'Pública' if gasolinera.TipoVenta else 'Restringida a socios o cooperativistas'
            margen = 'Derecho' if gasolinera.Margen == 'D' else 'Izquierdo' if gasolinera.Margen == 'I' else None
            gasolinera_list.append({
                'id_distribuidora': gasolinera.IdDistribuidora,
                'tipo_venta': tipo_venta,
                'horario': gasolinera.Horario,
                'margen': margen,
                'latitud': gasolinera.latitud,
                'longitud': gasolinera.longitud, 
                'mail': gasolinera.MailPropietario,
                'nombre': gasolinera.Nombre

            })
        return gasolinera_list
    
#Insertar la información que ofrece un propietario cuando quiere añadir una nueva gasolinera
def insert_db_property(doc):
    with session_scope() as session:
        try:
            new_owner_document = PoseeDistribuidora(
                MailPropietario=current_user.MailPropietario,
                Documento=doc,
                IdDistribuidora=None,
                Confirmado=False,
                Revisado=False
            )
            session.add(new_owner_document)
            session.commit()
        except IntegrityError:
            session.rollback()
            flash('Ha habido un error al enviar el documento', 'danger')

#Modificar información de la posesión de las gasolineras que han sido confirmadas por un administrador
def insert_bd_confirmed_property(distribuidora_id, mail_propietario, id_posee):
    with session_scope() as session:
        try:
            # Actualizar la tabla Distribuidora
            distribuidora = session.query(Distribuidora).filter(Distribuidora.IdDistribuidora == distribuidora_id).one()
            distribuidora.MailPropietario = mail_propietario

            # Actualizar la tabla Propietario
            propietario = session.query(Propietario).filter(Propietario.MailPropietario == mail_propietario).one()
            propietario.Activo = True

            # Actualizar la tabla PoseeDistribuidora
            posee_distribuidora = session.query(PoseeDistribuidora).filter(PoseeDistribuidora.IdPosee == id_posee).one()
            posee_distribuidora.Confirmado = True
            posee_distribuidora.Revisado = True
            posee_distribuidora.IdDistribuidora = distribuidora_id

            # Confirmar los cambios
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


#Modificar información de la posesión de las gasolineras que han sido rechazadas por un administrador
def insert_bd_rejected_property(id_posee):
    with session_scope() as session:
        try:
            # Actualizar la tabla PoseeDistribuidora
            posee_distribuidora = session.query(PoseeDistribuidora).filter(PoseeDistribuidora.IdPosee == id_posee).one()
            posee_distribuidora.Confirmado = False
            posee_distribuidora.Revisado = True

            # Confirmar los cambios
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


#Función para obtener las gasolineras pendientes de verificación
def get_distributors_pending_verification():
    with session_scope() as session:
        try:
            pending_distributors = session.query(PoseeDistribuidora).filter(PoseeDistribuidora.Revisado == False).all()
            result = []
            for distributor in pending_distributors:
                result.append({
                    'mailPropietario': distributor.MailPropietario,
                    'documento': distributor.Documento,
                    'IdPosee': distributor.IdPosee
                })
            return result
        except Exception as e:
            raise e
        finally:
            session.close()

def get_distributor_document(id_posee):
    with session_scope() as session:
        try:
            distributor = session.query(PoseeDistribuidora).filter(PoseeDistribuidora.IdPosee == id_posee).one()
            document_data = distributor.Documento
            return document_data
        except Exception as e:
            return str(e), 500
        finally:
            session.close()

#Función para añadir distribuidora a favoritos
def insert_fav_distributor(distributor_id, mail):
    with session_scope() as session:
        try:
            new_fav_distributor = MarcaFavorita(
                IdDistribuidora=distributor_id,
                MailConductor=mail
            )
            with open ('app/test/log.txt', 'w') as file:
                file.write("\n" + str(new_fav_distributor))
            session.add(new_fav_distributor)
            session.commit()
        except IntegrityError:
            session.rollback()
            flash('Ya has añadido esta distribuidora a favoritos', 'danger')

#Función para eliminar distribuidora de favoritos
def delete_fav_distributor(distributor_id, mail):
    with session_scope() as session:
        try:
            session.query(MarcaFavorita).filter(
                and_(
                    MarcaFavorita.IdDistribuidora == distributor_id,
                    MarcaFavorita.MailConductor == mail
                )
            ).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            flash('Ha habido un error al eliminar la distribuidora de favoritos', 'danger')

#Función para obtener las distribuidoras favoritas de un conductor
def get_fav_distributors(mail):
    with session_scope() as session:
        try:
            # Consulta para obtener las distribuidoras favoritas del conductor
            fav_distributors = session.query(
                Distribuidora.IdDistribuidora,
                Distribuidora.Nombre,
                Distribuidora.MailPropietario,
                Distribuidora.Tipo,
                MarcaFavorita.IdDistribuidora,
                func.ST_Y(func.ST_GeomFromWKB(Distribuidora.Location)).label('latitud'),
                func.ST_X(func.ST_GeomFromWKB(Distribuidora.Location)).label('longitud')
            ).join(
                MarcaFavorita, MarcaFavorita.IdDistribuidora == Distribuidora.IdDistribuidora
            ).filter(
                MarcaFavorita.MailConductor == mail
            ).all()

            result = []
            for distributor in fav_distributors:
                distributor_info = {
                    'mailPropietario': distributor.MailPropietario,
                    'nombre': distributor.Nombre,
                    'tipo': distributor.Tipo,
                    'latitud': distributor.latitud,
                    'longitud': distributor.longitud, 
                    'idDistribuidora': distributor.IdDistribuidora
                }

                # Si el tipo es 'E', buscar en EstacionRecarga
                if distributor.Tipo == 'E':
                    estacion = session.query(EstacionRecarga).\
                        filter(EstacionRecarga.IdDistribuidora == distributor.IdDistribuidora).\
                        first()
                    if estacion:
                        distributor_info.update({
                            'TipoVenta': estacion.TipoVenta,
                            'Precio': estacion.Precio
                        })

                # Si el tipo es 'G', buscar en Gasolinera
                elif distributor.Tipo == 'G':
                    gasolinera = session.query(Gasolinera).\
                        filter(Gasolinera.IdDistribuidora == distributor.IdDistribuidora).\
                        first()
                    if gasolinera:
                        distributor_info.update({
                            'TipoVenta': gasolinera.TipoVenta,
                            'Horario': gasolinera.Horario,
                            'Margen': gasolinera.Margen
                        })

                result.append(distributor_info)

            return result
        except Exception as e:
            raise e
        finally:
            session.close()

def get_is_fav_distributor(id_distribuidora, mail):
    with session_scope() as session:
        try:
            fav = session.query(MarcaFavorita).filter(
                and_(
                    MarcaFavorita.IdDistribuidora == id_distribuidora,
                    MarcaFavorita.MailConductor == mail
                )
            ).first()
            return True if fav else False
        except Exception as e:
            raise e
        finally:
            session.close()

#Obtener id de distribuidora a partir de coordenadas
def get_distributor_id(lat, lon):
    with session_scope() as session:
        # Define el punto a buscar
        point_wkt = f'POINT({lon} {lat})'

        # Define la consulta SQL
        sql_query = text("""
            SELECT "IdDistribuidora"
            FROM "Distribuidora"
            WHERE ST_DWithin("Location", ST_GeomFromText(:point_wkt, 4326), 0.01)
            LIMIT 1
        """)

        # Ejecuta la consulta SQL
        result = session.execute(sql_query, {'point_wkt': point_wkt}).fetchone()

        if result:
            return result[0]
        else:
            return None

        
def get_distributor_rating(id):
    with session_scope() as session:
        try:
            # Consulta para obtener las valoraciones de la distribuidora
            ratings = session.query(
                Valoracion.Puntuacion,
                Valoracion.Texto,
                Valoracion.MailConductor
            ).filter(
                Valoracion.IdDistribuidora == id
            ).all()

            rating_media = session.query(func.avg(Valoracion.Puntuacion)).filter(Valoracion.IdDistribuidora == id).scalar()
            rating_media = round(rating_media, 2) if rating_media else None

            return rating_media
        except Exception as e:
            raise e
        finally:
            session.close()

def get_distributor_price(id, combustible):
    with session_scope() as session:
        try:
            # Consulta para obtener los precios de la gasolinera
            price = session.query(
                SuministraGasolinera.Precio
            ).filter(
                SuministraGasolinera.IdDistribuidora == id,
                SuministraGasolinera.IdCombustible == combustible
            ).first()

            # Si price no es None, extrae el primer valor de la tupla y conviértelo a float
            if price is not None:
                return float(price[0])
            else:
                return None
        except Exception as e:
            raise e
        finally:
            session.close()
