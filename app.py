import os
import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # <--- 1. IMPORTACIÓN AÑADIDA

# --- CONFIGURACIÓN ---
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)  # <--- 2. LÍNEA AÑADIDA (habilita CORS para toda la app)

# Configura la base de datos SQLite. Se creará un archivo 'app.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DE BASE DE DATOS ---

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    objetivos = db.relationship('Objetivo', backref='usuario', lazy=True)

class Objetivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    nombre = db.Column(db.String(255), nullable=False)
    fecha_limite = db.Column(db.Date)
    tareas = db.relationship('Tarea', backref='objetivo', lazy=True)

class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    objetivo_id = db.Column(db.Integer, db.ForeignKey('objetivo.id'), nullable=False)
    descripcion = db.Column(db.String(500), nullable=False)
    fecha_programada = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String(50), default='pendiente')

# --- RUTAS DE LA API (Endpoints) ---

@app.route('/')
def index():
    return "¡El backend del Co-Piloto está funcionando! (CORS HABILITADO)"

# --- API para crear Usuarios, Objetivos y Tareas ---

@app.route('/usuario', methods=['POST'])
def crear_usuario():
    datos = request.json
    try:
        nuevo_usuario = Usuario(nombre=datos['nombre'], email=datos['email'])
        db.session.add(nuevo_usuario)
        db.session.commit()
        return jsonify({'id': nuevo_usuario.id, 'mensaje': 'Usuario creado'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/objetivo', methods=['POST'])
def crear_objetivo():
    datos = request.json
    try:
        nuevo_objetivo = Objetivo(
            usuario_id=datos['usuario_id'],
            nombre=datos['nombre_objetivo'],
            fecha_limite=datetime.datetime.strptime(datos['fecha_limite'], '%Y-%m-%d').date()
        )
        db.session.add(nuevo_objetivo)
        db.session.commit()
        return jsonify({'id': nuevo_objetivo.id, 'mensaje': 'Objetivo creado'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/tarea', methods=['POST'])
def crear_tarea():
    datos = request.json
    try:
        nueva_tarea = Tarea(
            objetivo_id=datos['objetivo_id'],
            descripcion=datos['descripcion'],
            fecha_programada=datetime.datetime.strptime(datos['fecha_programada'], '%Y-%m-%d %H:%M')
        )
        db.session.add(nueva_tarea)
        db.session.commit()
        return jsonify({'id': nueva_tarea.id, 'mensaje': 'Tarea creada'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/tarea/<int:tarea_id>/completar', methods=['POST'])
def completar_tarea(tarea_id):
    tarea = Tarea.query.get(tarea_id)
    if not tarea:
        return jsonify({'error': 'Tarea no encontrada'}), 404
    tarea.estado = 'completada'
    db.session.commit()
    return jsonify({'mensaje': f"Tarea '{tarea.descripcion}' completada."})


# --- EL CEREBRO PROACTIVO ---

def generar_mensaje_proactivo(tarea, usuario, tipo_mensaje):
    """
    Genera los 3 mensajes clave usando plantillas (Escenario 1.5)
    """
    if tipo_mensaje == 'recordatorio':
        return f"¡Hola {usuario.nombre}! Es hora de tu sesión de '{tarea.descripcion}'. ¡Vamos!"
    
    elif tipo_mensaje == 'replanificar':
        return f"Hey {usuario.nombre}, vi que ayer no marcaste la tarea '{tarea.descripcion}'. ¿La movemos para hoy a la tarde o la fusionamos con la de mañana?"
    
    elif tipo_mensaje == 'felicitacion':
        conteo = len(tarea)
        return f"¡Completaste {conteo} tareas esta semana! ¡Excelente progreso en tu objetivo '{tarea[0].objetivo.nombre}'!"
    
    return None

@app.route('/trigger-chequeo-proactivo', methods=['GET'])
def ejecutar_chequeo_proactivo():
    """
    ESTE ES EL ENDPOINT QUE LLAMARÍA EL CRON JOB.
    Simula el envío de notificaciones.
    """
    
    ahora = datetime.datetime.now()
    hoy_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    ayer_inicio = hoy_inicio - datetime.timedelta(days=1)
    semana_pasada_inicio = hoy_inicio - datetime.timedelta(days=7)

    mensajes_generados = []

    # 1. Lógica del Mensaje 1: Recordatorio de Tarea de Hoy
    limite_recordatorio = ahora + datetime.timedelta(hours=1)
    tareas_para_hoy = Tarea.query.join(Objetivo).join(Usuario).filter(
        Tarea.estado == 'pendiente',
        Tarea.fecha_programada >= ahora,
        Tarea.fecha_programada <= limite_recordatorio
    ).all()
    
    for tarea in tareas_para_hoy:
        mensaje = generar_mensaje_proactivo(tarea, tarea.objetivo.usuario, 'recordatorio')
        mensajes_generados.append(f"[SIMULACIÓN DE ENVÍO] Para {tarea.objetivo.usuario.email}: {mensaje}")

    # 2. Lógica del Mensaje 2: Replanificar Tarea de Ayer
    tareas_pendientes_ayer = Tarea.query.join(Objetivo).join(Usuario).filter(
        Tarea.estado == 'pendiente',
        Tarea.fecha_programada >= ayer_inicio,
        Tarea.fecha_programada < hoy_inicio
    ).all()

    for tarea in tareas_pendientes_ayer:
        mensaje = generar_mensaje_proactivo(tarea, tarea.objetivo.usuario, 'replanificar')
        mensajes_generados.append(f"[SIMULACIÓN DE ENVÍO] Para {tarea.objetivo.usuario.email}: {mensaje}")

    # 3. Lógica del Mensaje 3: Felicitación Semanal
    tareas_completadas_semana = Tarea.query.join(Objetivo).join(Usuario).filter(
        Tarea.estado == 'completada',
        Tarea.fecha_programada >= semana_pasada_inicio
    ).all()
    
    tareas_por_usuario = {}
    for tarea in tareas_completadas_semana:
        uid = tarea.objetivo.usuario_id
        if uid not in tareas_por_usuario:
            tareas_por_usuario[uid] = []
        tareas_por_usuario[uid].append(tarea)

    for uid, lista_tareas in tareas_por_usuario.items():
        if len(lista_tareas) >= 5: # Umbral de felicitación
            usuario = Usuario.query.get(uid)
            mensaje = generar_mensaje_proactivo(lista_tareas, usuario, 'felicitacion')
            mensajes_generados.append(f"[SIMULACIÓN DE ENVÍO] Para {usuario.email}: {mensaje}")

    return jsonify({
        'status': 'Chequeo completado',
        'mensajes_generados': mensajes_generados
    })


# --- INICIAR LA APP ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
