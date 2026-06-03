from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from config import OLLAMA_MODEL, OLLAMA_BASE_URL, GYM_NAME, AGENT1_SYSTEM_PROMPT
from database.db import (
    get_member_by_phone,
    get_active_membership,
    get_all_plans,
    days_until_expiry
)
import json

# Inicializar el LLM
llm = Ollama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.3
)

INTENTS = [
    "NUEVO_INFORME",
    "CONSULTA_MEMBRESIA",
    "PROBLEMA_APP",
    "PROBLEMA_ACCESO",
    "OTRO"
]

def detect_intent(message: str) -> dict:
    """Detecta la intención del mensaje del cliente."""
    prompt = f"""Analiza este mensaje de un cliente de gimnasio y clasifícalo.

Mensaje: "{message}"

Intenciones posibles:
- NUEVO_INFORME: cliente nuevo pidiendo precios, planes, informes
- CONSULTA_MEMBRESIA: socio preguntando su membresía, vencimiento, renovación
- PROBLEMA_APP: no puede usar la app, error en aplicación, no ve rutinas
- PROBLEMA_ACCESO: no puede entrar al gym, torniquete no funciona
- OTRO: cualquier otra cosa

Responde ÚNICAMENTE con JSON válido:
{{
  "intent": "NOMBRE_INTENCION",
  "confidence": "ALTA/MEDIA/BAJA",
  "extracted_data": {{
    "phone": null,
    "name": null,
    "problem_description": null
  }}
}}"""

    response = llm.invoke(prompt)
    try:
        clean = response.strip()
        start = clean.find('{')
        end = clean.rfind('}') + 1
        return json.loads(clean[start:end])
    except:
        return {
            "intent": "OTRO",
            "confidence": "BAJA",
            "extracted_data": {
                "phone": None,
                "name": None,
                "problem_description": message
            }
        }

def extract_phone(message: str) -> str | None:
    """Extrae un número de teléfono del mensaje si existe."""
    import re
    phones = re.findall(r'\b\d{10}\b', message)
    return phones[0] if phones else None

def handle_nuevo_informe() -> dict:
    """
    Maneja la intención NUEVO_INFORME.
    Obtiene todos los planes de la BD y los formatea.
    """
    plans = get_all_plans()
    plans_text = "\n".join([
        f"- {p['name']}: ${p['price']:.2f} ({p['duration_days']} días) — {p['description']}"
        for p in plans
    ])
    
    context = {
        "plans": plans,
        "plans_text": plans_text
    }
    
    prompt = f"""Eres la recepcionista de {GYM_NAME}.
Un cliente nuevo está pidiendo informes sobre precios y planes.

Planes disponibles:
{plans_text}

Responde de forma amable presentando los planes con sus precios.
Menciona que pueden pasar al gimnasio para conocer las instalaciones.
Sé breve y usa un tono amigable. Responde en español."""

    response = llm.invoke(prompt)
    return {
        "response": response.strip(),
        "context": context,
        "rule_applied": "R1: cliente_nuevo → mostrar_planes",
        "requires_human": False
    }

def handle_consulta_membresia(message: str, phone: str = None) -> dict:
    """
    Maneja la intención CONSULTA_MEMBRESIA.
    Busca al cliente por teléfono y consulta su membresía.
    """
    # Si no tenemos teléfono, pedirlo
    if not phone:
        phone = extract_phone(message)
    
    if not phone:
        return {
            "response": f"¡Hola! Para consultar tu membresía necesito tu número de teléfono de 10 dígitos con el que estás registrado en {GYM_NAME}. ¿Me lo puedes proporcionar?",
            "context": {"waiting_for": "phone"},
            "rule_applied": "R2a: consulta_membresia → solicitar_telefono",
            "requires_human": False
        }
    
    # Buscar cliente
    member = get_member_by_phone(phone)
    if not member:
        return {
            "response": f"No encontré ningún socio registrado con el número {phone} en nuestro sistema. ¿Podrías verificar el número? Si eres cliente nuevo, con gusto te doy informes sobre nuestros planes.",
            "context": {"phone": phone, "found": False},
            "rule_applied": "R2b: telefono_no_encontrado → sugerir_verificar",
            "requires_human": False
        }
    
    # Buscar membresía activa
    membership = get_active_membership(member['id'])
    
    if not membership:
        prompt = f"""Eres la recepcionista de {GYM_NAME}.
El socio {member['name']} no tiene membresía activa en este momento.
Dile amablemente que su membresía no está activa y ofrécele opciones para renovar.
Menciona que puede pasar al gimnasio o contactar al staff para renovar. Responde en español."""
        response = llm.invoke(prompt)
        return {
            "response": response.strip(),
            "context": {"member": member, "membership": None},
            "rule_applied": "R2c: membresia_inactiva → ofrecer_renovacion",
            "requires_human": False
        }
    
    days = days_until_expiry(membership['end_date'])
    
    # Regla: membresía por vencer (menos de 7 días)
    if days <= 7 and days >= 0:
        rule = "R2d: membresia_por_vencer → recordatorio_urgente"
        urgency = f"⚠️ Tu membresía vence en {days} días"
    elif days < 0:
        rule = "R2c: membresia_vencida → ofrecer_renovacion"
        urgency = "❌ Tu membresía está vencida"
    else:
        rule = "R2e: membresia_activa → mostrar_estatus"
        urgency = f"✅ Tu membresía está activa por {days} días más"

    prompt = f"""Eres la recepcionista de {GYM_NAME}.
Información del socio:
- Nombre: {member['name']}
- Plan actual: {membership['plan_name']}
- Fecha de vencimiento: {membership['end_date']}
- Días restantes: {days}
- Estado: {urgency}

Informa al socio sobre el estado de su membresía de forma amable.
Si está por vencer o vencida, invítalo a renovar. Responde en español."""

    response = llm.invoke(prompt)
    return {
        "response": response.strip(),
        "context": {
            "member": member,
            "membership": membership,
            "days_remaining": days
        },
        "rule_applied": rule,
        "requires_human": False
    }

def handle_problema(message: str, intent: str) -> dict:
    """
    Maneja PROBLEMA_APP y PROBLEMA_ACCESO.
    Registra el problema y prepara datos para el Agente 2.
    """
    if intent == "PROBLEMA_APP":
        rule = "R3a: problema_app → registrar_ticket_normal"
        priority = "NORMAL"
        tipo = "problema con la aplicación"
    else:
        rule = "R3b: problema_acceso → registrar_ticket_alta_prioridad"
        priority = "ALTA"
        tipo = "problema de acceso al gimnasio"

    prompt = f"""Eres la recepcionista de {GYM_NAME}.
Un socio reporta un {tipo}.
Mensaje: "{message}"

Responde con empatía, dile que registrarás su caso y que el staff
le dará seguimiento a la brevedad. Si es problema de acceso,
dile que es prioritario y se atenderá de inmediato. Responde en español."""

    response = llm.invoke(prompt)
    return {
        "response": response.strip(),
        "context": {
            "issue_type": intent,
            "description": message,
            "priority": priority
        },
        "rule_applied": rule,
        "requires_human": True
    }

def handle_otro(message: str) -> dict:
    """Maneja intenciones no reconocidas."""
    prompt = f"""Eres la recepcionista de {GYM_NAME}.
Un cliente envió este mensaje: "{message}"

No estás segura de cómo ayudarle exactamente.
Responde amablemente, di que puedes ayudarle con:
informes de precios, consultas de membresía, problemas con la app
o problemas de acceso. Pregunta en qué le puedes ayudar. Responde en español."""

    response = llm.invoke(prompt)
    return {
        "response": response.strip(),
        "context": {"original_message": message},
        "rule_applied": "R0: intencion_desconocida → pedir_clarificacion",
        "requires_human": False
    }

def process_message(message: str, phone: str = None) -> dict:
    """
    Función principal del Agente 1.
    Recibe mensaje del cliente y devuelve respuesta + metadata.
    """
    print(f"\n[Agente 1] 📨 Mensaje recibido: '{message}'")

    # 1. Detectar intención
    intent_result = detect_intent(message)
    intent = intent_result.get('intent', 'OTRO')
    confidence = intent_result.get('confidence', 'BAJA')
    extracted = intent_result.get('extracted_data', {})

    # Si el mensaje tiene teléfono, extraerlo
    if not phone and extracted.get('phone'):
        phone = extracted['phone']

    print(f"[Agente 1] 🎯 Intención: {intent} (confianza: {confidence})")

    # 2. Enrutar según intención
    if intent == "NUEVO_INFORME":
        result = handle_nuevo_informe()
    elif intent == "CONSULTA_MEMBRESIA":
        result = handle_consulta_membresia(message, phone)
    elif intent in ["PROBLEMA_APP", "PROBLEMA_ACCESO"]:
        result = handle_problema(message, intent)
    else:
        result = handle_otro(message)

    # 3. Agregar metadata
    result["intent"] = intent
    result["confidence"] = confidence
    result["extracted_data"] = extracted
    result["original_message"] = message

    print(f"[Agente 1] 📋 Regla aplicada: {result['rule_applied']}")
    print(f"[Agente 1] 🚨 Requiere humano: {result['requires_human']}")

    return result