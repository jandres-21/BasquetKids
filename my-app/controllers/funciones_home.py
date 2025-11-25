
# Para subir archivo tipo foto al servidor
from werkzeug.utils import secure_filename
import uuid  # Modulo de python para crear un string

from conexion.conexionBD import connectionBD  # Conexión a BD

import datetime
import re
import os

from os import remove  # Modulo  para remover archivo
from os import path  # Modulo para obtener la ruta o directorio
from datetime import timedelta
from datetime import datetime
import pytz

import openpyxl  # Para generar el excel
# biblioteca o modulo send_file para forzar la descarga
from flask import send_file, session
zona_ecuador = pytz.timezone('America/Guayaquil')

# Función reutilizable
def ahora_guayaquil():
    return datetime.now(zona_ecuador).strftime('%Y-%m-%d %H:%M:%S')

def accesosReporte():
    try:
        with connectionBD() as conexion_MYSQLdb:
            with conexion_MYSQLdb.cursor(dictionary=True) as cursor:
                if session['rol'] == 1:
                    querySQL = """
                        SELECT a.id_acceso, a.cedula, a.fecha, r.nombre_rol as rol, u.nombre_usuario, u.apellido_usuario
                        FROM accesos a
                        JOIN usuarios u ON a.cedula = u.cedula
                        JOIN rol r ON u.id_rol = r.id_rol
                        ORDER BY a.fecha DESC
                    """
                    cursor.execute(querySQL)
                else:
                    querySQL = """
                        SELECT a.id_acceso, a.cedula, a.fecha, r.nombre_rol as rol, u.nombre_usuario, u.apellido_usuario
                        FROM accesos a
                        JOIN usuarios u ON a.cedula = u.cedula
                        JOIN rol r ON u.id_rol = r.id_rol
                        WHERE a.cedula = %s
                        ORDER BY a.fecha DESC
                    """
                    cursor.execute(querySQL, (session['cedula'],))
                accesosBD = cursor.fetchall()
                return accesosBD
    except Exception as e:
        print(f"Error en la función accesosReporte: {e}")
        return None



def generarReporteExcel():
    dataAccesos = accesosReporte()
    wb = openpyxl.Workbook()
    hoja = wb.active

    # Agregar la fila de encabezado (sin ID y en orden: CÉDULA, NOMBRE, APELLIDO, ROL, FECHA)
    hoja.append(("CÉDULA", "NOMBRE", "APELLIDO", "ROL", "FECHA"))

    # Agregar los registros con el orden correcto
    for registro in dataAccesos:
        hoja.append((
            registro['cedula'],
            registro['nombre_usuario'],
            registro['apellido_usuario'],
            registro['rol'],
            registro['fecha'].strftime('%Y-%m-%d %H:%M:%S') if registro['fecha'] else ""
        ))

    # Crear nombre de archivo
    fecha_actual = datetime.now()
    archivoExcel = f"Reporte_accesos_{session.get('cedula', 'usuario')}_{fecha_actual.strftime('%Y_%m_%d')}.xlsx"
    carpeta_descarga = "../static/downloads-excel"
    ruta_descarga = os.path.join(os.path.dirname(os.path.abspath(__file__)), carpeta_descarga)

    if not os.path.exists(ruta_descarga):
        os.makedirs(ruta_descarga)
        os.chmod(ruta_descarga, 0o755)

    ruta_archivo = os.path.join(ruta_descarga, archivoExcel)
    wb.save(ruta_archivo)

    return send_file(ruta_archivo, as_attachment=True)


def buscarAreaBD(search):
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as mycursor:
                querySQL = ("""
                        SELECT 
                            a.id_area,
                            a.nombre_area
                        FROM area AS a
                        WHERE a.nombre_area LIKE %s 
                        ORDER BY a.id_area DESC
                    """)
                search_pattern = f"%{search}%"  # Agregar "%" alrededor del término de búsqueda
                mycursor.execute(querySQL, (search_pattern,))
                resultado_busqueda = mycursor.fetchall()
                return resultado_busqueda

    except Exception as e:
        print(f"Ocurrió un error en def buscarEmpleadoBD: {e}")
        return []


# Lista de Usuarios creados
def lista_usuariosBD():
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as cursor:
                querySQL = "SELECT id_usuario, cedula, nombre_usuario, apellido_usuario, id_area, id_rol FROM usuarios"
                cursor.execute(querySQL,)
                usuariosBD = cursor.fetchall()
        return usuariosBD
    except Exception as e:
        print(f"Error en lista_usuariosBD : {e}")
        return []

def lista_areasBD():
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as cursor:
                querySQL = "SELECT id_area, nombre_area FROM area"
                cursor.execute(querySQL,)
                areasBD = cursor.fetchall()
        return areasBD
    except Exception as e:
        print(f"Error en lista_areas : {e}")
        return []

# Eliminar usuario
def eliminarUsuario(id):
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as cursor:
                querySQL = "DELETE FROM usuarios WHERE id_usuario=%s"
                cursor.execute(querySQL, (id,))
                conexion_MySQLdb.commit()
                resultado_eliminar = cursor.rowcount
        return resultado_eliminar
    except Exception as e:
        print(f"Error en eliminarUsuario : {e}")
        return []    

def eliminarArea(id):
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as cursor:
                querySQL = "DELETE FROM area WHERE id_area=%s"
                cursor.execute(querySQL, (id,))
                conexion_MySQLdb.commit()
                resultado_eliminar = cursor.rowcount
        return resultado_eliminar
    except Exception as e:
        print(f"Error en eliminarArea : {e}")
        return []
    
def dataReportes():
    try:
        with connectionBD() as conexion_MYSQLdb:
            with conexion_MYSQLdb.cursor(dictionary=True) as cursor:
                querySQL = """
                    SELECT a.id_acceso, a.cedula, a.fecha, a.rol
                    FROM accesos a
                    ORDER BY a.cedula, a.fecha DESC
                """
                cursor.execute(querySQL)
                reportes = cursor.fetchall()
        return reportes
    except Exception as e:
        print(f"Error en dataReportes : {e}")
        return []
def lastAccessBD(cedula):
    try:
        with connectionBD() as conexion_MYSQLdb:
            with conexion_MYSQLdb.cursor(dictionary=True) as cursor:
                querySQL = """
                    SELECT id_acceso, cedula, fecha, rol
                    FROM accesos
                    WHERE cedula = %s
                    ORDER BY fecha DESC
                    LIMIT 1
                """
                cursor.execute(querySQL, (cedula,))
                reporte = cursor.fetchone()
                print(reporte)
        return reporte
    except Exception as e:
        print(f"Error en lastAccessBD : {e}")
        return []

##GUARDAR CLAVES GENERADAS EN AUDITORIA
def guardarClaveAuditoria(clave_audi, id):
    try:
        hora_actual = ahora_guayaquil()  # Hora de Guayaquil en formato MySQL
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as mycursor:
                sql = "INSERT INTO accesos (fecha, clave, id_usuario) VALUES (%s, %s, %s)"
                valores = (hora_actual, clave_audi, id)
                mycursor.execute(sql, valores)
                conexion_MySQLdb.commit()
                return mycursor.rowcount
                

    except Exception as e:
        return f'Se produjo un error en crear Clave: {str(e)}'
    
def lista_rolesBD():
    try:
        with connectionBD() as conexion_MYSQLdb:
            with conexion_MYSQLdb.cursor(dictionary=True) as cursor:
                querySQL = "SELECT * FROM rol"
                cursor.execute(querySQL)
                roles = cursor.fetchall()
                return roles
    except Exception as e:
        print(f"Error en select roles : {e}")
        return []
##CREAR AREA
def guardarArea(area_name):
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as mycursor:
                    sql = "INSERT INTO area (nombre_area) VALUES (%s)"
                    valores = (area_name,)
                    mycursor.execute(sql, valores)
                    conexion_MySQLdb.commit()
                    resultado_insert = mycursor.rowcount
                    return resultado_insert 
        
    except Exception as e:
        return f'Se produjo un error en crear Area: {str(e)}' 
    
##ACTUALIZAR AREA
def actualizarArea(area_id, area_name):
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as mycursor:
                sql = """UPDATE area SET nombre_area = %s WHERE id_area = %s"""
                valores = (area_name, area_id)
                mycursor.execute(sql, valores)
                conexion_MySQLdb.commit()
                resultado_update = mycursor.rowcount
                return resultado_update 
        
    except Exception as e:
        return f'Se produjo un error al actualizar el área: {str(e)}'
    
    #--------consulta de datos de los roles-----------:

    
#--------------------- metodo de graficas ----------------------
def obtenerroles():
    try:
        with connectionBD() as conexion_MYSQLdb:
            with conexion_MYSQLdb.cursor(dictionary=True) as cursor:
                query = """
                    SELECT r.nombre_rol
                    FROM rol r
                    ORDER BY r.nombre_rol ASC
                """
                cursor.execute(query)
                roles = cursor.fetchall()
        return roles
    except Exception as e:
        print(f"Error en obtenerroles: {e}")
        return []
    
#------------------------ area de graficas -----------------------


    #------------------------ entrada de accesos --------------------------
def obtener_accesos_por_fecha(fecha_inicio, fecha_fin):
    try:
        with connectionBD() as conexion_MYSQLdb:
            with conexion_MYSQLdb.cursor(dictionary=True) as cursor:
                query = """
                    SELECT clave, COUNT(id_acceso) AS cantidad
                    FROM accesos
                    WHERE fecha BETWEEN %s AND %s
                    GROUP BY clave
                    ORDER BY clave ASC
                """
                cursor.execute(query, (fecha_inicio, fecha_fin))
                accesos = cursor.fetchall()
        return accesos
    except Exception as e:
        print(f"Error en obtener_accesos_por_fecha: {e}")
        return []
    

def guardarNuevoUsuario(cedula, nombre, apellido, id_area, id_rol, password):
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor(dictionary=True) as mycursor:

                # Verificar si ya existe la cédula
                mycursor.execute("SELECT id_usuario FROM usuarios WHERE cedula = %s", (cedula,))
                existente = mycursor.fetchone()

                if existente:
                    return "duplicado"  # Indicamos que ya existe

                # Insertar nuevo usuario
                sql = """
                    INSERT INTO usuarios (cedula, nombre_usuario, apellido_usuario, id_area, id_rol, password)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                valores = (cedula, nombre, apellido, id_area, id_rol, password)
                mycursor.execute(sql, valores)
                conexion_MySQLdb.commit()

                return "ok"
    except Exception as e:
        print(f"Error en guardarUsuario: {e}")
        return "error"




#_____________________________________________________________________________________________________________________________________________________
#--------------------- metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------
def obtener_roles_con_conteo_usuarios():
    """Obtiene los roles y el número de usuarios asignados a cada rol."""
    try:
        with connectionBD() as conexion_MYSQLdb:
            with conexion_MYSQLdb.cursor(dictionary=True) as cursor:
                query = """
                    SELECT r.nombre_rol, COUNT(u.id_usuario) AS cantidad_usuarios
                    FROM rol r
                    LEFT JOIN usuarios u ON r.id_rol = u.id_rol
                    GROUP BY r.nombre_rol
                    ORDER BY r.nombre_rol ASC
                """
                cursor.execute(query)
                roles_con_conteo = cursor.fetchall()
        return roles_con_conteo
    except Exception as e:
        print(f"Error en obtener_roles_con_conteo_usuarios: {e}")
        return []

def obtener_areas_con_conteo_usuarios():
    """Obtiene las áreas y el número de usuarios asignados a cada área."""
    try:
        with connectionBD() as conexion_MYSQLdb:
            with conexion_MYSQLdb.cursor(dictionary=True) as cursor:
                # Modificado para contar usuarios asociados a cada área
                query = """
                    SELECT a.nombre_area, COUNT(u.id_usuario) AS cantidad_usuarios
                    FROM area a
                    LEFT JOIN usuarios u ON a.id_area = u.id_area
                    GROUP BY a.nombre_area
                    ORDER BY a.nombre_area ASC
                """
                cursor.execute(query)
                areas_con_conteo = cursor.fetchall()
        return areas_con_conteo
    except Exception as e:
        print(f"Error en obtener_areas_con_conteo_usuarios: {e}")
        return []

def obtener_accesos_por_rol_y_fecha(fecha_inicio, fecha_fin):
    """Obtiene el conteo de accesos por rol dentro de un rango de fechas."""
    try:
        with connectionBD() as conexion_MYSQLdb:
            with conexion_MYSQLdb.cursor(dictionary=True) as cursor:
                query = """
                    SELECT rol, COUNT(id_acceso) AS cantidad_accesos
                    FROM accesos
                    WHERE DATE(fecha) BETWEEN %s AND %s
                    GROUP BY rol
                    ORDER BY rol ASC
                """
                cursor.execute(query, (fecha_inicio, fecha_fin))
                accesos = cursor.fetchall()
        return accesos
    except Exception as e:
        print(f"Error en obtener_accesos_por_rol_y_fecha: {e}")
        return []

def obtener_fechas_sesion_usuario_con_conteo(nombre_usuario):
    """Obtiene las fechas y conteo de accesos de un usuario específico."""
    try:
        with connectionBD() as conexion_MYSQLdb:
            with conexion_MYSQLdb.cursor(dictionary=True) as cursor:
                query = """
                    SELECT DATE(a.fecha) AS fecha_corta, COUNT(a.id_acceso) AS cantidad_accesos
                    FROM accesos a
                    INNER JOIN usuarios u ON a.cedula = u.cedula -- Unimos por cédula como en tu tabla accesos
                    WHERE u.nombre_usuario = %s
                    GROUP BY DATE(a.fecha)
                    ORDER BY DATE(a.fecha) ASC
                """
                cursor.execute(query, (nombre_usuario,))
                accesos_usuario = cursor.fetchall()

        # Prepara los datos para Chart.js
        fechas = [str(acceso['fecha_corta']) for acceso in accesos_usuario] # Convertir date a string
        cantidades = [acceso['cantidad_accesos'] for acceso in accesos_usuario]
        
        return {"fechas": fechas, "cantidades": cantidades}
    except Exception as e:
        print(f"Error en obtener_fechas_sesion_usuario_con_conteo: {e}")
        return {"fechas": [], "cantidades": []}

def obtener_todos_los_nombres_usuarios():
    """Obtiene todos los nombres de usuario para poblar un select."""
    try:
        with connectionBD() as conexion_MYSQLdb:
            with conexion_MYSQLdb.cursor(dictionary=True) as cursor:
                query = "SELECT nombre_usuario FROM usuarios ORDER BY nombre_usuario ASC"
                cursor.execute(query)
                usuarios = cursor.fetchall()
        nombres = [usuario['nombre_usuario'] for usuario in usuarios]
        return nombres
    except Exception as e:
        print(f"Error en obtener_todos_los_nombres_usuarios: {e}")
        return []



























    #_____________________________________________________________________________________________________________________________________________________
#--------------------- metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------metodo de graficas ----------------------



#-**************************************************************************************************************************************************************************************
#dashboard
#****************************************************************************************************************************************************************************************
