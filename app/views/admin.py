from flask import request, jsonify, Blueprint, render_template, redirect, url_for, send_file, flash
from flask_login import login_required

import io

import app.views.database as db
import app.views.helpers as helpers

admin_bp = Blueprint('admin', __name__)

#Ruta para visualizar las gasolineras pendientes de verificación 
@admin_bp.route('/home_admin')
@helpers.admin_required
@login_required
def home_admin():
    distributors = db.get_distributors_pending_verification()
    return render_template('admin.html', distributors=distributors)

#Ruta para descargarse el documento

@admin_bp.route('/admin/get_document/<int:id_posee>')
@helpers.admin_required
@login_required
def get_document(id_posee):
    document = db.get_distributor_document(id_posee)
    return send_file(io.BytesIO(document), mimetype='application/pdf', as_attachment=True, download_name='verificacion.pdf')

#Ruta para confirmar que una gasolinera pertenece a un propietario 
@admin_bp.route('/confirm_property')
@helpers.admin_required
@login_required
def confirm_property():
    distribuidora_id = request.args.get('distribuidora_id')
    mail_propietario = request.args.get('mailPropietario')
    id_posee = request.args.get('IdPosee')

    if distribuidora_id and mail_propietario and id_posee:
        try:
            db.insert_bd_confirmed_property(distribuidora_id, mail_propietario, id_posee)
            return redirect(url_for('admin.home_admin'))
        except Exception as e:
            return str(e), 500
    else:
        return "Missing parameters", 400

#Ruta para rechazar que una gasolinera pertenece a un propietario
@admin_bp.route('/reject_property')
@helpers.admin_required
@login_required
def reject_property():
    id_posee = request.args.get('id')
    with open('/app/test/log2.txt', 'a') as f:
        f.write("\nIdPosee " + str(id_posee) + '\n')

    if id_posee:
        try:
            db.insert_bd_rejected_property(id_posee)
            return redirect(url_for('admin.home_admin'))
        except Exception as e:
            return str(e), 500
    else:
        return "Missing parameters", 400
    
#Ruta para eliminar un usuario
@admin_bp.route('/delete_user', methods=['POST'])
@helpers.admin_required
@login_required
def delete_user():
    email = request.form.get('email')
    if db.delete_user_BD(email):
        flash(f'Usuario con correo {email} eliminado exitosamente.', 'success')
    else:
        flash(f'Usuario con correo {email} no existe.', 'danger')
    return redirect(url_for('admin.home_admin'))
