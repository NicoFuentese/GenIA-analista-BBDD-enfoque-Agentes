import os
from crewai import Agent, Task, Crew, Process
from langchain_aws import ChatBedrock
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import InfoSQLDatabaseTool, QuerySQLDataBaseTool
from dotenv import load_dotenv

# Cargamos las variables de entorno
load_dotenv()

# 1. CONEXIÓN A LA BASE DE DATOS
user = os.getenv("DB_USER")
password = os.getenv("DB_PASS")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT", "3306")
db_name = os.getenv("DB_NAME")

db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
db = SQLDatabase.from_uri(db_url)

# 2. HERRAMIENTAS Y LLM
herramienta_esquema = InfoSQLDatabaseTool(db=db)
herramienta_query = QuerySQLDataBaseTool(db=db)

llm_bedrock = ChatBedrock(
    model_id=os.getenv("MODEL_ID"), # Ajusta a tu modelo de AWS
    model_kwargs={"temperature": 0.1}
)

# 3. LOS AGENTES (El Equipo)
arquitecto_datos = Agent(
    role='Arquitecto de Datos Senior',
    goal='Diseñar un plan técnico detallado revisando la estructura de la base de datos GLPI.',
    backstory='Conoces GLPI a la perfección (sabes que las áreas son glpi_groups). Exploras el esquema y le dices al desarrollador qué tablas usar.',
    tools=[herramienta_esquema],
    llm=llm_bedrock,
    allow_delegation=False
)

dba_developer = Agent(
    role='Desarrollador SQL y DBA',
    goal='Escribir y ejecutar una consulta SQL optimizada (solo SELECT) en MariaDB.',
    backstory='Eres un purista del SQL. Tomas las instrucciones del Arquitecto, armas la query, la ejecutas y entregas los resultados exactos.',
    tools=[herramienta_query],
    llm=llm_bedrock,
    allow_delegation=False
)

analista_negocio = Agent(
    role='Analista de Negocios de TI',
    goal='Traducir los datos crudos en una respuesta ejecutiva y clara para el usuario final.',
    backstory='Eres el puente entre tecnología y gerencia. Transformas datos en reportes limpios y amables en Markdown. No muestras errores técnicos.',
    tools=[], 
    llm=llm_bedrock,
    allow_delegation=False
)

# 4. LA FUNCIÓN PRINCIPAL
def procesar_pregunta_agentes(pregunta_usuario):
    """Esta función recibe la pregunta y arranca la cadena de trabajo de la Crew."""
    
    # Definimos las tareas inyectando la pregunta del usuario
    tarea_arquitectura = Task(
        description=f"Analizar la siguiente solicitud: '{pregunta_usuario}'. Revisa el esquema de bases de datos de GLPI y define exactamente qué tablas y columnas se necesitan.",
        expected_output="Un plan de acción en viñetas indicando tablas y relaciones (JOINs) a utilizar.",
        agent=arquitecto_datos
    )

    tarea_desarrollo = Task(
        description=f"Basado en el plan del arquitecto, escribe una query SQL (solo SELECT) para responder: '{pregunta_usuario}'. Ejecuta la query usando tu herramienta.",
        expected_output="Los datos crudos extraídos de la base de datos y el código SQL utilizado.",
        agent=dba_developer
    )

    tarea_analisis = Task(
        description=f"Toma los datos extraídos por el DBA y redacta una respuesta final para la solicitud original: '{pregunta_usuario}'.",
        expected_output="Una respuesta final bien formateada en Markdown, lista para ser leída por un gerente.",
        agent=analista_negocio
    )

    # Armamos la Crew
    equipo_glpi = Crew(
        agents=[arquitecto_datos, dba_developer, analista_negocio],
        tasks=[tarea_arquitectura, tarea_desarrollo, tarea_analisis],
        process=Process.sequential, # Trabajan uno después del otro
        verbose=True
    )

    #Arrancamos proceso
    resultado_final = equipo_glpi.kickoff()
    return resultado_final