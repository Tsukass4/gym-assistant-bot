from langchain_community.llms import Ollama
from config import OLLAMA_MODEL, OLLAMA_BASE_URL, GYM_NAME, AGENT1_SYSTEM_PROMPT
from database.db import (
    get_member_by_phone,
    get_active_membership,
    get_all_plans,
    days_until_expiry
)
import json

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
    import re
    phones = re.findall(r'\b\d{10}\b', message)
    return phones[0] if phones else None

def handle_nuevo_informe() -> dict:
    plans = get_all_plans()
    plans_text = "\n".join([
        f"- {p['name']}: ${p['price']:.2f} ({p['duration_days']} días) — {p['description']}"
        for p in plans
    ])

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
        "context": {"plans": plans, "plans_text": plans_text},
        "rule_applied": "R1: cliente_nuevo → mostrar_planes",
        "requires_human": False
    }

def handle_consulta_membresia(message: str, phone: str = None) -> dict:
    if not phone:
        phone = extract_phone(message)

    if not phone:
        return {
            "response": f"¡Hola! Para consultar tu membresía necesito tu número de teléfono de 10 dígitos con el que estás registrado en {GYM_NAME}. ¿Me lo puedes proporcionar?",
            "context": {"waiting_for": "phone"},
            "rule_applied": "R2a: consulta_membresia → solicitar_telefono",
            "requires_human": False
        }

    member = get_member_by_phone(phone)
    if not member:
        return {
            "response": f"No encontré ningún socio registrado con el número {phone} en nuestro sistema. ¿Podrías verificar el número? Si eres cliente nuevo, con gusto te doy informes sobre nuestros planes.",
            "context": {"phone": phone, "found": False},
            "rule_applied": "R2b: telefono_no_encontrado → sugerir_verificar",
            "requires_human": False
        }

    membership = get_active_membership(member['id'])

    if not membership:
        return {
            "response": f"Hola {member['name']} 👋\n\nRevisé tu cuenta y actualmente **no tienes una membresía activa** en {GYM_NAME}.\n\nEstos son nuestros planes para renovar:\n💪 Mensual: $350\n📅 Trimestral: $900\n🗓️ Semestral: $1,600\n🏆 Anual: $2,800\n\nPuedes pasar al gimnasio o escribirnos para renovar. ¡Te esperamos!",
            "context": {"member": member, "membership": None},
            "rule_applied": "R2c: membresia_inactiva → ofrecer_renovacion",
            "requires_human": False
        }

    days = days_until_expiry(membership['end_date'])

    if days < 0:
        rule = "R2c: membresia_vencida → ofrecer_renovacion"
        response = (
            f"Hola {member['name']} 👋\n\n"
            f"Tu membresía **{membership['plan_name']}** venció el {membership['end_date']}. "
            f"❌ Ya no está activa.\n\n"
            f"¿Te gustaría renovar? Puedes pasar al gimnasio o escribirnos. ¡Te esperamos!"
        )
    elif days <= 7:
        rule = "R2d: membresia_por_vencer → recordatorio_urgente"
        response = (
            f"Hola {member['name']} 👋\n\n"
            f"⚠️ Tu membresía **{membership['plan_name']}** vence en **{days} días** "
            f"(el {membership['end_date']}).\n\n"
            f"Te recomendamos renovar pronto para no perder tu acceso. "
            f"¡Pasa al gimnasio o escríbenos!"
        )
    else:
        rule = "R2e: membresia_activa → mostrar_estatus"
        response = (
            f"Hola {member['name']} 👋\n\n"
            f"✅ Tu membresía está **activa**.\n\n"
            f"📋 Plan: {membership['plan_name']}\n"
            f"📅 Vence el: {membership['end_date']}\n"
            f"⏳ Días restantes: {days}\n\n"
            f"¡Sigue entrenando duro! 💪"
        )

    return {
        "response": response,
        "context": {
            "member": member,
            "membership": membership,
            "days_remaining": days
        },
        "rule_applied": rule,
        "requires_human": False
    }

def handle_problema(message: str, intent: str) -> dict:
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

SALUDOS = [
    "hola", "buenos dias", "buenas tardes", "buenas noches",
    "buen dia", "buenas", "hey", "hi", "hello", "que tal",
    "como estan"
]

PALABRAS_INFORME = [
    "precio", "precios", "costo", "costos", "plan", "planes",
    "informes", "informe", "mensualidad", "anual", "trimestral",
    "semestral", "inscripcion", "inscripción", "cuanto cuesta",
    "cuánto cuesta", "cuanto vale", "información", "informacion",
    "quiero saber", "tienen", "que planes", "qué planes"
]

PALABRAS_APP = [
    "app", "aplicacion", "aplicación", "rutinas", "rutina",
    "no carga", "no abre", "error", "no funciona la app",
    "no puedo ver", "no me deja ver"
]

PALABRAS_ACCESO = [
    "torniquete", "no puedo entrar", "no me deja entrar",
    "acceso denegado", "no me abre", "puerta", "entrada",
    "no entra", "codigo no funciona", "código no funciona"
]

def normalizar(text: str) -> str:
    """Normaliza el texto para comparación."""
    t = text.lower().strip()
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ü","u")]:
        t = t.replace(a, b)
    return t

def is_greeting(message: str) -> bool:
    clean = normalizar(message)
    return any(clean == s or clean.startswith(s + " ") for s in SALUDOS)

def detect_intent_manual(message: str) -> str | None:
    """
    Detecta intención con reglas manuales antes de llamar al LLM.
    Devuelve la intención si la detecta, None si no está seguro.
    """
    clean = normalizar(message)

    # Saludos simples
    if is_greeting(message):
        return "SALUDO"

    # Problema de acceso físico
    if any(p in clean for p in PALABRAS_ACCESO):
        return "PROBLEMA_ACCESO"

    # Problema con la app
    if any(p in clean for p in PALABRAS_APP):
        return "PROBLEMA_APP"

    # Informes de precios
    if any(p in clean for p in PALABRAS_INFORME):
        return "NUEVO_INFORME"

    # Teléfono de 10 dígitos solo
    import re
    if re.fullmatch(r'\d{10}', clean.replace(" ", "")):
        return "CONSULTA_MEMBRESIA"

    return None  # No detectado, usar LLM

def process_message(message: str, phone: str = None) -> dict:
    print(f"\n[Agente 1] 📨 Mensaje recibido: '{message}'")

    # Intentar detección manual primero
    intent_manual = detect_intent_manual(message)

    if intent_manual == "SALUDO":
        print(f"[Agente 1] 🎯 Intención: OTRO (saludo manual)")
        return {
            "intent": "OTRO",
            "confidence": "ALTA",
            "extracted_data": {"phone": None, "name": None, "problem_description": None},
            "original_message": message,
            "response": f"¡Hola! Bienvenido a {GYM_NAME} 👋 ¿En qué te puedo ayudar hoy?\n\n💪 **Precios y planes**\n\n🏅 **Consulta de membresía**\n\n📱 **Problemas con la app**\n\n🚪 **Problemas de acceso**",
            "context": {},
            "rule_applied": "R0: saludo_detectado → bienvenida",
            "requires_human": False
        }

    elif intent_manual == "NUEVO_INFORME":
        print(f"[Agente 1] 🎯 Intención: NUEVO_INFORME (regla manual)")
        result = handle_nuevo_informe()
        result["intent"] = "NUEVO_INFORME"
        result["confidence"] = "ALTA"
        result["extracted_data"] = {"phone": None, "name": None, "problem_description": None}
        result["original_message"] = message
        print(f"[Agente 1] 📋 Regla aplicada: {result['rule_applied']}")
        return result

    elif intent_manual == "PROBLEMA_APP":
        print(f"[Agente 1] 🎯 Intención: PROBLEMA_APP (regla manual)")
        result = handle_problema(message, "PROBLEMA_APP")
        result["intent"] = "PROBLEMA_APP"
        result["confidence"] = "ALTA"
        result["extracted_data"] = {"phone": None, "name": None, "problem_description": message}
        result["original_message"] = message
        print(f"[Agente 1] 📋 Regla aplicada: {result['rule_applied']}")
        return result

    elif intent_manual == "PROBLEMA_ACCESO":
        print(f"[Agente 1] 🎯 Intención: PROBLEMA_ACCESO (regla manual)")
        result = handle_problema(message, "PROBLEMA_ACCESO")
        result["intent"] = "PROBLEMA_ACCESO"
        result["confidence"] = "ALTA"
        result["extracted_data"] = {"phone": None, "name": None, "problem_description": message}
        result["original_message"] = message
        print(f"[Agente 1] 📋 Regla aplicada: {result['rule_applied']}")
        return result

    elif intent_manual == "CONSULTA_MEMBRESIA":
        print(f"[Agente 1] 🎯 Intención: CONSULTA_MEMBRESIA (regla manual)")
        result = handle_consulta_membresia(message, message.strip())
        result["intent"] = "CONSULTA_MEMBRESIA"
        result["confidence"] = "ALTA"
        result["extracted_data"] = {"phone": message.strip(), "name": None, "problem_description": None}
        result["original_message"] = message
        print(f"[Agente 1] 📋 Regla aplicada: {result['rule_applied']}")
        return result

    # Si no detectó nada manualmente, usar el LLM
    print(f"[Agente 1] 🤖 Usando LLM para detectar intención...")
    intent_result = detect_intent(message)
    intent = intent_result.get('intent', 'OTRO')
    confidence = intent_result.get('confidence', 'BAJA')
    extracted = intent_result.get('extracted_data', {})

    if not phone and extracted.get('phone'):
        phone = extracted['phone']

    print(f"[Agente 1] 🎯 Intención: {intent} (confianza: {confidence})")

    if intent == "NUEVO_INFORME":
        result = handle_nuevo_informe()
    elif intent == "CONSULTA_MEMBRESIA":
        result = handle_consulta_membresia(message, phone)
    elif intent in ["PROBLEMA_APP", "PROBLEMA_ACCESO"]:
        result = handle_problema(message, intent)
    else:
        result = handle_otro(message)

    result["intent"] = intent
    result["confidence"] = confidence
    result["extracted_data"] = extracted
    result["original_message"] = message

    print(f"[Agente 1] 📋 Regla aplicada: {result['rule_applied']}")
    print(f"[Agente 1] 🚨 Requiere humano: {result['requires_human']}")

    return result