import streamlit as st
import time
# Importamos la lógica de nuestra Crew
from crew_bot import procesar_pregunta_agentes

# 1. Configuración visual de la UI
st.set_page_config(
    page_title="Agente Multi-Agente GLPI", 
    page_icon="🕵️‍♂️", 
    layout="centered"
)

st.title("🕵️‍♂️ Crew Analista de BD")
st.markdown("""
Esta interfaz utiliza una **Crew** de 3 agentes especializados:
1. **Arquitecto:** Planifica la consulta.
2. **DBA:** Ejecuta el SQL en MariaDB.
3. **Analista:** Redacta el reporte final.
""")

# 2. Inicializar el historial del chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 3. Mostrar mensajes previos
for mensaje in st.session_state.chat_history:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

# 4. Entrada del usuario
if prompt := st.chat_input("Ej: ¿Qué grupos han cerrado más tickets este mes?"):
    
    # Agregar mensaje del usuario al chat
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 5. Ejecución de la Crew (El corazón del sistema)
    with st.chat_message("assistant"):
        # Usamos un contenedor vacío para ir mostrando el progreso
        with st.spinner("🚀 El escuadrón está trabajando (Arquitecto -> DBA -> Analista)..."):
            try:
                # Llamamos a la función de crew_bot.py
                inicio_tiempo = time.time()
                resultado = procesar_pregunta_agentes(prompt)
                fin_tiempo = time.time()
                
                # Mostramos el resultado final generado por el Agente Analista
                st.markdown(resultado)
                st.caption(f"⏱️ Análisis completado en {round(fin_tiempo - inicio_tiempo, 2)} segundos.")
                
                # Guardamos en el historial
                st.session_state.chat_history.append({"role": "assistant", "content": resultado})
                
            except Exception as e:
                st.error(f"❌ Error en la ejecución de la Crew: {e}")
                st.info("Revisa los logs de Docker para ver el detalle del razonamiento de los agentes.")

# 6. Barra lateral con información técnica
with st.sidebar:
    st.header("⚙️ Estado del Sistema")
    st.success("Conectado a MariaDB (GLPI)")
    st.info("Modelo IA: AWS Bedrock (Claude 3)")
    if st.button("Limpiar Historial"):
        st.session_state.chat_history = []
        st.rerun()