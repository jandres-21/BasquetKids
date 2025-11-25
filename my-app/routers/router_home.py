from controllers.funciones_login import *
from app import app
from flask import render_template, request, flash, redirect, url_for, session,  jsonify
from mysql.connector.errors import Error
from datetime import datetime
from uuid import uuid4
import pytz
import uuid
import socketio
import socketio
from flask_socketio import socketio, emit
zona_ecuador = pytz.timezone('America/Guayaquil')

# Función reutilizable
def ahora_guayaquil():
    return datetime.now(zona_ecuador).strftime('%Y-%m-%d %H:%M:%S')

# Importando cenexión a BD
from controllers.funciones_home import *

@app.route('/lista-de-areas', methods=['GET'])
def lista_areas():
    if 'conectado' in session:
        return render_template('public/usuarios/lista_areas.html', areas=lista_areasBD(), dataLogin=dataLoginSesion())
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))

@app.route("/lista-de-usuarios", methods=['GET'])
def usuarios():
    if 'conectado' in session:
        return render_template('public/usuarios/lista_usuarios.html',  resp_usuariosBD=lista_usuariosBD(), dataLogin=dataLoginSesion(), areas=lista_areasBD(), roles = lista_rolesBD())
    else:
        return redirect(url_for('inicioCpanel'))

#Ruta especificada para eliminar un usuario
@app.route('/borrar-usuario/<string:id>', methods=['GET'])
def borrarUsuario(id):
    resp = eliminarUsuario(id)
    if resp:
        flash('El Usuario fue eliminado correctamente', 'success')
        return redirect(url_for('usuarios'))
    
    
@app.route('/borrar-area/<string:id_area>/', methods=['GET'])
def borrarArea(id_area):
    resp = eliminarArea(id_area)
    if resp:
        flash('El Empleado fue eliminado correctamente', 'success')
        return redirect(url_for('lista_areas'))
    else:
        flash('Hay usuarios que pertenecen a esta área', 'error')
        return redirect(url_for('lista_areas'))


@app.route("/descargar-informe-accesos/", methods=['GET'])
def reporteBD():
    if 'conectado' in session:
        return generarReporteExcel()
    else:
        flash('primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))
    
@app.route("/reporte-accesos", methods=['GET'])
def reporteAccesos():
    if 'conectado' in session:
        userData = dataLoginSesion()  # info de sesión
        reportes = accesosReporte() or []

        # Obtener el último acceso para mostrar en la parte superior (fecha, nombre, apellido)
        lastAccess = reportes[0] if len(reportes) > 0 else None

        return render_template('public/perfil/reportes.html', 
                               reportes=reportes,
                               lastAccess=lastAccess,
                               dataLogin=userData)
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


#CREAR AREA
@app.route('/crear-area', methods=['GET','POST'])
def crearArea():
    if request.method == 'POST':
        area_name = request.form['nombre_area']  # Asumiendo que 'nombre_area' es el nombre del campo en el formulario
        resultado_insert = guardarArea(area_name)
        if resultado_insert:
            # Éxito al guardar el área
            flash('El Area fue creada correctamente', 'success')
            return redirect(url_for('lista_areas'))
            
        else:
            # Manejar error al guardar el área
            return "Hubo un error al guardar el área."
    return render_template('public/usuarios/lista_areas')

##ACTUALIZAR AREA
@app.route('/actualizar-area', methods=['POST'])
def updateArea():
    if request.method == 'POST':
        nombre_area = request.form['nombre_area']  # Asumiendo que 'nuevo_nombre' es el nombre del campo en el formulario
        id_area = request.form['id_area']
        resultado_update = actualizarArea(id_area, nombre_area)
        if resultado_update:
           # Éxito al actualizar el área
            flash('El actualizar fue creada correctamente', 'success')
            return redirect(url_for('lista_areas'))
        else:
            # Manejar error al actualizar el área
            return "Hubo un error al actualizar el área."

    return redirect(url_for('lista_areas'))
#registrar usuario 
@app.route('/register-user', methods=['GET'])
def cpanelRegisterUser():
    if 'conectado' in session:
        return render_template(
            'public/login/auth_register.html', 
            roles=lista_rolesBD(), 
            areas=lista_areasBD(), 
            dataLogin=dataLoginSesion()
        )
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))




#registrar usuario
@app.route('/register-user', methods=['POST'])
def cpanelRegisterUserBD():
    if 'conectado' in session:
        cedula = request.form['cedula']
        nombre = request.form['name']
        apellido = request.form['surname']
        id_area = request.form['selectArea']
        id_rol = request.form['selectRol']
        pass_user = request.form['pass_user']

        resultado = recibeInsertRegisterUser(cedula, nombre, apellido, id_area, id_rol, pass_user)

        if resultado == "duplicado":
            flash('❌ Error: El usuario con esta cédula ya está registrado.', 'error')
        elif resultado == "ok":
            flash('✅ Usuario registrado exitosamente.', 'success')
        elif resultado == "invalid_data":
            flash('❌ Datos inválidos. Por favor verifica el formulario.', 'error')
        else:
            flash('❌ Error al registrar el usuario.', 'error')

        return redirect(url_for('usuarios'))
    else:
        flash('Primero debes iniciar sesión.', 'error')
        return redirect(url_for('inicio'))


@app.route('/lista-de-ninos')
def lista_de_ninos():
    try:
        # Abre la conexión con un bloque 'with' (autocierre)
        with connectionBD() as conn:
            # Crea un cursor con dictionary=True para acceder por nombre de columna
            with conn.cursor(dictionary=True) as cursor:
                # Incluye 'genero' en la consulta SELECT
                cursor.execute("SELECT id, nombre, apellido, edad, genero FROM jugadores ORDER BY id ASC")
                lista_ninos = cursor.fetchall()
        return render_template('public/usuarios/lista_niños.html', lista_ninos=lista_ninos, dataLogin=session)
    except Exception as e:
        print(f"Error al obtener lista de niños: {e}")
        flash("Error al cargar la lista de niños.", "error")
        return render_template('public/usuarios/lista_niños.html', lista_ninos=[], dataLogin=session)


@app.route('/registrar-nino', methods=['GET', 'POST'])
def registrar_nino():
    if request.method == 'POST':
        nombre = request.form.get('nombre').strip()
        apellido = request.form.get('apellido').strip()
        edad = request.form.get('edad').strip()
        genero = request.form.get('genero').strip()

        # Validación general
        if not nombre or not apellido or not edad or not genero:
            flash("Todos los campos (nombre, apellido, edad, género) son obligatorios.", "error")
            return redirect(url_for('registrar_nino'))
        
        # Validar género
        if genero not in ['niño', 'niña']:
            flash("Valor de género inválido. Selecciona 'Niño' o 'Niña'.", "error")
            return redirect(url_for('registrar_nino'))

        # Generar UUID obligatorio
        nuevo_uuid = str(uuid4())

        try:
            with connectionBD() as conn:
                with conn.cursor(dictionary=True) as cursor:

                    # Contar cuántos niños existen con ese nombre y apellido base
                    cursor.execute("""
                        SELECT COUNT(*) AS total
                        FROM jugadores
                        WHERE nombre = %s AND apellido REGEXP %s
                    """, (
                        nombre,
                        f'^{apellido}(0[0-9]|[1-9][0-9])?$'
                    ))

                    resultado = cursor.fetchone()
                    total = resultado['total']

                    # Si existen, agregar sufijo
                    if total > 0:
                        sufijo = f"{total:02}"
                        apellido = f"{apellido}{sufijo}"

                    # Insertar niño incluyendo UUID
                    cursor.execute("""
                        INSERT INTO jugadores (nombre, apellido, edad, genero, uuid)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (nombre, apellido, edad, genero, nuevo_uuid))

                    conn.commit()

            flash(f"Niño/a {nombre} {apellido} registrado/a correctamente.", "success")
            return redirect(url_for('lista_de_ninos'))

        except Exception as e:
            print(f"Error al registrar niño: {e}")
            flash("Error al registrar niño.", "error")
            return redirect(url_for('registrar_nino'))

    return render_template('public/usuarios/registrar_nino.html', dataLogin=session)


@app.route('/editar-nino/<string:id>', methods=['GET', 'POST'])
def editar_nino(id):
    try:
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                if request.method == 'POST':
                    nombre = request.form.get('nombre').strip()
                    apellido = request.form.get('apellido').strip()
                    edad = request.form.get('edad').strip()
                    genero = request.form.get('genero').strip() # <--- NUEVO: Obtener el género

                    if not nombre or not apellido or not edad or not genero: # <--- NUEVO: Validar género
                        flash("Todos los campos son obligatorios.", "error")
                        return redirect(url_for('editar_nino', id=id))

                    if genero not in ['niño', 'niña']: # <--- NUEVO: Validar valor del género
                        flash("Valor de género inválido. Selecciona 'Niño' o 'Niña'.", "error")
                        return redirect(url_for('editar_nino', id=id))

                    # Obtener datos actuales para comparar
                    # <--- NUEVO: Seleccionar 'genero' también para comparaciones
                    cursor.execute("SELECT nombre, apellido, genero FROM jugadores WHERE id = %s", (id,))
                    actual = cursor.fetchone()
                    if not actual:
                        flash("Niño no encontrado.", "error")
                        return redirect(url_for('lista_de_ninos'))

                    nombre_actual = actual['nombre']
                    apellido_actual = actual['apellido']
                    # genero_actual = actual['genero'] # Podrías compararlo si lo necesitas

                    # Solo aplicar la lógica de sufijo si se cambió el nombre o el apellido
                    if nombre != nombre_actual or apellido != apellido_actual:
                        cursor.execute("""
                            SELECT COUNT(*) AS total
                            FROM jugadores
                            WHERE nombre = %s AND apellido REGEXP %s AND id != %s
                        """, (
                            nombre,
                            f'^{apellido}(0[0-9]|[1-9][0-9])?$',
                            id
                        ))
                        resultado = cursor.fetchone()
                        total = resultado['total']

                        if total > 0:
                            sufijo = f"{total:02}"
                            apellido = f"{apellido}{sufijo}"

                    # Actualizar niño - <--- NUEVO: Incluir 'genero' en la sentencia UPDATE
                    sql_update = "UPDATE jugadores SET nombre = %s, apellido = %s, edad = %s, genero = %s WHERE id = %s"
                    cursor.execute(sql_update, (nombre, apellido, edad, genero, id)) # <--- NUEVO: Pasar el valor de 'genero'
                    conn.commit()

                    flash(f"Niño/a {nombre} {apellido} actualizado/a correctamente.", "success")
                    return redirect(url_for('lista_de_ninos'))

                else:
                    # <--- NUEVO: Seleccionar 'genero' para mostrarlo en el formulario GET
                    cursor.execute("SELECT id, nombre, apellido, edad, genero FROM jugadores WHERE id = %s", (id,))
                    ninox = cursor.fetchone() # Renombrado a ninox para evitar conflicto con 'nino' en el render_template.
                    if not ninox:
                        flash("Niño no encontrado.", "error")
                        return redirect(url_for('lista_de_ninos'))

        # <--- IMPORTANTE: Asegúrate de que 'ninox' se pasa a la plantilla para GET requests
        return render_template('public/usuarios/editar_nino.html', nino=ninox, dataLogin=session)


    except Exception as e:
        print(f"Error en editar niño: {e}")
        flash("Error al actualizar niño.", "error")
        return redirect(url_for('lista_de_ninos'))
@app.route('/borrar-nino/<int:id>', methods=['GET'])
def borrar_nino(id):
    try:
        with connectionBD() as conn:
            with conn.cursor() as cursor:
                # Eliminar primero los juegos del niño
                cursor.execute("DELETE FROM juegos WHERE jugador_id = %s", (id,))
                # Luego eliminar al niño
                cursor.execute("DELETE FROM jugadores WHERE id = %s", (id,))
                conn.commit()
        flash("Niño y sus sesiones eliminados correctamente.", "success")
    except Exception as e:
        print(f"Error al eliminar niño: {e}")
        flash("Error al eliminar niño.", "error")
    return redirect(url_for('lista_de_ninos'))

# ====================================================================
#              RUTAS DEL DASHBOARD (VERSIÓN FINAL Y COMPLETA)
# ====================================================================

@app.route('/dashboard')
def dashboard():
    """
    Muestra la página principal del dashboard, cargando datos iniciales.
    """
    if 'conectado' not in session or dataLoginSesion().get('rol') not in [1, 2]:
        flash('Acceso no autorizado al dashboard.', 'error')
        return redirect(url_for('inicio'))

    ultimos_jugadores, settings = [], {}
    try:
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # Cargar últimos 5 jugadores para el carrusel inicial
                cursor.execute("SELECT id, nombre, apellido, edad, genero FROM jugadores ORDER BY id DESC LIMIT 5")
                ultimos_jugadores = cursor.fetchall()
                
                # Cargar toda la configuración desde la base de datos
                cursor.execute("SELECT nombre_ajuste, valor_ajuste FROM configuracion")
                for row in cursor.fetchall():
                    settings[row['nombre_ajuste']] = row['valor_ajuste']
    except Exception as e:
        print(f"Error al cargar datos del dashboard: {e}")
        flash(f"Error al cargar la configuración inicial: {e}", 'error')

    return render_template('public/dashboard.html',
                           dataLogin=dataLoginSesion(),
                           ultimos_jugadores=ultimos_jugadores,
                           settings=settings)


@app.route('/update_setting', methods=['POST'])
def update_setting():
    """
    Ruta AJAX para actualizar un ajuste individual en la base de datos.
    """
    if 'conectado' not in session or dataLoginSesion().get('rol') not in [1, 2]:
        return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 403
    
    data = request.get_json()
    setting_name = data.get('setting_name')
    setting_value = data.get('setting_value')

    if not setting_name:
        return jsonify({'success': False, 'error': 'Falta el nombre del ajuste'}), 400

    try:
        with connectionBD() as conn:
            with conn.cursor() as cursor:
                # Usa INSERT ... ON DUPLICATE KEY UPDATE para insertar o actualizar
                sql = "INSERT INTO configuracion (nombre_ajuste, valor_ajuste) VALUES (%s, %s) ON DUPLICATE KEY UPDATE valor_ajuste = VALUES(valor_ajuste)"
                # Convierte booleans de JS a strings para la BD
                setting_value_db = 'true' if isinstance(setting_value, bool) else str(setting_value)
                cursor.execute(sql, (setting_name, setting_value_db))
                conn.commit()
        return jsonify({'success': True, 'message': f"Ajuste '{setting_name}' guardado."})
    except Exception as e:
        print(f"Error al actualizar el ajuste '{setting_name}': {e}")
        return jsonify({'success': False, 'error': 'Error interno del servidor al guardar.'}), 500


@app.route('/search_children', methods=['GET'])
def search_children():
    """
    Busca jugadores según los criterios del formulario y devuelve un JSON.
    """
    if 'conectado' not in session or dataLoginSesion().get('rol') not in [1, 2]:
        return jsonify({'jugadores': [], 'error': 'Acceso no autorizado'}), 403

    try:
        # Recoger parámetros de la URL
        nombre, apellido = request.args.get('nombre', '').strip(), request.args.get('apellido', '').strip()
        edad, genero = request.args.get('edad', '').strip(), request.args.get('genero', '').strip()
        
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                query, params = "SELECT id, nombre, apellido, edad, genero FROM jugadores WHERE 1=1", []
                if nombre: query += " AND nombre LIKE %s"; params.append(f"%{nombre}%")
                if apellido: query += " AND apellido LIKE %s"; params.append(f"%{apellido}%")
                if edad: query += " AND edad = %s"; params.append(edad)
                if genero: query += " AND genero = %s"; params.append(genero)
                query += " ORDER BY nombre ASC, apellido ASC LIMIT 20"
                cursor.execute(query, tuple(params))
                jugadores_encontrados = cursor.fetchall()
        # Devuelve siempre un JSON válido, incluso si no hay resultados
        return jsonify({'jugadores': jugadores_encontrados})
    except Exception as e:
        print(f"Error en la búsqueda de niños: {e}")
        return jsonify({'jugadores': [], 'error': 'Error interno del servidor al buscar.'}), 500


@app.route('/get_next_session_number/<int:player_id>')
def get_next_session_number(player_id):
    """
    Consulta la BD para determinar el siguiente número de sesión para un jugador.
    """
    if 'conectado' not in session or dataLoginSesion().get('rol') not in [1, 2]:
        return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 403
    
    try:
        with connectionBD() as conn:
            with conn.cursor() as cursor:
                # Se usa la tabla 'juegos' para contar las sesiones
                cursor.execute("SELECT MAX(nro_sesion) FROM juegos WHERE jugador_id = %s", (player_id,))
                max_sesion = cursor.fetchone()[0]
                next_session_number = (max_sesion or 0) + 1
        return jsonify({'success': True, 'next_session_number': next_session_number})
    except Exception as e:
        print(f"Error al obtener número de sesión para el jugador {player_id}: {e}")
        return jsonify({'success': False, 'error': 'Error al consultar número de sesión.'}), 500


@app.route('/save_session_result', methods=['POST'])
def save_session_result():
    """
    Recibe los datos finales de la sesión y los guarda en la tabla 'juegos'.
    """
    if 'conectado' not in session or dataLoginSesion().get('rol') not in [1, 2]:
        return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No se recibieron datos'}), 400

    try:
        jugador_id = int(data.get('playerId'))
        nro_sesion = int(data.get('sessionNumber'))
        if not nro_sesion or nro_sesion < 1:
            return jsonify({'success': False, 'error': 'Número de sesión inválido.'}), 400

        # Verificar que el jugador exista
        with connectionBD() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM jugadores WHERE id = %s", (jugador_id,))
                if cursor.fetchone() is None:
                    return jsonify({'success': False, 'error': 'Jugador no encontrado.'}), 400

        # Convertir timestamps a datetime de Ecuador
        ecuador_tz = pytz.timezone('America/Guayaquil')
        fecha_inicio_ec = datetime.fromtimestamp(data.get('sessionStartTime') / 1000).astimezone(ecuador_tz)
        fecha_fin_ec = datetime.fromtimestamp(data.get('sessionEndTime') / 1000).astimezone(ecuador_tz)

        counts = data.get('gaugeCounts', {})

        rendimiento = data.get('rendimiento', 'No clasificado')

        # Generar UUID para esta sesión
        nuevo_uuid = str(uuid.uuid4())

        params = (
            jugador_id, 1, fecha_inicio_ec, fecha_fin_ec,
            counts.get('Aro', 0), counts.get('Izquierda', 0), counts.get('Derecha', 0), counts.get('Arriba', 0),
            nro_sesion, data.get('durationText', 'N/A'), data.get('diagnosticText', ''), rendimiento, nuevo_uuid
        )

        with connectionBD() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO juegos (
                        jugador_id, id_juguete, fecha_inicio, fecha_fin, 
                        cantidad_aros, zona_izq, zona_der, zona_arr, 
                        nro_sesion, duracion, diagnostico, rendimiento, uuid
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, params)
                conn.commit()

        return jsonify({'success': True, 'message': 'Resultados guardados correctamente.', 'uuid': nuevo_uuid})

    except Exception as e:
        print(f"Error al guardar la sesión: {e}")
        return jsonify({'success': False, 'error': 'Error interno del servidor al guardar.'}), 500



@app.route('/sync_settings', methods=['POST'])
def sync_settings():
    """ Recibe todos los ajustes y los actualiza en la base de datos. """
    if 'id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    settings = request.get_json()
    if not settings:
        return jsonify({'success': False, 'error': 'No se recibieron datos'}), 400

    try:
        with connectionBD() as conn:
            with conn.cursor() as cursor:
                for key, value in settings.items():
                    # Usamos INSERT ... ON DUPLICATE KEY UPDATE para insertar si no existe, o actualizar si ya existe.
                    # Asume que (nombre_ajuste, id_juguete) es una clave única.
                    sql = """
                        INSERT INTO configuracion (nombre_ajuste, valor_ajuste, id_juguete)
                        VALUES (%s, %s, 1)
                        ON DUPLICATE KEY UPDATE valor_ajuste = %s
                    """
                    cursor.execute(sql, (key, str(value), str(value)))
                conn.commit()
        return jsonify({'success': True, 'message': 'Ajustes sincronizados'})
    except Exception as e:
        print(f"Error en /sync_settings: {e}")
        return jsonify({'success': False, 'error': 'Error en la base de datos'}), 500

@app.route('/set_game_state', methods=['POST'])
def set_game_state():
    """ Establece el estado del juego (true/false) en la tabla sincronizacion_estado. """
    if 'id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    data = request.get_json()
    new_state = data.get('estado', False)
    
    try:
        with connectionBD() as conn:
            with conn.cursor() as cursor:
                # Asumimos que solo hay una fila, para id_juguete = 1.
                # UPDATE ... WHERE id_juguete=1 sería más seguro que un TRUNCATE si hubiera más juguetes.
                sql = "UPDATE sincronizacion_estado SET estado = %s WHERE id_juguete = 1"
                cursor.execute(sql, (new_state,))
                conn.commit()
        return jsonify({'success': True, 'message': f'Estado del juego actualizado a {new_state}'})
    except Exception as e:
        print(f"Error en /set_game_state: {e}")
        return jsonify({'success': False, 'error': 'Error en la base de datos'}), 500

@app.route('/get_game_counters')
def get_game_counters():
    """ Obtiene los contadores actuales de la tabla sincronizacion_estado. """
    if 'id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT conteo_izquierda, conteo_derecha, conteo_arriba, conteo_aro FROM sincronizacion_estado WHERE id_juguete = 1")
                counters = cursor.fetchone()
        
        if not counters:
            # Si no hay fila, devolver ceros para evitar errores en el frontend.
            return jsonify({
                'Aro': 0, 'Arriba': 0, 'Izquierda': 0, 'Derecha': 0
            })

        # Mapear nombres de columnas a los nombres que usa el frontend
        mapped_counters = {
            'Aro': counters.get('conteo_aro', 0),
            'Arriba': counters.get('conteo_arriba', 0),
            'Izquierda': counters.get('conteo_izquierda', 0),
            'Derecha': counters.get('conteo_derecha', 0)
        }
        return jsonify(mapped_counters)
    except Exception as e:
        print(f"Error en /get_game_counters: {e}")
        return jsonify({'success': False, 'error': 'Error en la base de datos'}), 500

@app.route('/reset_game_counters', methods=['POST'])
def reset_game_counters():
    """ 
    Guarda la sesión actual en el historial (juegos) y luego reinicia los contadores. 
    """
    if 'conectado' not in session: # Ajustado a tu variable de sesión
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # 1. LEER: Obtenemos los puntos actuales ANTES de borrarlos
                cursor.execute("SELECT * FROM sincronizacion_estado WHERE id_juguete = 1")
                data_sync = cursor.fetchone()
                
                if not data_sync:
                    return jsonify({'success': False, 'error': 'No se encontraron datos del juguete'})

                # 2. GUARDAR: Insertamos en la tabla 'juegos' solo si hubo juego
                # (Si todo es 0, asumimos que no se jugó y solo se resetea)
                if (data_sync['conteo_aro'] > 0 or data_sync['conteo_izquierda'] > 0 or 
                    data_sync['conteo_derecha'] > 0 or data_sync['conteo_arriba'] > 0):
                    
                    # Generar UUID obligatorio
                    new_uuid = str(uuid.uuid4())
                    
                    # Obtener ID del jugador si está en la sesión, o None
                    # Ajusta 'playerId' o 'user_id' según como guardes esto en tu login
                    jugador_id = session.get('playerId') 
                    
                    sql_insert = """
                        INSERT INTO juegos 
                        (id_juguete, jugador_id, fecha_inicio, fecha_fin, 
                         cantidad_aros, zona_izq, zona_der, zona_arr, 
                         nro_sesion, uuid, duracion, diagnostico, rendimiento) 
                        VALUES 
                        (1, %s, NOW(), NOW(), 
                         %s, %s, %s, %s, 
                         1, %s, 'Manual', 'Finalizado desde Panel', 'N/A')
                    """
                    # Nota: nro_sesion se pone en 1 por defecto para evitar errores.
                    
                    values = (
                        jugador_id,
                        data_sync['conteo_aro'],
                        data_sync['conteo_izquierda'],
                        data_sync['conteo_derecha'],
                        data_sync['conteo_arriba'],
                        new_uuid
                    )
                    cursor.execute(sql_insert, values)

                # 3. RESETEAR: Ponemos los contadores a 0
                # CORRECCIÓN: Quitamos 'timestamp = NOW()' porque esa columna NO existe.
                sql_reset = """
                    UPDATE sincronizacion_estado
                    SET conteo_izquierda = 0, 
                        conteo_derecha = 0, 
                        conteo_arriba = 0, 
                        conteo_aro = 0, 
                        estado = 0
                    WHERE id_juguete = 1
                """
                cursor.execute(sql_reset)
                conn.commit()

        return jsonify({'success': True, 'message': 'Juego guardado y reiniciado.'})

    except Exception as e:
        print(f"Error CRITICO en /reset_game_counters: {e}")
        return jsonify({'success': False, 'error': f'Error interno: {str(e)}'}), 500

@app.route('/get_all_settings')
def get_all_settings():
    """ Devuelve todos los ajustes actuales de la tabla de configuración. """
    if 'id' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401

    try:
        with connectionBD() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # Asumimos que todos los ajustes son para id_juguete = 1
                cursor.execute("SELECT nombre_ajuste, valor_ajuste FROM configuracion WHERE id_juguete = 1")
                settings_list = cursor.fetchall()

        # Convertir la lista de diccionarios a un solo diccionario clave-valor
        settings_dict = {item['nombre_ajuste']: item['valor_ajuste'] for item in settings_list}
        return jsonify(settings_dict)

    except Exception as e:
        print(f"Error en /get_all_settings: {e}")
        return jsonify({'success': False, 'error': 'Error en la base de datos'}), 500
    
    


@app.route('/update_diagnostic', methods=['POST'])
def update_diagnostic():
    """
    Actualiza el texto del diagnóstico de una sesión específica.
    """
    # 1. Verificar permisos
    if 'conectado' not in session or dataLoginSesion().get('rol') not in [1, 2]:
        return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 403

    # 2. Obtener los datos
    data = request.get_json()
    if not data or 'sessionId' not in data or 'diagnosticText' not in data:
        return jsonify({'success': False, 'error': 'Datos incompletos'}), 400

    try:
        session_id = int(data['sessionId'])
        diagnostic_text = data['diagnosticText']

        # 3. Actualizar la base de datos
        with connectionBD() as conn:
            with conn.cursor() as cursor:
                sql = "UPDATE juegos SET diagnostico = %s WHERE id = %s"
                cursor.execute(sql, (diagnostic_text, session_id))
                conn.commit()
        
        return jsonify({'success': True, 'message': 'Diagnóstico actualizado correctamente.'})

    except ValueError:
        return jsonify({'success': False, 'error': 'ID de sesión inválido.'}), 400
    except Exception as e:
        print(f"Error al actualizar el diagnóstico: {e}")
        return jsonify({'success': False, 'error': 'Error interno del servidor al guardar.'}), 500