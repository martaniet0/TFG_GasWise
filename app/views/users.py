from flask import Blueprint, redirect, url_for, render_template, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_login import login_user, current_user, logout_user, login_required

from app import bcrypt
from app.models import Conductor, Propietario, Administrador
import app.views.database as database

users_bp = Blueprint('users', __name__)


class driver_registration(FlaskForm):
    nombre = StringField('Nombre',
                           validators=[DataRequired(), Length(min=2, max=100)])
    apellidos = StringField('Apellidos',
                           validators=[Length(min=0, max=100)])
    tipoVehiculo = SelectField('Tipo de Vehiculo', choices=[('E', 'Eléctrico'), ('H', 'Híbrido enchufable'), ('D', 'Híbrido'), ('G', 'Gasolina, Diesel o Gas')])
    mail = StringField('Correo',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmación de la contraseña',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

    def validate_mail(self, mail):
        conductor = Conductor.query.filter_by(MailConductor=mail.data).first()
        if conductor:
            raise ValidationError('Ya existe un usuario registrado con ese mail. Por favor, introduzca otro.')

class driver_login(FlaskForm):
    mail = StringField('Correo',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class driver_update(FlaskForm):
    nombre = StringField('Nombre',
                        validators=[DataRequired(), Length(min=2, max=100)])
    apellidos = StringField('Apellidos',
                           validators=[Length(min=0, max=100)])
    tipoVehiculo = SelectField('Tipo de Vehiculo', choices=[('E', 'Eléctrico'), ('H', 'Híbrido enchufable'), ('D', 'Híbrido'), ('G', 'Gasolina, Diesel o Gas')])
    password = PasswordField('Contraseña')
    confirm_password = PasswordField('Confirmación de la contraseña',
                                     validators=[EqualTo('password')])
    submit = SubmitField('Modificar perfil')

############################################################################################################
#RUTAS
############################################################################################################

#Ruta para registrar a un conductor o propietario. Arriba se selecciona que tipo de usuario es y el formulario se adapta a ello
#!!!FALTA IMPLEMENTAR LA PARTE DE PROPIETARIO!!!
@users_bp.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('search.mapa'))
    form = driver_registration()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        database.insert_driver_data_BD(mail=form.mail.data, contrasenia=hashed_password, nombre=form.nombre.data, apellidos=form.apellidos.data, tipo_vehiculo=form.tipoVehiculo.data)
        flash(f'¡Genial, {form.nombre.data}! Tu cuenta ha sido creada con éxito. Ya puedes inciar sesión.', 'success')
        return redirect(url_for('users.login'))
    return render_template('registration.html', title='Register', form=form)

#Ruta para loguear a un conductor o propietario
#!!!FALTA IMPLEMENTAR LA PARTE DE PROPIETARIO!!!
#AÑADIR A PROPIETARIO ATRIBUTO ACTIVADO
@users_bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('search.mapa'))
    form = driver_login()
    if form.validate_on_submit():
        conductor = Conductor.query.filter_by(MailConductor=form.mail.data).first()
        if conductor and bcrypt.check_password_hash(conductor.Contrasenia, form.password.data):
            login_user(conductor)
            return redirect(url_for('search.mapa'))
        else:
            flash('¡Error! Por favor, comprueba tu correo y contraseña.', 'danger')
    return render_template('login.html', title='Login', form=form)

#Ruta para cerrar sesión
@users_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template('logout.html', title='Adiós')

#Ruta para ver la información de un conductor o propietario
@users_bp.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = driver_update()
    if form.validate_on_submit():
        hashed_password = None
        if form.password.data:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        database.update_driver_data_BD(mail=current_user.MailConductor, nombre=form.nombre.data, apellidos=form.apellidos.data, tipo_vehiculo=form.tipoVehiculo.data, contrasenia=hashed_password)
        flash('Tu perfil ha sido modificado correctamente.', 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.nombre.data = current_user.Nombre
        form.apellidos.data = current_user.Apellidos
        form.tipoVehiculo.data = current_user.TipoVehiculo
    return render_template('account.html', title='Account', form=form)