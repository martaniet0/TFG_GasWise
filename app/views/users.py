from flask import Blueprint, redirect, url_for, render_template, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from flask_login import login_user, current_user, logout_user, login_required

from app import bcrypt
from app.models import Conductor, Propietario, Administrador
import app.views.database as database
import app.views.helpers as helpers

users_bp = Blueprint('users', __name__)

#Variable global para distinguier entre conductores y propietarios
@users_bp.context_processor
def context_processor():
    return dict(user_type=helpers.user_type)


class registration(FlaskForm):
    tipoUsuario = SelectField('Tipo de Usuario', choices=[('C', 'Conductor'), ('P', 'Propietario')])
    nombre = StringField('Nombre',
                           validators=[DataRequired(), Length(min=2, max=100)])
    apellidos = StringField('Apellidos',
                           validators=[Length(min=0, max=100)])
    tipoVehiculo = SelectField('Tipo de Vehiculo', choices=[('E', 'Eléctrico'), ('H', 'Híbrido enchufable'), ('D', 'Híbrido'), ('G', 'Gasolina, Diesel o Gas')], validators=[Optional()])
    doc = FileField('Documento acreditativo', validators=[Optional()])
    mail = StringField('Correo',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmación de la contraseña',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

    def validate(self, extra_validators=None):
        is_valid = super(registration, self).validate()
        if not is_valid:
            return False
        
        if self.tipoUsuario.data == 'P':
            if not self.doc.data:
                self.doc.errors.append('El documento acreditativo es requerido para los propietarios.')
                return False
        elif self.tipoUsuario.data == 'C':
            if not self.tipoVehiculo.data:
                self.tipoVehiculo.errors.append('El tipo de vehículo es requerido para los conductores.')
                return False
        return True

    def validate_mail(self, mail):
        conductor = Conductor.query.filter_by(MailConductor=mail.data).first()
        propietario = Propietario.query.filter_by(MailPropietario=mail.data).first()
        if conductor or propietario:
            raise ValidationError('Ya existe un usuario registrado con ese mail. Por favor, introduzca otro.')

class user_login(FlaskForm):
    mail = StringField('Correo',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class update(FlaskForm):
    nombre = StringField('Nombre',
                        validators=[DataRequired(), Length(min=2, max=100)])
    apellidos = StringField('Apellidos',
                           validators=[Length(min=0, max=100)])
    tipoVehiculo = SelectField('Tipo de Vehiculo', choices=[('E', 'Eléctrico'), ('H', 'Híbrido enchufable'), ('D', 'Híbrido'), ('G', 'Gasolina, Diesel o Gas')], validators=[Optional()])
    password = PasswordField('Contraseña')
    confirm_password = PasswordField('Confirmación de la contraseña',
                                     validators=[EqualTo('password')])
    submit = SubmitField('Modificar perfil')

############################################################################################################
#RUTAS
############################################################################################################

#Ruta para registrar a un conductor o propietario. Arriba se selecciona que tipo de usuario es y el formulario se adapta a ello
@users_bp.route("/register", methods=['GET', 'POST'])
def register():
    if helpers.user_type() == 'C':
        return redirect(url_for('search.mapa'))
    elif helpers.user_type() == 'P':
        return redirect(url_for('users.wait'))
    form = registration()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        if form.tipoUsuario.data == 'C':
            database.insert_driver_data_BD(mail=form.mail.data, contrasenia=hashed_password, nombre=form.nombre.data, apellidos=form.apellidos.data, tipo_vehiculo=form.tipoVehiculo.data)
            flash(f'¡Genial, {form.nombre.data}! Tu cuenta ha sido creada con éxito. Ya puedes inciar sesión.', 'success')
            return redirect(url_for('users.login'))
        else:
            if form.doc.data:
                documento = form.doc.data.read()  
                database.insert_owner_data_BD(mail=form.mail.data, contrasenia=hashed_password, nombre=form.nombre.data, apellidos=form.apellidos.data, documento=documento, activo=False)
            else:
                flash('Documento acreditativo es requerido.', 'error')
                return render_template('registration.html', form=form)
            flash(f'¡Genial, {form.nombre.data}! Tu registro ha sido completado con éxito. Ahora debes esperar hasta que el administrador te envie un correo informándote de que tu cuenta está habilitada. Hasta ese momento no podrás logearte.', 'success')
            return render_template('logout.html', title='¡Hasta pronto!')
    else:
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                flash(f'Error en {fieldName}: {err}', 'danger')
    return render_template('registration.html', title='Register', form=form)

#Ruta para loguear a un conductor o propietario
@users_bp.route("/login", methods=['GET', 'POST'])
def login():
    if helpers.user_type() == 'C' and current_user.is_authenticated:
        return redirect(url_for('search.mapa'))
    elif helpers.user_type() == 'P' and current_user.is_authenticated:
        if current_user.Activo:
            return redirect(url_for('users.home_owner'))
        else:
            return redirect(url_for('users.wait'))
    form = user_login()
    if form.validate_on_submit():
        usuario = Conductor.query.filter_by(MailConductor=form.mail.data).first()
        tipo = "Conductor" if usuario else None
        if not usuario:
            usuario = Propietario.query.filter_by(MailPropietario=form.mail.data).first()
            tipo = "Propietario"
        if usuario and bcrypt.check_password_hash(usuario.Contrasenia, form.password.data):
            if tipo == "Propietario" and not usuario.Activo:
                    return redirect(url_for('users.wait'))
            login_user(usuario)
            if tipo == "Conductor":
                return redirect(url_for('search.mapa'))
            elif tipo == "Propietario":
                return redirect(url_for('users.home_owner'))
        else:
            flash('¡Error! Por favor, comprueba tu correo y contraseña.', 'danger')
    return render_template('login.html', title='Login', form=form)

#Ruta para cerrar sesión
@users_bp.route("/logout")
def logout():
    logout_user()
    return render_template('logout.html', title='¡Hasta pronto!')

#Ruta para ver la información de un conductor o propietario
@users_bp.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = update()
    if form.validate_on_submit():
        hashed_password = None
        if form.password.data:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        tipo = helpers.user_type()
        if tipo == "C":
            database.update_driver_data_BD(mail=current_user.MailConductor, nombre=form.nombre.data, apellidos=form.apellidos.data, tipo_vehiculo=form.tipoVehiculo.data, contrasenia=hashed_password)
            flash('Tu perfil ha sido modificado correctamente.', 'success')
        else:
            database.update_owner_data_BD(mail=current_user.MailPropietario, nombre=form.nombre.data, apellidos=form.apellidos.data, contrasenia=hashed_password)
            flash('Tu perfil ha sido modificado correctamente.', 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.nombre.data = current_user.Nombre
        form.apellidos.data = current_user.Apellidos
        if helpers.user_type() == 'C':
            form.tipoVehiculo.data = current_user.TipoVehiculo
    return render_template('account.html', title='Account', form=form)

#Ruta para mostrar página de espera al propietario
@users_bp.route("/owner/wait")
def wait():
    return render_template('owner_wait.html')

#Ruta para mostrar página home al propietario
@users_bp.route("/owner/home")
@login_required
@helpers.owner_required
def home_owner():
    #Tengo que pasarle los distribuidores que tiene este owner
    return render_template('owner_home.html', title='Home')


