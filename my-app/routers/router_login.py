from app import app
from flask import render_template, request, flash, redirect, url_for, session, get_flashed_messages
from flask import jsonify
from controllers.funciones_home import obtenerroles
from datetime import datetime
import pytz
zona_ecuador = pytz.timezone('America/Guayaquil')
from flask import request
# Función reutilizable
def ahora_guayaquil():
    return datetime.now(zona_ecuador).strftime('%Y-%m-%d %H:%M:%S')


# Importando mi conexión a BD
from conexion.conexionBD import connectionBD

# Para encriptar contraseña check_password_hash
from werkzeug.security import check_password_hash

# Importando controllers para el modulo de login
from controllers.funciones_login import *
from controllers.funciones_home import * # Asegúrate que info_perfil_session y dataLoginSesion están aquí
PATH_URL_LOGIN = "/public/login"


@app.route('/', methods=['GET'])
def inicio():
    if 'conectado' in session:
        # Asumiendo que dataLoginSesion() usa session['id_usuario'], session['name'], etc.
        # Ya que veo que guardas 'id_usuario' y 'nombre_usuario' en la sesión.
        # Asegúrate de que 'name_surname' se construye a partir de 'name' aquí si es necesario.
        return render_template('public/base_cpanel.html', dataLogin=dataLoginSesion())
    else:
        # Renderiza el template de login principal (dónde está tu formulario re-diseñado)
        return render_template(f'{PATH_URL_LOGIN}/base_login.html') # Asumo que base_login.html ES tu login.



# Validar sesión - RUTA DE LOGIN CORREGIDA
@app.route('/login', methods=['GET', 'POST'])
def loginCliente():
    # 1. Si el usuario ya está conectado, redirigir a la página de inicio
    if 'conectado' in session:
        return redirect(url_for('inicio')) # Va a 'inicio' que ya sabe qué mostrar si está conectado

    # 2. Manejar la solicitud POST cuando el formulario de inicio de sesión es enviado
    if request.method == 'POST':
        # Asegúrate que los nombres de los campos coincidan con tu HTML (cedula, password)
        cedula = request.form.get('cedula', '').strip() # .get para evitar errores si no existe, .strip() para limpiar espacios
        pass_user = request.form.get('password', '').strip() # Cambiado de 'pass_user' a 'password' según tu último HTML

        # Validación básica de campos vacíos
        if not cedula or not pass_user:
            flash('Por favor, ingresa tu cédula y contraseña.', 'error')
            return redirect(url_for('loginCliente')) # PRG: Redirige al GET de la misma página

        conexion_MySQLdb = connectionBD()
        if not conexion_MySQLdb: # Manejo de error si la conexión falla
            flash('Error de conexión a la base de datos.', 'error')
            return redirect(url_for('loginCliente'))

        try:
            cursor = conexion_MySQLdb.cursor(dictionary=True)
            cursor.execute("SELECT id_usuario, nombre_usuario, cedula, password, id_rol FROM usuarios WHERE cedula = %s", [cedula])
            account = cursor.fetchone()
            fecha_actual = ahora_guayaquil()
            

            if account:
                # Verifica la contraseña hasheada
                # Asegúrate de que 'password' en account['password'] es el hash REAL de la BD
                # y que pass_user es la contraseña en texto plano ingresada por el usuario.
                # Tu HTML usa 'password' para el campo.
                if check_password_hash(account['password'], pass_user):
                    # Crear datos de sesión
                    session['conectado'] = True
                    session['id'] = account['id_usuario']
                    session['name'] = account['nombre_usuario'] # Asegúrate que este nombre es para dataLoginSesion
                    session['cedula'] = account['cedula']
                    session['rol'] = account['id_rol']
                    # REGISTRO DE ACCESO
                    sql_insert_acceso = "INSERT INTO accesos (fecha, cedula, rol) VALUES (%s, %s, %s)"
                    cursor.execute(sql_insert_acceso, (fecha_actual, account['cedula'], 'admin' if account['id_rol'] == 1 else 'user'))

                    conexion_MySQLdb.commit()
                    flash('La sesión fue iniciada correctamente.', 'success')
                    return redirect(url_for('inicio')) # Redirige a donde debe ir el usuario logueado
                else:
                    flash('Contraseña incorrecta. Por favor, intente de nuevo.', 'error')
                    return redirect(url_for('loginCliente')) # PRG: Redirige al GET de la misma página
            else:
                flash('Usuario no encontrado. Por favor, verifique su cédula.', 'error')
                return redirect(url_for('loginCliente')) # PRG: Redirige al GET de la misma página
            cursor.close()
        except Exception as e:
            # Captura cualquier error de base de datos o inesperado
            print(f"Error durante el login: {e}")
            flash('Ocurrió un error inesperado. Por favor, intente de nuevo más tarde.', 'error')
            return redirect(url_for('loginCliente'))
        finally:
            # Asegura que la conexión a la base de datos se cierre
            if conexion_MySQLdb:
                conexion_MySQLdb.close()

    # 3. Manejar la solicitud GET o si el método POST no cumple las condiciones iniciales (campos vacíos).
    # Este bloque solo renderiza el formulario de inicio de sesión.
    # Los mensajes flash aparecerán aquí si fueron establecidos por una redirección previa.
    return render_template(f'{PATH_URL_LOGIN}/base_login.html')


@app.route('/closed-session', methods=['GET'])
def cerraSesion():
    if request.method == 'GET':
        if 'conectado' in session:
            session.pop('conectado', None)
            session.pop('id', None)
            # Asegúrate de vaciar todas las sesiones que estableciste
            session.pop('name', None) # Agregado 'name'
            session.pop('cedula', None) # Agregado 'cedula'
            session.pop('rol', None) # Agregado 'rol'
            flash('Tu sesión fue cerrada correctamente.', 'success')
            return redirect(url_for('inicio'))
        else:
            flash('Recuerda que debes iniciar sesión.', 'error') # Corregido para mejor gramática
            return render_template(f'{PATH_URL_LOGIN}/base_login.html')



    #------------------------ acesso de datos por usuario---------------------



#---------------------------------------------------------------------
@app.route('/mi-perfil/<int:id>', methods=['GET', 'POST'], endpoint='perfil')
def perfil(id):
    # Verifico que esté logueado
    if 'conectado' not in session:
        flash('Por favor, inicie sesión nuevamente para continuar.', 'error')
        return redirect(url_for('inicio'))

    if request.method == 'POST':
        cedula    = request.form.get('cedula')          # cédula del usuario que se edita
        nombre    = request.form.get('nombre_usuario')
        apellido  = request.form.get('apellido_usuario')
        id_area   = request.form.get('id_area')
        id_rol    = request.form.get('id_rol')
        pass_user = request.form.get('pass_user')

        # Preparar hash de contraseña si la cambió
        password_hash = None
        if pass_user and pass_user.strip():
            password_hash = generate_password_hash(pass_user.strip())

        # Intento de actualización
        resultado = actualizarUsuario(
            id_usuario=id,
            cedula=cedula,
            nombre=nombre,
            apellido=apellido,
            id_area=id_area,
            id_rol=id_rol,
            password=password_hash
        )

        if resultado:
            flash('Perfil actualizado correctamente.', 'success')

            # Solo cierro la sesión si la cédula editada coincide con la de quien está logueado
            if session.get('cedula') == cedula:
                # Capturamos el flash actual
                flashes = get_flashed_messages(with_categories=True)
                # Limpio la sesión completa
                session.clear()
                # Reinyecto únicamente los flashes para mostrarlos en JS
                session['_flashes'] = flashes
            else:
    # Si es otro usuario el que se actualiza, redirigir al menú de usuarios
                flash('Usuario actualizado correctamente.', 'success')
                return redirect(url_for('usuarios'))

        else:
            flash('Error al actualizar el perfil.', 'error')

        return redirect(url_for('perfil', id=id))

    # GET: muestro el formulario
    usuario = obtenerUsuarioPorId(id)
    if not usuario:
        flash('Usuario no encontrado.', 'error')
        return redirect(url_for('inicio'))

    areas = obtener_areas()
    roles = obtener_roles()

    return render_template(
        'public/login/actualizar_perfil.html',
        usuario=usuario,
        areas=areas,
        roles=roles,
        dataLogin=session
    )


def actualizarUsuario(id_usuario, cedula, nombre, apellido, id_area, id_rol, password=None):
    try:
        with connectionBD() as conexion_MySQLdb:
            with conexion_MySQLdb.cursor() as cursor:
                if password:
                    sql = """
                        UPDATE usuarios 
                        SET cedula=%s, nombre_usuario=%s, apellido_usuario=%s, id_area=%s, id_rol=%s, password=%s
                        WHERE id_usuario=%s
                    """
                    params = (cedula, nombre, apellido, id_area, id_rol, password, id_usuario)
                else:
                    sql = """
                        UPDATE usuarios 
                        SET cedula=%s, nombre_usuario=%s, apellido_usuario=%s, id_area=%s, id_rol=%s
                        WHERE id_usuario=%s
                    """
                    params = (cedula, nombre, apellido, id_area, id_rol, id_usuario)

                cursor.execute(sql, params)
                conexion_MySQLdb.commit()
                return cursor.rowcount > 0
    except Exception as e:
        print(f"Error en actualizarUsuario: {e}")
        return False




#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------
@app.route('/lista-de-graficas')
def lista_de_graficas():
    if 'conectado' in session:
        dataLogin = {
            "id": session.get("id"),
            "rol": session.get("rol"),
        }
        return render_template('public/grafica/lista_graficas.html', dataLogin=dataLogin)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('loginCliente'))

# --- Rutas para la API de datos de gráficos ---

@app.route('/grafica_roles_datos', methods=['GET'])
def grafica_roles_datos():
    try:
        roles_con_conteo = obtener_roles_con_conteo_usuarios()
        nombres = [rol['nombre_rol'] for rol in roles_con_conteo]
        cantidades = [rol['cantidad_usuarios'] for rol in roles_con_conteo]
        return jsonify({"nombres": nombres, "cantidades": cantidades})
    except Exception as e:
        print(f"Error en grafica_roles_datos: {e}")
        return jsonify({"error": "Error al obtener los datos de roles"}), 500

@app.route('/grafica_areas_datos', methods=['GET'])
def grafica_areas_datos():
    try:
        areas_con_conteo = obtener_areas_con_conteo_usuarios()
        nombres = [area['nombre_area'] for area in areas_con_conteo]
        cantidades = [area['cantidad_usuarios'] for area in areas_con_conteo]
        return jsonify({"nombres": nombres, "cantidades": cantidades})
    except Exception as e:
        print(f"Error en grafica_areas_datos: {e}")
        return jsonify({"error": "Error al obtener los datos de áreas"}), 500

@app.route('/grafica_accesos_datos', methods=['GET'])
def grafica_accesos_datos():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')

        if not fecha_inicio or not fecha_fin:
            return jsonify({"error": "Debe proporcionar las fechas de inicio y fin"}), 400

        accesos_por_rol = obtener_accesos_por_rol_y_fecha(fecha_inicio, fecha_fin)
        
        # Prepara los datos para el frontend
        roles = [acceso['rol'] for acceso in accesos_por_rol]
        cantidades = [acceso['cantidad_accesos'] for acceso in accesos_por_rol]

        return jsonify({"roles": roles, "cantidades": cantidades})
    except Exception as e:
        print(f"Error en grafica_accesos_datos: {e}")
        return jsonify({"error": "Error al obtener los datos de accesos"}), 500

@app.route('/obtener_nombres_usuarios', methods=['GET'])
def obtener_nombres_usuarios():
    try:
        nombres = obtener_todos_los_nombres_usuarios()
        return jsonify({"nombres": nombres})
    except Exception as e:
        print(f"Error en obtener_nombres_usuarios: {e}")
        return jsonify({"error": "Error al obtener los nombres de los usuarios"}), 500
    
@app.route('/grafica_fechas_usuario_datos', methods=['GET'])
def grafica_fechas_usuario_datos():
    try:
        nombre_usuario = request.args.get('nombre_usuario')

        if not nombre_usuario:
            return jsonify({"error": "Debe proporcionar el nombre del usuario"}), 400

        datos_grafico = obtener_fechas_sesion_usuario_con_conteo(nombre_usuario)
        
        return jsonify(datos_grafico) # Este ya devuelve {"fechas": [], "cantidades": []}
    except Exception as e:
        print(f"Error en grafica_fechas_usuario_datos: {e}")
        return jsonify({"error": "Error al obtener los datos de accesos por usuario"}), 500


@app.route('/test_roles')
def test_roles():
    return jsonify(obtener_roles_con_conteo_usuarios())









@app.before_request
def always_desktop():
    user_agent = request.headers.get('User-Agent', '').lower()
    if 'mobile' in user_agent:
        # Aquí podrías activar alguna variable global si necesitas
        # mostrar un aviso o cambiar alguna plantilla.
        pass








































#--------------------- metodo de graficas juegos ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------

def obtener_sesiones_de_jugador(jugador_id):
    """
    Obtiene el número de sesión y la fecha de inicio para un jugador dado.
    """
    conn = connectionBD() # Asume que connectionBD() está disponible y devuelve una conexión
    sesiones = []
    if conn:
        try:
            with conn.cursor(dictionary=True) as cursor:
                # Ordenar por nro_sesion para que las sesiones aparezcan en orden lógico
                # Asegura que nro_sesion sea único por la combinación jugador_id y nro_sesion,
                # tomando la fecha mínima (o máxima, dependiendo de preferencia) para esa sesión.
                query = """
                    SELECT 
                        nro_sesion, 
                        DATE_FORMAT(MIN(fecha_inicio), '%Y-%m-%d') as fecha 
                    FROM juegos 
                    WHERE jugador_id = %s 
                    GROUP BY nro_sesion 
                    ORDER BY nro_sesion ASC
                """
                cursor.execute(query, (jugador_id,))
                sesiones = cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener sesiones para jugador {jugador_id}: {e}")
        finally:
            conn.close()
    return sesiones

def obtener_datos_aros_zonas(jugador_id, nro_sesion):
    """
    Obtiene el total de aros y toques por zona para una sesión específica o todas.
    """
    conn = connectionBD() # Asume que connectionBD() está disponible
    
    data = {
        "total_aros": 0,
        "total_zona_izq": 0,
        "total_zona_der": 0,
        "total_zona_arr": 0
    }

    if conn:
        try:
            with conn.cursor(dictionary=True) as cursor:
                if nro_sesion == 'todas': # Caso para el total acumulado
                    query = """
                        SELECT 
                            SUM(cantidad_aros) AS total_aros, 
                            SUM(zona_izq) AS total_zona_izq, 
                            SUM(zona_der) AS total_zona_der, 
                            SUM(zona_arr) AS total_zona_arr
                        FROM juegos 
                        WHERE jugador_id = %s
                    """
                    cursor.execute(query, (jugador_id,))
                else: # Caso para una sesión específica, convertir nro_sesion a INT
                    try:
                        nro_sesion_int = int(nro_sesion) # Convertir a int si es un número de sesión
                    except ValueError:
                        print(f"DEBUG: nro_sesion '{nro_sesion}' no es un entero válido para la consulta específica.")
                        return data # Devuelve datos vacíos si no es un número válido

                    query = """
                        SELECT 
                            SUM(cantidad_aros) AS total_aros, 
                            SUM(zona_izq) AS total_zona_izq, 
                            SUM(zona_der) AS total_zona_der, 
                            SUM(zona_arr) AS total_zona_arr
                        FROM juegos 
                        WHERE jugador_id = %s AND nro_sesion = %s
                    """
                    cursor.execute(query, (jugador_id, nro_sesion_int)) # Usar la versión int
                
                result = cursor.fetchone()
                if result:
                    # Usar .get() con valor por defecto para manejar posibles None si no hay datos.
                    # El 'or 0' adicional es para asegurar que sean números y no None si el SUM devuelve None.
                    data["total_aros"] = result.get("total_aros", 0) or 0
                    data["total_zona_izq"] = result.get("total_zona_izq", 0) or 0
                    data["total_zona_der"] = result.get("total_zona_der", 0) or 0
                    data["total_zona_arr"] = result.get("total_zona_arr", 0) or 0
        except Exception as e:
            print(f"Error al obtener datos de aros/zonas para jugador {jugador_id}, sesion {nro_sesion}: {e}")
        finally:
            conn.close()
    return data


# =======================================================================
# RUTA PRINCIPAL PARA RENDERIZAR LA PÁGINA DEL PANEL
# =======================================================================

@app.route('/lista-de-graficas_2') # Mantengo esta ruta como pediste
def lista_de_graficas_2(): # Y el nombre de la función consistente
    if 'conectado' in session:
        dataLogin = {
            "id": session.get("id"),
            "nombre": session.get("nombre", "Usuario"),
            "rol": session.get("rol")
        }
        return render_template('public/grafica/lista_graficas_2.html', dataLogin=dataLogin)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('loginCliente'))


# =======================================================================
# RUTAS DE LA API (Endpoints para que el JavaScript obtenga los datos)
# =======================================================================

# --- RUTA PARA POBLAR LOS SELECTORES DE JUGADORES ---
@app.route('/obtener_jugadores_para_select', methods=['GET'])
def obtener_jugadores_para_select():
    conn = connectionBD()
    if conn:
      with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id, nombre, apellido FROM jugadores ORDER BY nombre, apellido ASC")
            jugadores = cursor.fetchall()
            # Para cada jugador, obtenemos también sus sesiones asociadas usando el helper
            data_jugadores = []
            for j in jugadores:
                jugador_id = j['id']
                sesiones_del_jugador = obtener_sesiones_de_jugador(jugador_id)
                data_jugadores.append({
                    "id": jugador_id, 
                    "nombre_completo": f"{j['nombre']} {j['apellido']}", 
                    "sesiones": sesiones_del_jugador
                })
            conn.close()
            return jsonify({"jugadores": data_jugadores})
    return jsonify({"jugadores": []})


# --- RUTAS PARA LAS TABLAS ---
@app.route('/tabla_mejores_sesiones_datos', methods=['GET'])
def tabla_mejores_sesiones_datos():
    conn = connectionBD()
    if conn:
        with conn.cursor(dictionary=True) as cursor:
            query = "SELECT j.nro_sesion, ju.nombre, ju.apellido, j.cantidad_aros, j.zona_izq, j.zona_der, j.zona_arr, DATE_FORMAT(j.fecha_inicio, '%Y-%m-%d') AS fecha FROM juegos j JOIN jugadores ju ON j.jugador_id=ju.id ORDER BY j.cantidad_aros DESC LIMIT 5"
            cursor.execute(query)
            data = cursor.fetchall()
            conn.close()
            return jsonify({"mejores_sesiones": data})
    return jsonify({"mejores_sesiones": []})


@app.route('/tabla_mejores_jugadores_totales_datos', methods=['GET'])
def tabla_mejores_jugadores_totales_datos():
    conn = connectionBD()
    if conn:
        with conn.cursor(dictionary=True) as cursor:
            query = "SELECT j.nombre, j.apellido, j.edad, SUM(g.cantidad_aros) AS total_aros, SUM(g.zona_izq) AS total_zona_izq, SUM(g.zona_der) AS total_zona_der, SUM(g.zona_arr) AS total_zona_arr FROM jugadores j JOIN juegos g ON j.id=g.jugador_id GROUP BY j.id, j.nombre, j.apellido, j.edad ORDER BY total_aros DESC LIMIT 5"
            cursor.execute(query)
            data = cursor.fetchall()
            conn.close()
            return jsonify({"mejores_jugadores": data})
    return jsonify({"mejores_jugadores": []})


# --- RUTAS PARA GRÁFICOS ESTÁTICOS ---
@app.route('/grafico_genero_datos', methods=['GET'])
def grafico_genero_datos():
    conn = connectionBD()
    if conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT genero, COUNT(id) as total FROM jugadores GROUP BY genero")
            data = cursor.fetchall()
            conn.close()
            return jsonify({"labels": [d['genero'] or 'N/E' for d in data], "values": [d['total'] for d in data]})
    return jsonify({"labels": [], "values": []})


@app.route('/grafico_edades_agrupadas_datos', methods=['GET'])
def grafico_edades_agrupadas_datos():
    conn = connectionBD()
    if conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT edad, COUNT(id) AS total FROM jugadores WHERE edad > 0 GROUP BY edad ORDER BY edad")
            data = cursor.fetchall()
            conn.close()
            return jsonify({"labels": [f"{d['edad']} años" for d in data], "values": [d['total'] for d in data]})
    return jsonify({"labels": [], "values": []})


@app.route('/grafico_distribucion_rendimiento_datos', methods=['GET'])
def grafico_distribucion_rendimiento_datos():
    conn = connectionBD()
    if conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT rendimiento, COUNT(id) AS total FROM juegos WHERE rendimiento IS NOT NULL AND rendimiento != '' GROUP BY rendimiento")
            data = cursor.fetchall()
            conn.close()
            return jsonify({"labels": [d['rendimiento'] for d in data], "values": [d['total'] for d in data]})
    return jsonify({"labels": [], "values": []})


# --- RUTAS PARA GRÁFICOS INTERACTIVOS ---
@app.route('/grafico_rendimiento_sesion_datos', methods=['GET'])
def grafico_rendimiento_sesion_datos():
    jugador_id = request.args.get('jugador_id', type=int) # Convertir a int
    nro_sesion = request.args.get('nro_sesion') # 'todas' o un número (string)
    
    if not jugador_id: 
        return jsonify({"error": "Falta el ID del jugador"}), 400
    
    # Aquí se usa la función helper
    data_res = obtener_datos_aros_zonas(jugador_id, nro_sesion)
    
    if data_res and any(data_res[key] > 0 for key in data_res): # Verificar si hay algún valor mayor a 0
        return jsonify({
            "labels": ["Aros", "Z. Izq", "Z. Der", "Z. Arr"], 
            "values": [
                int(data_res['total_aros']), 
                int(data_res['total_zona_izq']), 
                int(data_res['total_zona_der']), 
                int(data_res['total_zona_arr'])
            ]
        })
    return jsonify({"labels": [], "values": [], "error": "No hay datos para la sesión/jugador seleccionados."}), 404


@app.route('/grafico_evolucion_datos', methods=['GET'])
def grafico_evolucion_datos():
    jugador_id = request.args.get('jugador_id', type=int)
    desde = request.args.get('sesion_desde', type=int)
    hasta = request.args.get('sesion_hasta', type=int)

    if not all([jugador_id, desde, hasta]): 
        return jsonify({"error": "Faltan parámetros jugador_id, sesion_desde o sesion_hasta."}), 400
    
    if desde > hasta:
        return jsonify({"error": "'Desde' no puede ser mayor que 'Hasta'."}), 400

    conn = connectionBD()
    if conn:
        with conn.cursor(dictionary=True) as cursor:
            query = """
                SELECT 
                    nro_sesion, 
                    DATE_FORMAT(MIN(fecha_inicio), '%Y-%m-%d') as fecha,
                    SUM(cantidad_aros) as cantidad_aros, 
                    SUM(zona_izq) as zona_izq, 
                    SUM(zona_der) as zona_der, 
                    SUM(zona_arr) as zona_arr
                FROM juegos 
                WHERE 
                    jugador_id = %s AND nro_sesion BETWEEN %s AND %s 
                GROUP BY nro_sesion
                ORDER BY nro_sesion ASC
            """
            cursor.execute(query, (jugador_id, desde, hasta))
            results = cursor.fetchall()
            conn.close()

            if not results: 
                return jsonify({"error": "No hay datos para el rango de sesiones seleccionado."})
            
            return jsonify({
                "labels": [f"S.{r['nro_sesion']} ({r['fecha']})" for r in results], 
                "datasets": {
                    "aros": [int(r['cantidad_aros']) for r in results],
                    "izq": [int(r['zona_izq']) for r in results], 
                    "der": [int(r['zona_der']) for r in results], 
                    "arr": [int(r['zona_arr']) for r in results]
                }
            })
    return jsonify({"error": "Error de conexión a la base de datos."}), 500














@app.route('/lista-juegos')
def lista_juegos():
    # Los filtros del formulario se manejan principalmente en el frontend,
    # pero puedes mantener uno como el de fecha si quieres soportar filtros por URL.
    fecha = request.args.get('fecha', '')
    
    # --- CONSULTA CORREGIDA ---
    # Se usan los nombres de columna que me proporcionaste.
    query = """
        SELECT 
            j.id, j.nro_sesion, j.fecha_inicio, j.fecha_fin, 
            j.cantidad_aros, j.zona_arr, j.zona_izq, j.zona_der,
            j.rendimiento,  -- Añadido para mostrar en la tabla
            ju.nombre, ju.apellido
        FROM juegos j
        LEFT JOIN jugadores ju ON j.jugador_id = ju.id
        WHERE 1=1
    """
    params = []

    if fecha:
        query += " AND DATE(j.fecha_inicio) = %s"
        params.append(fecha)

    query += " ORDER BY j.fecha_inicio DESC"

    try:
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
                juegos = cursor.fetchall()
                
        return render_template('public/juegos/lista_juegos.html', juegos=juegos, dataLogin=session)
    except Exception as e:
        print(f"Error al obtener lista de juegos: {e}")
        flash("Error al cargar la lista de sesiones.", "error")
        return render_template('public/juegos/lista_juegos.html', juegos=[], dataLogin=session)

# --- RUTA DE API CORREGIDA ---
# Se usan los nombres de columna que me proporcionaste.
@app.route('/get-session-details/<int:session_id>')
def get_session_details(session_id):
    if 'id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401

    query = """
        SELECT
            j.id, j.nro_sesion, j.fecha_inicio, j.fecha_fin, 
            j.cantidad_aros, j.zona_arr, j.zona_izq, j.zona_der,
            j.duracion, j.rendimiento, j.diagnostico,
            ju.nombre, ju.apellido, ju.edad, ju.genero
        FROM juegos j
        LEFT JOIN jugadores ju ON j.jugador_id = ju.id
        WHERE j.id = %s
    """
    try:
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, (session_id,))
                session_data = cursor.fetchone()

        if not session_data:
            return jsonify({'success': False, 'error': 'Sesión no encontrada'}), 404

        # Convertir objetos datetime a strings en formato ISO para que JS los pueda leer
        if session_data.get('fecha_inicio'):
            session_data['fecha_inicio'] = session_data['fecha_inicio'].isoformat()
        if session_data.get('fecha_fin'):
            session_data['fecha_fin'] = session_data['fecha_fin'].isoformat()
            
        return jsonify({'success': True, 'data': session_data})
    except Exception as e:
        print(f"Error al obtener detalles de la sesión {session_id}: {e}")
        return jsonify({'success': False, 'error': 'Error en la base de datos'}), 500


@app.route('/borrar-juego/<int:id>', methods=['GET'])
def borrar_juego(id):
    try:
        with connectionBD() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM juegos WHERE id = %s", (id,))
                conn.commit()
        flash("Sesión eliminada correctamente.", "success")
    except Exception as e:
        print(f"Error al eliminar juego: {e}")
        flash("Error al eliminar la sesión.", "error")
    return redirect(url_for('lista_juegos'))
