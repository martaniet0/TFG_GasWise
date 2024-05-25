from flask import request, jsonify, Blueprint, render_template, flash, redirect, url_for
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField, HiddenField, SubmitField, SelectField, StringField
from wtforms.validators import DataRequired, Optional, ValidationError
from flask_login import login_required

import app.views.database as db
import app.views.helpers as helpers
import json
import requests 
from flask_login import current_user

distributor_bp = Blueprint('distributor', __name__)

headers = {
    'User-Agent': 'gasWise/1.0',
    'Referer': 'http://gaswise.com'
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
        response = {
            'Nombre': info[0],
            'Tipo_venta': info[3],
            'Precio': info[4], #!!!
            'Tipo': tipo, 
            'Id_distribuidora': info[4]
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
            'Id_distribuidora': info[6]
        }
        
    response.update({'Direccion': get_address(lat, lon)})
    return response, tipo, lat, lon


#Ruta para mostrar la informacion de una distribuidora
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
        #redirect(url_for('distributor.distributor_info'))


    # Obtener latitud y longitud de los parámetros de la URL
    latitud = request.args.get('lat') if request.args.get('lat') else None
    longitud = request.args.get('lon') if request.args.get('lon') else None
    with open('app/test/log.txt', 'a') as f:
        f.write(f'\n En la capación de args latitud: {latitud}, longitud: {longitud}, id: {id}\n')

    # Información de la distribuidora
    info, tipo, latitud, longitud = distributor_details(latitud, longitud, id)

    # Combustibles y precios (si gasolinera)
    precios = db.get_gas_station_prices(latitud, longitud) if tipo == 'G' else []

    # Servicios (si estación de recarga)
    servicios = db.get_gas_station_services(latitud, longitud) if tipo == 'G' else []
    with open('app/test/log.txt', 'w') as f:
        f.write(f'\n Aquí no estoy llegando\n')

    # Preguntas y respuestas
    preguntas, respuestas = db.get_questions(latitud, longitud)

    # Valoraciones
    valoraciones, valoracion_media = db.get_ratings(latitud, longitud)

    return render_template('info_distributor.html', form=form, tipo=tipo, distributor=info, precios=precios, servicios=servicios, preguntas=preguntas, respuestas=respuestas, valoraciones=valoraciones, valoracion_media=valoracion_media)

@distributor_bp.route('/service/form/<int:distributor_id>')
def service_form(distributor_id):
    services = db.services_names
    return render_template('service_form.html', distributor_id=distributor_id, services=services)


@distributor_bp.route('/distributor/services/<int:distributor_id>', methods=['POST'])
@login_required
def services(distributor_id):
    selected_services = {key: request.form[key] for key in request.form if request.form[key] != 'unknown'}
    
    # Procesar los servicios (por ejemplo, insertarlos en la base de datos)
    db.insert_db_services(distributor_id, selected_services)
    
    return redirect(url_for('distributor.distributor_info', id=distributor_id))

@distributor_bp.route('/answer', methods=['POST'])
@login_required
def answer():
    texto_respuesta = request.form['respuesta']
    id_pregunta = request.form['id_pregunta']
    distributor_id = request.form['id_distribuidora']
    
    # Obtener la fecha y la hora actuales
    fecha_respuesta = datetime.now().strftime("%Y-%m-%d")
    hora_respuesta = datetime.now().strftime("%H:%M:%S")
    
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
    db.insert_db_answer(
        TextoRespuesta=texto_respuesta,
        Fecha=fecha_respuesta,
        Hora=hora_respuesta,
        Verificada=verificada,
        IdPregunta=id_pregunta,
        MailConductor=mail_conductor,
        MailPropietario=mail_propietario
    )
    
    return redirect(url_for('distributor.distributor_info', id=distributor_id))
