#!!!REVISAR RELACIONES
from app import db
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Time, Numeric, Boolean, LargeBinary
from geoalchemy2 import Geography
from geoalchemy2.shape import to_shape
from shapely.geometry import Point

#from sqlalchemy.orm import sessionmaker, relationship
#from sqlalchemy.orm import relationship, backref

class Conductor(db.Model):
    __tablename__ = 'Conductor'

    MailConductor = Column(String(100), primary_key=True)
    Contrasenia = Column(String(20), nullable=False)
    Nombre = Column(String(100), nullable=False)
    Apellidos = Column(String(100))
    
    #da_respuesta_conductor = db.relationship('DaRespuestaConductor', backref='conductor', lazy='dynamic')
    #valoraciones = db.relationship('Valoracion', backref='conductor', lazy='dynamic')
    #indica_servicios = db.relationship('IndicaServicioConductor', backref='conductor', lazy='dynamic')
    #marca_favoritas = db.relationship('MarcaFavorita', backref='conductor', lazy='dynamic')
    #preguntas = db.relationship('Pregunta', backref='conductor', lazy='dynamic')


class DaRespuestaConductor(db.Model):
    __tablename__ = 'DaRespuestaConductor'

    MailConductor = Column(String(100), ForeignKey('Conductor.MailConductor'), primary_key=True)
    IdRespuesta = Column(Integer, ForeignKey('Respuesta.IdRespuesta'), primary_key=True)
    Fecha = Column(Date, nullable=False)
    Hora = Column(Time, nullable=False)

    #conductor = db.relationship('Conductor', backref=db.backref('da_respuesta_conductors', lazy='dynamic'))
    #respuesta = db.relationship('Respuesta', backref=db.backref('da_respuesta_conductors', lazy='dynamic'))

class Valoracion(db.Model):
    __tablename__ = 'Valoracion'

    IdValoracion = Column(Integer, primary_key=True)
    Puntuacion = Column(Integer, nullable=False)
    Texto = Column(String(500))
    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'), nullable=False)
    MailConductor = Column(String(100), ForeignKey('Conductor.MailConductor'), nullable=False)

    #conductor = db.relationship('Conductor', backref=db.backref('valoraciones', lazy='dynamic'))
    #distribuidora = db.relationship('Distribuidora', backref=db.backref('valoraciones', lazy='dynamic'))

class DaRespuestaPropietario(db.Model):
    __tablename__ = 'DaRespuestaPropietario'

    MailPropietario = Column(String(100), ForeignKey('Propietario.MailPropietario'), primary_key=True)
    IdRespuesta = Column(Integer, ForeignKey('Respuesta.IdRespuesta'), primary_key=True)
    Fecha = Column(Date, nullable=False)
    Hora = Column(Time, nullable=False)

    #propietario = db.relationship('Propietario', backref=db.backref('da_respuesta_propietarios', lazy='dynamic'))
    #respuesta = db.relationship('Respuesta', backref=db.backref('da_respuesta_propietarios', lazy='dynamic'))

class Distribuidora(db.Model):
    __tablename__ = 'Distribuidora'

    IdDistribuidora = Column(Integer, primary_key=True)
    Nombre = Column(String(100))
    Latitud = Column(Numeric, ForeignKey('Ubicacion.Latitud'))
    Longitud = Column(Numeric, ForeignKey('Ubicacion.Longitud'))
    MailPropietario = Column(String(100), ForeignKey('Propietario.MailPropietario'))
    IdAPI = Column(String(100), unique=True)

    #valoraciones = db.relationship('Valoracion', backref='distribuidora', lazy='dynamic')
    #estaciones_recarga = db.relationship('EstacionRecarga', backref='distribuidora', uselist=False)
    #gasolineras = db.relationship('Gasolinera', backref='distribuidora', uselist=False)
    #preguntas = db.relationship('Pregunta', backref='distribuidora', lazy='dynamic')
    #servicios_gasolinera = db.relationship('ServiciosGasolinera', backref='distribuidora', lazy='dynamic')
    #suministra_estacion_recargas = db.relationship('SuministraEstacionRecarga', backref='distribuidora', lazy='dynamic')
    #suministra_gasolineras = db.relationship('SuministraGasolinera', backref='distribuidora', lazy='dynamic')


class EstacionRecarga(db.Model):
    __tablename__ = 'EstacionRecarga'

    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'), primary_key=True)
    TipoVenta = Column(String(255))
    Precio = Column(String(255))

    #suministra_estacion_recargas = db.relationship('SuministraEstacionRecarga', backref='estacion_recarga', lazy='dynamic')


class Gasolinera(db.Model):
    __tablename__ = 'Gasolinera'

    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'), primary_key=True)
    TipoVenta = Column(Boolean)
    Horario = Column(String(255))
    Margen = Column(String(1))

    #suministra_gasolineras = db.relationship('SuministraGasolinera', backref='gasolinera', lazy='dynamic')


class IndicaServicioConductor(db.Model):
    __tablename__ = 'IndicaServicioConductor'

    IdServicio = Column(Integer, ForeignKey('Servicio.IdServicio'), primary_key=True)
    MailConductor = Column(String(100), ForeignKey('Conductor.MailConductor'), primary_key=True)
    Existe = Column(Boolean, nullable=False)

    #conductor = db.relationship('Conductor', backref='indica_servicio_conductors')
    #servicio = db.relationship('Servicio', backref='indica_servicio_conductors')

class IndicaServicioPropietario(db.Model):
    __tablename__ = 'IndicaServicioPropietario'

    IdServicio = Column(Integer, ForeignKey('Servicio.IdServicio'), primary_key=True)
    MailPropietario = Column(String(100), ForeignKey('Propietario.MailPropietario'), primary_key=True)
    Existe = Column(Boolean, nullable=False)

    #propietario = db.relationship('Propietario', backref='indica_servicio_propietarios')
    #servicio = db.relationship('Servicio', backref='indica_servicio_propietarios')

class MarcaFavorita(db.Model):
    __tablename__ = 'MarcaFavorita'

    MailConductor = Column(String(100), ForeignKey('Conductor.MailConductor'), primary_key=True)
    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'), primary_key=True)

    #conductor = db.relationship('Conductor', backref='marca_favoritas')
    #distribuidora = db.relationship('Distribuidora', backref='marca_favoritas')

class Pregunta(db.Model):
    __tablename__ = 'Pregunta'

    IdPregunta = Column(Integer, primary_key=True)
    Texto = Column(String(500), nullable=False)
    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'), nullable=False)
    MailConductor = Column(String(100), ForeignKey('Conductor.MailConductor'), nullable=False)

    #respuestas = db.relationship('Respuesta', backref='pregunta', lazy='dynamic')

class Propietario(db.Model):
    __tablename__ = 'Propietario'

    MailPropietario = Column(String(100), primary_key=True)
    Contrasenia = Column(String(20), nullable=False)
    Nombre = Column(String(100), nullable=False)
    Apellidos = Column(String(100))
    Documento = Column(LargeBinary, nullable=False)

    #da_respuesta_propietario = db.relationship('DaRespuestaPropietario', backref='propietario', lazy='dynamic')
    #distribuidoras = db.relationship('Distribuidora', backref='propietario', lazy='dynamic')
    #indica_servicios_propietario = db.relationship('IndicaServicioPropietario', backref='propietario', lazy='dynamic')


class Respuesta(db.Model):
    __tablename__ = 'Respuesta'

    IdRespuesta = Column(Integer, primary_key=True)
    IdPregunta = Column(Integer, ForeignKey('Pregunta.IdPregunta'), nullable=False)
    Texto = Column(String(500), nullable=False)
    Verificado = Column(Boolean)

    #da_respuesta_conductors = db.relationship('DaRespuestaConductor', backref='respuesta', lazy='dynamic')
    #da_respuesta_propietarios = db.relationship('DaRespuestaPropietario', backref='respuesta', lazy='dynamic')


class Servicio(db.Model):
    __tablename__ = 'Servicio'

    IdServicio = Column(Integer, primary_key=True)
    Nombre = Column(String(255), nullable=False)

    #indica_servicio_conductors = db.relationship('IndicaServicioConductor', backref='servicio', lazy='dynamic')
    #indica_servicio_propietarios = db.relationship('IndicaServicioPropietario', backref='servicio', lazy='dynamic')
    #servicios_gasolinera = db.relationship('ServiciosGasolinera', backref='servicio', lazy='dynamic')

class ServiciosGasolinera(db.Model):
    __tablename__ = 'ServiciosGasolinera'

    IdServicio = Column(Integer, ForeignKey('Servicio.IdServicio'), primary_key=True)
    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'), primary_key=True)
    Verificado = Column(Boolean)
    Existe = Column(Boolean)

    #servicio = db.relationship('Servicio', backref='servicios_gasolineras')
    #distribuidora = db.relationship('Distribuidora', backref='servicios_gasolineras')

class SuministraEstacionRecarga(db.Model):
    __tablename__ = 'SuministraEstacionRecarga'
    
    IdDistribuidora = Column(Integer, ForeignKey('EstacionRecarga.IdDistribuidora'), primary_key=True)
    IdPunto = Column(Integer, ForeignKey('TipoPunto.IdPunto'), primary_key=True)
    CargaRapida = Column(Boolean)
    Cantidad = Column(Integer)
    Voltaje = Column(Integer)
    Amperios = Column(Integer)
    kW = Column(Integer)

    #estacion_recarga = db.relationship('EstacionRecarga', backref='suministra_estacion_recargas')
    #tipo_punto = db.relationship('TipoPunto', backref='suministra_estacion_recargas')

class SuministraGasolinera(db.Model):
    __tablename__ = 'SuministraGasolinera'

    IdDistribuidora = Column(Integer, ForeignKey('Gasolinera.IdDistribuidora'), primary_key=True)
    IdCombustible = Column(Integer, ForeignKey('TipoCombustible.IdCombustible'), primary_key=True)
    Precio = Column(Numeric, nullable=False)

    #gasolinera = db.relationship('Gasolinera', backref='suministra_gasolineras')
    #tipo_combustible = db.relationship('TipoCombustible', backref='suministra_gasolineras')

class TipoCombustible(db.Model):
    __tablename__ = 'TipoCombustible'

    IdCombustible = Column(Integer, primary_key=True)
    Nombre = Column(String(100), nullable=False)

    #suministra_gasolineras = db.relationship('SuministraGasolinera', backref='tipo_combustible', lazy='dynamic')

class TipoPunto(db.Model):
    __tablename__ = 'TipoPunto'

    IdPunto = Column(Integer, primary_key=True)
    Nombre = Column(String(100), nullable=False)

    #suministra_estacion_recargas = db.relationship('SuministraEstacionRecarga', backref='tipo_punto', lazy='dynamic')


class Ubicacion(db.Model):
    __tablename__ = 'Ubicacion'

    Longitud = Column(Numeric, primary_key=True)
    Latitud = Column(Numeric, primary_key=True)
    Provincia = Column(String(255))
    Municipio = Column(String(255))
    Localidad = Column(String(255))
    CP = Column(String(5))
    Direccion = Column(String(255))

    #distribuidoras = db.relationship('Distribuidora', backref='ubicacion', lazy='dynamic')

class PruebaUbicacion(db.Model):
    __tablename__ = 'Prueba_ubicacion'
    id = Column(Integer, primary_key=True)
    location = Column(Geography('POINT'))


