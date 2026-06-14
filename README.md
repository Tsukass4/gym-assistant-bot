# GymBot 🏋️ — Asistente Inteligente para Gimnasio

Sistema experto basado en agentes inteligentes para automatizar la atención al cliente de **The Field** gimnasio. Desarrollado como proyecto final de Sistemas Expertos — José Andrés Rivera Assad | 23110118 | 7°E.

## ¿Qué hace?

- Atiende clientes nuevos dando informes de precios y planes
- Consulta el estatus de membresía de socios existentes
- Recibe y registra problemas técnicos con la app o el acceso
- Genera explicaciones de cada decisión tomada por el sistema

## Arquitectura — 3 Agentes

| Agente | Función |
|--------|---------|
| Agente 1 — Recepcionista | Detecta intención del cliente y responde |
| Agente 2 — Motor de reglas | Aplica lógica IF-THEN del gimnasio |
| Agente 3 — Supervisor | Explica decisiones y alerta al staff |

## Reglas de inferencia implementadas

- R1: IF cliente_nuevo THEN mostrar_planes_disponibles
- R2a: IF consulta_membresia AND sin_telefono THEN solicitar_telefono
- R2b: IF telefono_no_encontrado THEN sugerir_verificar
- R2c: IF membresia_vencida THEN ofrecer_renovacion
- R2d: IF membresia_vence_en_menos_7_dias THEN recordatorio_urgente
- R2e: IF membresia_activa THEN mostrar_estatus_normal
- R2f: IF cliente_6_meses_plan_mensual THEN sugerir_plan_anual
- R3a: IF problema_app THEN crear_ticket_prioridad_NORMAL
- R3b: IF problema_acceso THEN crear_ticket_prioridad_ALTA + alerta_RED

## Tecnologías utilizadas

- Python 3.10+
- LangChain + Ollama (llama3.2:1b)
- Streamlit
- SQLite
- LangChain Community

## Instalación paso a paso

### 1. Clonar el repositorio

git clone https://github.com/TU_USUARIO/gym-assistant-bot.git
cd gym-assistant-bot

### 2. Crear entorno virtual

python -m venv venv
venv\Scripts\activate

### 3. Instalar dependencias

pip install -r requirements.txt

### 4. Instalar Ollama

Descarga desde ollama.com e instala el modelo:

ollama pull llama3.2:1b

### 5. Configurar variables de entorno

Crea un archivo .env en la raíz del proyecto con este contenido:

GYM_NAME=The Field

### 6. Inicializar la base de datos

python -c "from database.db import init_db; init_db()"

### 7. Ejecutar la aplicación

streamlit run ui/app.py

Abre tu navegador en http://localhost:8501

## Estructura del proyecto

gym-assistant-bot/
├── agents/
│   ├── agent1.py          # Agente 1 — Recepcionista virtual
│   ├── agent2.py          # Agente 2 — Motor de reglas e inferencias
│   ├── agent3.py          # Agente 3 — Supervisor y explicador
│   └── pipeline.py        # Conecta los 3 agentes en secuencia
├── database/
│   ├── db.py              # Funciones CRUD y conexión a SQLite
│   └── schema.sql         # Esquema de tablas y datos de prueba
├── ui/
│   ├── app.py             # Interfaz de chat principal
│   └── pages/
│       └── admin.py       # Panel de administración del staff
├── docs/
│   └── architecture.md    # Documentación de arquitectura
├── config.py              # Configuración general del sistema
├── .env                   # Variables de entorno (no se sube a GitHub)
├── .gitignore
├── requirements.txt
└── README.md

## Base de datos

El sistema usa SQLite con las siguientes tablas:

- members — Socios del gimnasio
- plans — Planes y precios disponibles
- memberships — Membresías activas y vencidas
- tickets — Tickets de soporte generados por los agentes
- conversation_logs — Logs de cada interacción para el Agente 3

## Limitaciones conocidas

- El modelo llama3.2:1b es pequeño y puede clasificar mal mensajes muy cortos o ambiguos
- Se implementaron reglas manuales de detección para los casos más frecuentes
- En producción se recomienda usar un modelo más grande como llama3 o Gemini

## Video demostrativo

Enlace al video en YouTube: [AGREGAR ENLACE DESPUÉS DE GRABAR]

## Autor

José Andrés Rivera Assad | Estudiante 23110118 | 7°E
Ingeniería Mecatrónica | Sistemas Expertos
