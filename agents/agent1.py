from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from config import OLLAMA_MODEL, OLLAMA_BASE_URL, GYM_NAME, AGENT1_SYSTEM_PROMPT
import json

# Inicializar el LLM
llm = Ollama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.3
)

# Intenciones posibles
INTENTS = {
    "NUEVO_INFORME": "Cliente nuevo pidiendo precios o información general",
    "CONSULTA_MEMBRESIA": "Socio preguntando por su membresía, vencimiento o pagos",
    "PROBLEMA_APP": "Problema con la aplicación de entrenamientos",
    "PROBLEMA_ACCESO": "Problema para entrar al gimnasio físicamente",
    "OTRO": "Consulta que no encaja en las anteriores"
}

def detect_intent(message: str) -> dict:
    """
    Detecta la intención del mensaje del cliente.
    Devuelve: { intent, confidence, extracted_data }
    """
    prompt = f"""Analiza este mensaje de un cliente de gimnasio y clasifícalo.

Mensaje: "{message}"

Intenciones posibles:
- NUEVO_INFORME: cliente nuevo pidiendo precios, planes, informes
- CONSULTA_MEMBRESIA: socio preguntando su membresía, vencimiento, renovación
- PROBLEMA_APP: no puede usar la app, error en aplicación, no ve rutinas
- PROBLEMA_ACCESO: no puede entrar al gym, torniquete no funciona, código no sirve
- OTRO: cualquier otra cosa

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
  "intent": "NOMBRE_DE_LA_INTENCION",
  "confidence": "ALTA/MEDIA/BAJA",
  "extracted_data": {{
    "phone": null,
    "name": null,
    "problem_description": null
  }}
}}

No agregues texto antes ni después del JSON."""

    response = llm.invoke(prompt)
    
    # Limpiar respuesta y parsear JSON
    try:
        clean = response.strip()
        # Buscar el JSON aunque haya texto extra
        start = clean.find('{')
        end = clean.rfind('}') + 1
        json_str = clean[start:end]
        result = json.loads(json_str)
        return result
    except Exception as e:
        # Si falla el parse, devolver intención por defecto
        return {
            "intent": "OTRO",
            "confidence": "BAJA",
            "extracted_data": {
                "phone": None,
                "name": None,
                "problem_description": message
            }
        }

def generate_response(message: str, intent: str, 
                      context_data: dict = None) -> str:
    """
    Genera una respuesta al cliente basada en la intención detectada
    y datos de contexto opcionales (planes, membresía, etc.)
    """
    system = AGENT1_SYSTEM_PROMPT.format(gym_name=GYM_NAME)
    
    context_text = ""
    if context_data:
        context_text = f"\n\nInformación disponible:\n{json.dumps(context_data, ensure_ascii=False, indent=2)}"
    
    prompt = f"""{system}

Intención detectada: {intent}
{context_text}

Mensaje del cliente: {message}

Responde al cliente de forma amable y útil."""

    response = llm.invoke(prompt)
    return response.strip()

def process_message(message: str) -> dict:
    """
    Función principal del Agente 1.
    Recibe el mensaje del cliente y devuelve todo procesado.
    """
    print(f"\n[Agente 1] Procesando: '{message}'")
    
    # 1. Detectar intención
    intent_result = detect_intent(message)
    intent = intent_result.get('intent', 'OTRO')
    confidence = intent_result.get('confidence', 'BAJA')
    extracted = intent_result.get('extracted_data', {})
    
    print(f"[Agente 1] Intención: {intent} (confianza: {confidence})")
    
    # 2. Generar respuesta inicial
    response = generate_response(message, intent)
    
    return {
        "original_message": message,
        "intent": intent,
        "confidence": confidence,
        "extracted_data": extracted,
        "initial_response": response,
        "needs_phone": intent == "CONSULTA_MEMBRESIA" and not extracted.get('phone')
    }