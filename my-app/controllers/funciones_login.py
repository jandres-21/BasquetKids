# Importandopaquetes desde flask
from flask import session, flash, request, redirect, url_for
from flask import get_flashed_messages

# Importando conexion a BD
from conexion.conexionBD import connectionBD
# Para  validar contraseña
from werkzeug.security import check_password_hash

import re
# Para encriptar contraseña generate_password_hash
from werkzeug.security import generate_password_hash
import datetime
# utils_hora.py
from datetime import datetime
import pytz

# Definir hora de Guayaquil al cargar el módulo
zona_ecuador = pytz.timezone('America/Guayaquil')

# Función reutilizable
def ahora_guayaquil():
    return datetime.now(zona_ecuador).strftime('%Y-%m-%d %H:%M:%S')

def recibeInsertRegisterUser(cedula, name, surname, id_area, id_rol, pass_user):
    # Validar datos (ya lo haces con validarDataRegisterLogin)
    if not validarDataRegisterLogin(cedula, name, surname, pass_user):
        return "invalid_data"

    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as mycursor:
                # Verificar si la cédula ya existe
                sql_check = "SELECT COUNT(*) AS count FROM usuarios WHERE cedula = %s"
                mycursor.execute(sql_check, (cedula,))
                result = mycursor.fetchone()
                if result['count'] > 0:
                    return "duplicado"

                # Hashear contraseña
                nueva_password = generate_password_hash(pass_user, method='scrypt')

                # Insertar nuevo usuario
                sql_insert = """
                    INSERT INTO usuarios (cedula, nombre_usuario, apellido_usuario, id_area, id_rol, password) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                valores = (cedula, name, surname, id_area, id_rol, nueva_password)
                mycursor.execute(sql_insert, valores)
                conexion_MySQLdb.commit()

                if mycursor.rowcount > 0:
                    return "ok"
                else:
                    return "error"

    except Exception as e:
        print(f"Error en el Insert users: {e}")
        return "error"



# Validando la data del Registros para el login
def validarDataRegisterLogin(cedula, name, surname, pass_user):
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as cursor:
                querySQL = "SELECT * FROM usuarios WHERE cedula = %s"
                cursor.execute(querySQL, (cedula,))
                userBD = cursor.fetchone()  # Obtener la primera fila de resultados

                if userBD is not None:
                    flash('el registro no fue procesado ya existe la cuenta', 'error')
                    return False
                elif not cedula or not name or not pass_user:
                    flash('por favor llene los campos del formulario.', 'error')
                    return False
                else:
                    return True
    except Exception as e:
        print(f"Error en validarDataRegisterLogin : {e}")
        return []


def info_perfil_session(id):
    print(id)
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as cursor:
                querySQL = "SELECT id_usuario, nombre_usuario, apellido_usuario, cedula, id_area, id_rol FROM usuarios WHERE id_usuario = %s"
                cursor.execute(querySQL, (id,))
                info_perfil = cursor.fetchall()
        return info_perfil
    except Exception as e:
        print(f"Error en info_perfil_session : {e}")
        return []



def dataLoginSesion():
    inforLogin = {
        "id": session.get('id'),
        "name": session.get('name'),  # o cambiarlo a 'nombre_usuario'
        "apellido_usuario": session.get('apellido_usuario'),  # Agrega esta línea
        "cedula": session.get('cedula'),
        "rol": session.get('rol')
    }
    return inforLogin



# FUNCIONALIDAD AGREGADA PARA GUARDAR SESIÓN AL INICIAR SESIÓN

def obtenerUsuarioPorId(id_usuario):
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as cursor:
                query = "SELECT * FROM usuarios WHERE id_usuario = %s"
                cursor.execute(query, (id_usuario,))
                return cursor.fetchone()
    except Exception as e:
        print(f"Error en obtenerUsuarioPorId: {e}")
        return None

def actualizarUsuario(id_usuario, cedula, nombre, apellido, id_area, id_rol):
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor() as cursor:
                sql = """
                    UPDATE usuarios 
                    SET cedula=%s, nombre_usuario=%s, apellido_usuario=%s, id_area=%s, id_rol=%s
                    WHERE id_usuario=%s
                """
                cursor.execute(sql, (cedula, nombre, apellido, id_area, id_rol, id_usuario))
                conexion_MySQLdb.commit()
                return cursor.rowcount > 0
    except Exception as e:
        print(f"Error en actualizarUsuario: {e}")
        return False

def obtener_areas():
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT id_area, nombre_area FROM area")
                areas = cursor.fetchall()
                print("Áreas encontradas:", areas)  # deberías ver [(1, 'Area 1')]
                return areas                      # devuelve aquí, no llamando de nuevo a fetchall()
    except Exception as e:
        print(f"Error en obtener_areas: {e}")
        return []

    
def obtener_roles():
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT id_rol, nombre_rol FROM rol")
                return cursor.fetchall()
    except Exception as e:
        print(f"Error en obtener_roles: {e}")
        return []
    


    