// --- ¡IMPORTANTE! ---
// Reemplaza esta URL con la URL de tu backend en Render
const API_URL = 'https://light-work.onrender.com';
// ---

// Espera a que todo el HTML esté cargado
document.addEventListener('DOMContentLoaded', () => {

    // Referencias a los botones y al div de resultados
    const btnCrear = document.getElementById('btn-crear-datos');
    const btnChequear = document.getElementById('btn-chequear');
    const resultadosDiv = document.getElementById('resultados');

    // Referencias a los inputs
    const inputNombre = document.getElementById('nombre-usuario');
    const inputObjetivo = document.getElementById('nombre-objetivo');
    const inputTareaAyer = document.getElementById('tarea-ayer');
    const inputTareaHoy = document.getElementById('tarea-hoy');

    let datosPrueba = {}; // Guardaremos los IDs aquí

    // -- Función para crear los datos de prueba --
    btnCrear.addEventListener('click', async () => {
        resultadosDiv.textContent = 'Creando datos...';
        try {
            // 1. Crear Usuario
            const resUsuario = await fetch(`${API_URL}/usuario`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    nombre: inputNombre.value,
                    email: `${inputNombre.value.toLowerCase()}@email.com`
                })
            });
            const usuario = await resUsuario.json();
            if (!resUsuario.ok) throw new Error(usuario.error || 'Error al crear usuario');
            
            datosPrueba.usuario_id = usuario.id;

            // 2. Crear Objetivo
            const resObjetivo = await fetch(`${API_URL}/objetivo`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    usuario_id: datosPrueba.usuario_id,
                    nombre_objetivo: inputObjetivo.value,
                    fecha_limite: '2025-12-31'
                })
            });
            const objetivo = await resObjetivo.json();
            if (!resObjetivo.ok) throw new Error(objetivo.error || 'Error al crear objetivo');

            datosPrueba.objetivo_id = objetivo.id;

            // 3. Crear Tarea de AYER (para simular el "fallo")
            const ayer = new Date();
            ayer.setDate(ayer.getDate() - 1); // Resta un día
            const fechaAyerStr = `${ayer.getFullYear()}-${String(ayer.getMonth() + 1).padStart(2, '0')}-${String(ayer.getDate()).padStart(2, '0')} 18:00`;

            await fetch(`${API_URL}/tarea`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    objetivo_id: datosPrueba.objetivo_id,
                    descripcion: inputTareaAyer.value,
                    fecha_programada: fechaAyerStr
                })
            });

            // 4. Crear Tarea de HOY (para simular el "recordatorio")
            const hoy = new Date();
            hoy.setHours(hoy.getHours() + 1); // Suma una hora
            const fechaHoyStr = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}-${String(hoy.getDate()).padStart(2, '0')} ${String(hoy.getHours()).padStart(2, '0')}:${String(hoy.getMinutes()).padStart(2, '0')}`;
            
            await fetch(`${API_URL}/tarea`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    objetivo_id: datosPrueba.objetivo_id,
                    descripcion: inputTareaHoy.value,
                    fecha_programada: fechaHoyStr
                })
            });

            resultadosDiv.textContent = `¡Datos de prueba creados!\nUsuario ID: ${datosPrueba.usuario_id}\nObjetivo ID: ${datosPrueba.objetivo_id}\n\nListo para el Paso 2.`;
            
        } catch (error) {
            resultadosDiv.textContent = `Error: ${error.message}`;
        }
    });

    // -- Función para chequear el cerebro --
    btnChequear.addEventListener('click', async () => {
        resultadosDiv.textContent = 'Chequeando tareas... llamando al cerebro...';
        try {
            const res = await fetch(`${API_URL}/trigger-chequeo-proactivo`);
            const data = await res.json();
            
            if (data.mensajes_generados && data.mensajes_generados.length > 0) {
                // Formatea los mensajes para que se vean bien
                resultadosDiv.textContent = data.mensajes_generados
                    .map(msg => msg.replace('[SIMULACIÓN DE ENVÍO] Para ', ''))
                    .join('\n\n'); // Doble salto de línea entre mensajes
            } else {
                resultadosDiv.textContent = 'No se generaron mensajes. (Asegúrate de haber creado datos de prueba y que las horas sean correctas)';
            }
            
        } catch (error) {
            resultadosDiv.textContent = `Error: ${error.message}`;
        }
    });
});
