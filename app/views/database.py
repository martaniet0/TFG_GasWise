import re

from sqlalchemy import create_engine, text, select, func, cast
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy.exc import IntegrityError
from geoalchemy2 import functions as geofuncs


from app.models import Ubicacion, Distribuidora, Gasolinera, EstacionRecarga, SuministraGasolinera, SuministraEstacionRecarga, Conductor, Propietario, Administrador

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
    'CEE 7/4 - Schuko - Type F' : '7/4p',
    'IEC 60309 5-pin' : '60309',
    'Tesla (Model S/X)' : 'teslaS/X',
    'CEE 5 Pin' : '5p',
    'CEE 3 Pin' : '3p',
    'Type 1 (J1772)' : 'J1772',
    'CCS (Type 1)' : 'ccs1',
    'Type I (AS 3112)' : 'AS/NZS3112',
    'Europlug 2-Pin (CEE 7/16)' : 'Europlug',
    'NACS / Tesla Supercharger' : 'NACS',
    'CEE+ 7 Pin' : '7p',
    'Blue Commando (2P+E)' : 'Commando'
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

        with open('app/json_data/nearest_distributors.json', 'w') as file:
            json.dump(coordinates_dict, file, indent=4)

        return tipo


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
        with open('app/test/log.txt', 'w') as file:
            json.dump(results, file, indent=4)
        if (results and results[2] == 'G'):
            query_gas_station = f"""
            SELECT 
            g."TipoVenta",
            g."Horario",
            g."Margen"
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
            e."Precio"
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
                    e."Precio"
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
            return results 
        else:
            return None
    except psycopg2.Error as e:
        print(f"Error al extraer información de la distribuidora: {e}")
        return None
    finally:
        cur.close()
        conn.close()
