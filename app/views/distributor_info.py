from flask import request, jsonify, Blueprint, render_template, flash, redirect, url_for
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField, HiddenField, SubmitField, SelectField, StringField
from wtforms.validators import DataRequired, Optional, ValidationError
from flask_login import login_required, current_user

import app.views.database as db
import app.views.helpers as helpers
import json
import requests 
import pytz

distributor_bp = Blueprint('distributor', __name__)

headers = {
    'User-Agent': 'gasWise/1.0',
    'Referer': 'http://gaswise.com'
}

venta = {
    "Private - Restricted Access": "Privada",
    "Public - Notice Required": "Pública - Requiere aviso",
    "Public": "Pública",
    "(Unknown)": "-",
    "Public - Pay At Location": "Pública - Pago en el lugar",
    "Private - For Staff, Visitors or Customers": "Privada - Para personal, visitantes o clientes",
    "Privately Owned - Notice Required": "Privada - Requiere aviso",
    "Public - Membership Required": "Pública - Requiere afiliación"
}

class RatingForm(FlaskForm):
    rating = StringField('Rating', validators=[DataRequired()])
    comment = TextAreaField('Comentario', default='', validators=[Optional()])
    Id_distribuidora = IntegerField('Id_distribuidora', validators=[DataRequired()])
    submit = SubmitField('Enviar valoración')

def get_address(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    response = requests.get(url, headers=headers)
    data = response.json()
    if data:
        return data['display_name']
    return None

def distributor_details(lat, lon, id):
    info, lat, lon = db.get_distributor_data(lat, lon, id)

    tipo = info[2]

    if tipo == 'E':
        tipo_venta = venta.get(info[3], "-")
        response = {
            'Nombre': info[0],
            'Tipo_venta': tipo_venta,
            'Precio': info[4], 
            'Tipo': tipo, 
            'Id_distribuidora': info[5]
        }
    else:
        tipo_venta = 'Pública' if info[3] else 'Restringida a socios o cooperativistas'
        margen = 'Derecho' if info[5] == 'D' else 'Izquierdo' if info[5] == 'I' else None
        response = {
            'Nombre': info[0],
            'Tipo_venta': tipo_venta,
            'Email': info[1],
            'Horario': info[4],
            'Margen': margen,
            'Tipo': tipo, 
            'Id_distribuidora': info[6], 
            'Servicios_verificados': info[7]
        }
        
    response.update({'Direccion': get_address(lat, lon)})
    return response, tipo, lat, lon


#Ruta para mostrar la informacion de una distribuidora tanto a un conductor como a un propietario
@distributor_bp.route('/distributor_info', methods=['GET', 'POST'])
@distributor_bp.route('/distributor_info/<int:id>', methods=['GET', 'POST'])
@login_required
def distributor_info(id=None):
    form = RatingForm()

    if form.validate_on_submit():
        id_rating = form.Id_distribuidora.data
        rating = form.rating.data
        comment = form.comment.data
        mail = current_user.MailConductor
        db.insert_rating(id_rating, rating, comment, mail)
        flash('Valoración enviada correctamente', 'success')


    # Obtener latitud y longitud de los parámetros de la URL
    latitud = request.args.get('lat') if request.args.get('lat') else None
    longitud = request.args.get('lon') if request.args.get('lon') else None

    # Información de la distribuidora
    info, tipo, latitud, longitud = distributor_details(latitud, longitud, id)

    # Combustibles y precios (si gasolinera)
    precios = db.get_gas_station_prices(latitud, longitud) if tipo == 'G' else []

    #Puntos de recarga (si estación de recarga)
    puntos_recarga = db.get_charge_points(latitud, longitud) if tipo == 'E' else []

    # Servicios (si estación de recarga)
    servicios = db.get_gas_station_services(latitud, longitud) if tipo == 'G' else []

    # Preguntas y respuestas
    preguntas, respuestas = db.get_questions(latitud, longitud)

    # Obtener parámetro de ordenación
    sort_by = request.args.get('sort_by', 'rating_desc')

    # Valoraciones
    valoraciones, valoracion_media = db.get_ratings(latitud, longitud, sort_by)

    #Tipo de usuario que quiere acceder a la página
    user_type = helpers.user_type() 

    return render_template('info_distributor.html', form=form, tipo=tipo, distributor=info, precios=precios, puntos_recarga=puntos_recarga, servicios=servicios, preguntas=preguntas, respuestas=respuestas, valoraciones=valoraciones, valoracion_media=valoracion_media, user_type=user_type)

#Ruta para mostrar el formulario para indicar los servicios de una distribuidora
@distributor_bp.route('/service/form/<int:distributor_id>')
@login_required
def service_form(distributor_id):
    services = db.services_names
    user_type = helpers.user_type()

    return render_template('service_form.html', distributor_id=distributor_id, services=services, user_type=user_type)

#Ruta para indicar los servicios de una gasolinera
@distributor_bp.route('/distributor/services/<int:distributor_id>', methods=['POST'])
@login_required
def services(distributor_id):
    selected_services = {key: request.form[key] for key in request.form if request.form[key] != 'unknown'}
    
    user_type = helpers.user_type() 
    # Procesar los servicios (por ejemplo, insertarlos en la base de datos)
    if user_type == "C":
        db.insert_db_services_driver(distributor_id, selected_services)
    else:
        db.insert_db_services_owner(distributor_id, selected_services)
    
    return redirect(url_for('distributor.distributor_info', id=distributor_id))

#Ruta para enviar una pregunta
@distributor_bp.route('/question', methods=['GET', 'POST'])
@login_required
@helpers.driver_required
def question():
    texto_pregunta = request.form['pregunta']
    id_distribuidora = request.form['id_distribuidora']
    
    # Obtener la fecha y la hora actuales
    timezone = pytz.timezone('Europe/Madrid')
    now = datetime.now(timezone)
    fecha_pregunta = now.strftime("%Y-%m-%d")
    hora_pregunta = now.strftime("%H:%M:%S")
    mail_conductor = current_user.MailConductor
    
    # Insertar la pregunta en la base de datos
    db.insert_db_question(texto_pregunta, fecha_pregunta, hora_pregunta, id_distribuidora, mail_conductor)
    
    return redirect(url_for('distributor.distributor_info', id=id_distribuidora))

#Ruta para enviar una respuesta a una pregunta
@distributor_bp.route('/answer', methods=['POST'])
@login_required
def answer():
    texto_respuesta = request.form['respuesta']
    id_pregunta = request.form['id_pregunta']
    distributor_id = request.form['id_distribuidora']
    
    # Obtener la fecha y la hora actuales
    timezone = pytz.timezone('Europe/Madrid')
    now = datetime.now(timezone)
    fecha_respuesta = now.strftime("%Y-%m-%d")
    hora_respuesta = now.strftime("%H:%M:%S")
    
    # Determinar el tipo de usuario
    user_type = helpers.user_type()
    
    if user_type == "C":
        verificada = False
        mail_conductor = current_user.MailConductor
        mail_propietario = None
    else:
        verificada = True
        mail_conductor = None
        mail_propietario = current_user.MailPropietario
    
    # Insertar la respuesta en la base de datos
    db.insert_db_answer(texto_respuesta, fecha_respuesta, hora_respuesta, verificada, id_pregunta, mail_conductor, mail_propietario)
    
    return redirect(url_for('distributor.distributor_info', id=distributor_id))

#Marcar una distribuidora como favorita
@distributor_bp.route('/add_fav/<int:distributor_id>', methods=['GET', 'POST'])
@login_required
def add_fav(distributor_id):
    mail = current_user.MailConductor
    db.insert_fav_distributor(distributor_id, mail)
    return redirect(url_for('distributor.distributor_info', id=distributor_id))

#Quitar una distribuidora de favoritos
@distributor_bp.route('/delete_fav/<int:distributor_id>', methods=['POST'])
@login_required
def delete_fav(distributor_id):
    mail = current_user.MailConductor
    db.delete_fav_distributor(distributor_id, mail)
    return redirect(url_for('distributor.distributor_info', id=distributor_id))

#Ruta para saber si una distribuidora es favorita
@distributor_bp.route('/is_fav/<int:distributor_id>', methods=['GET', 'POST'])
@login_required
def is_fav(distributor_id):
    mail = current_user.MailConductor
    fav = db.get_is_fav_distributor(distributor_id, mail)
    if fav:
        fav = "1"
    else:
        fav = "0"
    return fav
