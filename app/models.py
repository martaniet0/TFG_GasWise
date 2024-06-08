#!!!REVISAR RELACIONES
from app import db, login_manager
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Time, Numeric, Boolean, LargeBinary, UniqueConstraint
from geoalchemy2 import Geography
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_email):
    user = Conductor.query.get(user_email)
    if user is not None:
        return user
    user = Propietario.query.get(user_email)
    if user is not None:
        return user
    return Administrador.query.get(user_email)

class Administrador(db.Model, UserMixin):
    __tablename__= 'Administrador'

    MailAdmin = Column(String(100), primary_key=True)
    Contrasenia = Column(String(255), nullable=False)
    Nombre = Column(String(100), nullable=False)
    Apellidos = Column(String(100))

    def get_id(self):
        return self.MailAdmin
    
    def get_user_type(self):
        return 'Administrador'


class Conductor(db.Model, UserMixin):
    __tablename__ = 'Conductor'

    MailConductor = Column(String(100), primary_key=True)
    Contrasenia = Column(String(255), nullable=False)
    Nombre = Column(String(100), nullable=False)
    Apellidos = Column(String(100))
    TipoVehiculo = Column(String(1), nullable=False)

    def get_id(self):
        return self.MailConductor
    
    def get_user_type(self):
        return 'Conductor'
    
class Valoracion(db.Model):
    __tablename__ = 'Valoracion'

    IdValoracion = Column(Integer, primary_key=True)
    Puntuacion = Column(Integer, nullable=False)
    Texto = Column(String(500))
    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'), nullable=False)
    MailConductor = Column(String(100), ForeignKey('Conductor.MailConductor'), nullable=False)
    ClasificacionTexto = Column(Integer)

class Distribuidora(db.Model):
    __tablename__ = 'Distribuidora'
    __table_args__ = (
        UniqueConstraint('IdAPI'),
        UniqueConstraint('Location'),
    )

    IdDistribuidora = Column(Integer, primary_key=True)
    Nombre = Column(String(100))
    MailPropietario = Column(String(100), ForeignKey('Propietario.MailPropietario'))
    IdAPI = Column(String(100), unique=True)
    Location = Column(Geography('POINT'), ForeignKey('Ubicacion.Location'))
    Tipo = Column(String(1))

class EstacionRecarga(db.Model):
    __tablename__ = 'EstacionRecarga'

    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'), primary_key=True)
    TipoVenta = Column(String(255))
    Precio = Column(String(255))

class Gasolinera(db.Model):
    __tablename__ = 'Gasolinera'

    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'), primary_key=True)
    TipoVenta = Column(Boolean)
    Horario = Column(String(255))
    Margen = Column(String(1))
    ServiciosVerificados = Column(Boolean)

class IndicaServicioConductor(db.Model):
    __tablename__ = 'IndicaServicioConductor'

    IdServicio = Column(Integer, ForeignKey('Servicio.IdServicio'), primary_key=True)
    MailConductor = Column(String(100), ForeignKey('Conductor.MailConductor'), primary_key=True)
    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'), primary_key=True)
    Existe = Column(Boolean, nullable=False)

class MarcaFavorita(db.Model):
    __tablename__ = 'MarcaFavorita'

    MailConductor = Column(String(100), ForeignKey('Conductor.MailConductor'), primary_key=True)
    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'), primary_key=True)

class Pregunta(db.Model):
    __tablename__ = 'Pregunta'

    IdPregunta = Column(Integer, primary_key=True)
    TextoPregunta = Column(String(500), nullable=False) #!!!Revisar si es String
    Fecha = Column(Date, nullable=False) #!!!Revisar si es Date
    Hora = Column(Time, nullable=False) #!!!Revisar si es Time
    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'), nullable=False)
    MailConductor = Column(String(100), ForeignKey('Conductor.MailConductor'), nullable=False)

class Propietario(db.Model, UserMixin):
    __tablename__ = 'Propietario'

    MailPropietario = Column(String(100), primary_key=True)
    Contrasenia = Column(String(255), nullable=False)
    Nombre = Column(String(100), nullable=False)
    Apellidos = Column(String(100))
    Activo = Column(Boolean, nullable=False)

    def get_id(self):
        return self.MailPropietario
    
    def get_user_type(self):
        return 'Propietario'
    
    @property
    def is_active(self):
        return self.Activo

    #establece si el usuario esta o no activo
    @is_active.setter
    def is_active(self, value):
        self.Activo = value

class PoseeDistribuidora(db.Model):
    __tablename__ = 'PoseeDistribuidora'

    IdPosee= Column(Integer, primary_key=True)
    MailPropietario = Column(String(100), ForeignKey('Propietario.MailPropietario'), nullable=False)
    Documento = Column(LargeBinary, nullable=False)
    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'))
    Confirmado = Column(Boolean)
    Revisado = Column(Boolean)


class Respuesta(db.Model):
    __tablename__ = 'Respuesta'

    IdRespuesta = Column(Integer, primary_key=True)
    TextoRespuesta = Column(String(500), nullable=False)#!!!Revisar si es String
    Fecha = Column(Date, nullable=False)#!!!Revisar si es Date
    Hora = Column(Time, nullable=False)#!!!Revisar si es Time
    Verificada = Column(Boolean, nullable=False)
    IdPregunta = Column(Integer, ForeignKey('Pregunta.IdPregunta'), nullable=False)
    MailConductor = Column(String(100), ForeignKey('Conductor.MailConductor'))
    MailPropietario = Column(String(100), ForeignKey('Propietario.MailPropietario'))
    

class Servicio(db.Model):
    __tablename__ = 'Servicio'

    IdServicio = Column(Integer, primary_key=True)
    Nombre = Column(String(255), nullable=False)

class ServiciosGasolinera(db.Model):
    __tablename__ = 'ServiciosGasolinera'

    IdServicio = Column(Integer, ForeignKey('Servicio.IdServicio'), primary_key=True)
    IdDistribuidora = Column(Integer, ForeignKey('Distribuidora.IdDistribuidora'), primary_key=True)
    Verificado = Column(Boolean)
    Existe = Column(Boolean)
    Porcentaje = Column(Numeric)

class SuministraEstacionRecarga(db.Model):
    __tablename__ = 'SuministraEstacionRecarga'
    
    IdDistribuidora = Column(Integer, ForeignKey('EstacionRecarga.IdDistribuidora'), primary_key=True)
    IdPunto = Column(Integer, ForeignKey('TipoPunto.IdPunto'), primary_key=True)
    CargaRapida = Column(Boolean)
    Cantidad = Column(Integer)
    Voltaje = Column(Integer)
    Amperios = Column(Integer)
    kW = Column(Integer)

class SuministraGasolinera(db.Model):
    __tablename__ = 'SuministraGasolinera'

    IdDistribuidora = Column(Integer, ForeignKey('Gasolinera.IdDistribuidora'), primary_key=True)
    IdCombustible = Column(Integer, ForeignKey('TipoCombustible.IdCombustible'), primary_key=True)
    Precio = Column(Numeric, nullable=False)

class TipoCombustible(db.Model):
    __tablename__ = 'TipoCombustible'

    IdCombustible = Column(Integer, primary_key=True)
    Nombre = Column(String(100), nullable=False)

class TipoPunto(db.Model):
    __tablename__ = 'TipoPunto'

    IdPunto = Column(Integer, primary_key=True)
    Nombre = Column(String(100), nullable=False)

class Ubicacion(db.Model):
    __tablename__ = 'Ubicacion'

    Location = Column(Geography('POINT'), primary_key=True)
    Provincia = Column(String(255))
    Municipio = Column(String(255))
    Localidad = Column(String(255))
    CP = Column(String(5))
    Direccion = Column(String(255))



