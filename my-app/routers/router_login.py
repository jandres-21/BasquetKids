from app import app
from flask import render_template, request, flash, redirect, url_for, session, get_flashed_messages
from flask import jsonify
from controllers.funciones_home import obtenerroles
from datetime import datetime
import pytz
zona_ecuador = pytz.timezone('America/Guayaquil')

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

@app.route('/grafico_genero_datos', methods=['GET'])
def grafico_genero_datos():
    try:
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                query = """
                    SELECT
                        genero,
                        COUNT(id) AS cantidad
                    FROM jugadores
                    WHERE genero IN ('niño', 'niña')
                    GROUP BY genero
                """
                cursor.execute(query)
                results = cursor.fetchall()
        
        # Preparar datos para el gráfico
        labels = []
        values = []
        for row in results:
            labels.append(row['genero'].capitalize()) # 'Niño', 'Niña'
            values.append(row['cantidad'])
            
        return jsonify({"labels": labels, "values": values})
    except Exception as e:
        print(f"Error en grafico_genero_datos: {e}")
        return jsonify({"error": "Error al obtener datos de género"}), 500

# --- NUEVA RUTA: Para el gráfico de distribución por edades ---
@app.route('/grafico_edades_agrupadas_datos', methods=['GET'])
def grafico_edades_agrupadas_datos():
    try:
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # Agrupamos por edad para obtener el conteo de jugadores por cada edad
                query = """
                    SELECT 
                        edad, 
                        COUNT(id) as cantidad_jugadores
                    FROM jugadores
                    WHERE edad IS NOT NULL AND edad > 0
                    GROUP BY edad
                    ORDER BY edad ASC;
                """
                cursor.execute(query)
                results = cursor.fetchall()

        labels = [f"{row['edad']} años" for row in results]
        values = [row['cantidad_jugadores'] for row in results]

        return jsonify({"labels": labels, "values": values})
    except Exception as e:
        print(f"Error en grafico_edades_agrupadas_datos: {e}")
        return jsonify({"error": "Error al obtener datos de edades"}), 500















































#--------------------- metodo de graficas juegos ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------#--------------------- metodo de graficas ----------------------

# --- RUTA PRINCIPAL DE GRÁFICOS ---
# --- 1. FUNCIONES DE AYUDA (se definen primero) ---

def obtener_sesiones_de_jugador(jugador_id):
    try:
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                query = "SELECT DISTINCT nro_sesion FROM juegos WHERE jugador_id = %s ORDER BY nro_sesion ASC"
                cursor.execute(query, (jugador_id,))
                sesiones = cursor.fetchall()
        return [s['nro_sesion'] for s in sesiones]
    except Exception as e:
        print(f"Error en obtener_sesiones_de_jugador: {e}")
        return []

def obtener_datos_aros_zonas(jugador_id, nro_sesion=None):
    try:
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                query = """
                    SELECT
                        COALESCE(SUM(cantidad_aros), 0) AS total_aros,
                        COALESCE(SUM(zona_izq), 0) AS total_zona_izq,
                        COALESCE(SUM(zona_der), 0) AS total_zona_der,
                        COALESCE(SUM(zona_arr), 0) AS total_zona_arr
                    FROM juegos
                    WHERE jugador_id = %s
                """
                params = [jugador_id]
                if nro_sesion is not None and str(nro_sesion).lower() != 'todas':
                    query += " AND nro_sesion = %s"
                    params.append(nro_sesion)
                cursor.execute(query, tuple(params))
                data = cursor.fetchone()
        
        if data and (data['total_aros'] > 0 or data['total_zona_izq'] > 0 or data['total_zona_der'] > 0 or data['total_zona_arr'] > 0):
            return data
        return None 
    except Exception as e:
        print(f"Error en obtener_datos_aros_zonas: {e}")
        return None

# --- 2. RUTAS DE LA APLICACIÓN Y API ---

@app.route('/lista-de-graficas_2')
def lista_de_graficas_2():
    if 'conectado' in session:
        dataLogin = {"id": session.get("id"), "rol": session.get("rol")}
        return render_template('public/grafica/lista_graficas_2.html', dataLogin=dataLogin)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('loginCliente'))

@app.route('/obtener_jugadores_para_select', methods=['GET'])
def obtener_jugadores_para_select():
    try:
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                query = "SELECT id, nombre, apellido FROM jugadores ORDER BY nombre, apellido ASC"
                cursor.execute(query)
                jugadores = cursor.fetchall()
        
        jugadores_con_sesiones = []
        for j in jugadores:
            j_id = j['id']
            sesiones = obtener_sesiones_de_jugador(j_id)
            jugadores_con_sesiones.append({
                "id": j_id,
                "nombre_completo": f"{j['nombre']} {j['apellido']}",
                "sesiones_disponibles": sorted(list(sesiones))
            })
        return jsonify({"jugadores": jugadores_con_sesiones})
    except Exception as e:
        print(f"Error en obtener_jugadores_para_select: {e}")
        return jsonify({"error": "Error al obtener nombres de jugadores"}), 500

@app.route('/tabla_mejores_sesiones_datos', methods=['GET'])
def tabla_mejores_sesiones_datos():
    try:
        limite = request.args.get('limite', default=5, type=int)
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                query = """
                    SELECT j.id AS juego_id, j.nro_sesion, ju.nombre, ju.apellido, ju.edad,
                           DATE_FORMAT(j.fecha_inicio, '%Y-%m-%d') AS fecha_sesion,
                           DATE_FORMAT(j.fecha_inicio, '%H:%i') AS hora_sesion,
                           j.cantidad_aros, j.zona_izq, j.zona_der, j.zona_arr
                    FROM juegos j JOIN jugadores ju ON j.jugador_id = ju.id
                    ORDER BY j.cantidad_aros DESC, j.fecha_inicio DESC
                    LIMIT %s
                """
                cursor.execute(query, (limite,))
                mejores_sesiones = cursor.fetchall()
        return jsonify({"mejores_sesiones": mejores_sesiones})
    except Exception as e:
        print(f"Error en tabla_mejores_sesiones_datos: {e}")
        return jsonify({"error": "Error al obtener datos"}), 500

@app.route('/tabla_mejores_jugadores_totales_datos', methods=['GET'])
def tabla_mejores_jugadores_totales_datos():
    try:
        limite = request.args.get('limite', default=5, type=int)
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                query = """
                    SELECT j.id AS jugador_id, j.nombre, j.apellido, j.edad,
                           SUM(g.cantidad_aros) AS total_aros,
                           SUM(g.zona_izq) AS total_zona_izq,
                           SUM(g.zona_der) AS total_zona_der,
                           SUM(g.zona_arr) AS total_zona_arr
                    FROM jugadores j JOIN juegos g ON j.id = g.jugador_id
                    GROUP BY j.id, j.nombre, j.apellido, j.edad
                    ORDER BY total_aros DESC
                    LIMIT %s
                """
                cursor.execute(query, (limite,))
                mejores_jugadores = cursor.fetchall()
        return jsonify({"mejores_jugadores_totales": mejores_jugadores})
    except Exception as e:
        print(f"Error en tabla_mejores_jugadores_totales_datos: {e}")
        return jsonify({"error": "Error al obtener datos"}), 500

@app.route('/grafico_rendimiento_sesion_datos', methods=['GET'])
def grafico_rendimiento_sesion_datos():
    try:
        jugador_id = request.args.get('jugador_id', type=int)
        nro_sesion_str = request.args.get('nro_sesion')
        if not jugador_id or not nro_sesion_str:
            return jsonify({"labels": [], "values": []})

        nro_sesion = int(nro_sesion_str) if nro_sesion_str != 'Todas' else None
        data_res = obtener_datos_aros_zonas(jugador_id, nro_sesion)
        
        if data_res:
            labels = ["Aros", "Zona Izquierda", "Zona Derecha", "Zona Arriba"]
            values = [data_res['total_aros'], data_res['total_zona_izq'], data_res['total_zona_der'], data_res['total_zona_arr']]
            return jsonify({"labels": labels, "values": values})
        
        return jsonify({"labels": [], "values": []})
    except Exception as e:
        print(f"Error en grafico_rendimiento_sesion_datos: {e}")
        return jsonify({"error": "Error al obtener datos"}), 500

@app.route('/grafico_comparacion_sesiones_detallada_datos', methods=['GET'])
def grafico_comparacion_sesiones_detallada_datos():
    try:
        jugador_id1 = request.args.get('jugador_id1', type=int)
        nro_sesion1_str = request.args.get('nro_sesion1')
        jugador_id2 = request.args.get('jugador_id2', type=int)
        nro_sesion2_str = request.args.get('nro_sesion2')

        session1_num = int(nro_sesion1_str) if nro_sesion1_str and nro_sesion1_str != 'Todas' else None
        session2_num = int(nro_sesion2_str) if nro_sesion2_str and nro_sesion2_str != 'Todas' else None

        results = []
        # Llamar a la función directamente es más eficiente que hacer un request HTTP
        with app.app_context():
            all_players_data_response = obtener_jugadores_para_select()
            all_players_data = all_players_data_response.get_json().get('jugadores', [])

        if jugador_id1:
            data1 = obtener_datos_aros_zonas(jugador_id1, session1_num)
            player1_obj = next((p for p in all_players_data if p['id'] == jugador_id1), {})
            player1_name = player1_obj.get('nombre_completo', f"Jugador {jugador_id1}")
            results.append({
                "id": jugador_id1,
                "name": player1_name,
                "data": data1 if data1 else {'total_aros':0, 'total_zona_izq':0, 'total_zona_der':0, 'total_zona_arr':0}
            })

        if jugador_id2:
            data2 = obtener_datos_aros_zonas(jugador_id2, session2_num)
            player2_obj = next((p for p in all_players_data if p['id'] == jugador_id2), {})
            player2_name = player2_obj.get('nombre_completo', f"Jugador {jugador_id2}")
            results.append({
                "id": jugador_id2,
                "name": player2_name,
                "data": data2 if data2 else {'total_aros':0, 'total_zona_izq':0, 'total_zona_der':0, 'total_zona_arr':0}
            })
        
        return jsonify(results)
    except Exception as e:
        print(f"Error en grafico_comparacion_sesiones_detallada_datos: {e}")
        return jsonify({"error": "Error al obtener datos de comparación"}), 500

@app.route('/grafico_evolucion_datos', methods=['GET'])
def grafico_evolucion_datos():
    try:
        jugador_id = request.args.get('jugador_id', type=int)
        sesion_desde = request.args.get('sesion_desde', type=int)
        sesion_hasta = request.args.get('sesion_hasta', type=int)

        if not all([jugador_id, sesion_desde is not None, sesion_hasta is not None]):
            return jsonify({"error": "Faltan parámetros"}), 400
        if sesion_desde > sesion_hasta:
            return jsonify({"error": "Rango inválido", "message": "'Desde Sesión' no puede ser mayor que 'Hasta Sesión'."}), 400

        query = """
            SELECT nro_sesion, cantidad_aros, zona_izq, zona_der, zona_arr
            FROM juegos
            WHERE jugador_id = %s AND nro_sesion BETWEEN %s AND %s
            ORDER BY nro_sesion ASC
        """
        params = [jugador_id, sesion_desde, sesion_hasta]

        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()

        if len(results) < 2:
            return jsonify({"error": "insufficient_data", "message": "Se necesitan al menos 2 sesiones en el rango para mostrar la evolución."})

        labels = [f"Sesión {r['nro_sesion']}" for r in results]
        datasets = {
            "aros": [r['cantidad_aros'] for r in results],
            "zona_izq": [r['zona_izq'] for r in results],
            "zona_der": [r['zona_der'] for r in results],
            "zona_arr": [r['zona_arr'] for r in results]
        }
        return jsonify({"labels": labels, "datasets": datasets})
    except Exception as e:
        print(f"Error en grafico_evolucion_datos: {e}")
        return jsonify({"error": str(e)}), 500



































































@app.route('/lista-juegos')
def lista_juegos():
    # Los filtros del formulario se manejan principalmente en el frontend,
    # pero puedes mantener uno como el de fecha si quieres soportar filtros por URL.
    fecha = request.args.get('fecha', '')
    
    # --- CONSULTA CORREGIDA ---
    # Se usan los nombres de columna que me proporcionaste.
    query = """
        SELECT 
            j.id, 
            j.nro_sesion, 
            -- Si fecha_inicio es NULL (juegos de Node-RED), usamos fecha_fin
            IFNULL(j.fecha_inicio, j.fecha_fin) as fecha_inicio, 
            j.fecha_fin, 
            j.cantidad_aros, 
            j.zona_arr, 
            j.zona_izq, 
            j.zona_der,
            j.rendimiento,
            -- Si el nombre es NULL, mostramos 'Invitado'
            IFNULL(ju.nombre, 'Invitado') as nombre, 
            IFNULL(ju.apellido, '') as apellido
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
