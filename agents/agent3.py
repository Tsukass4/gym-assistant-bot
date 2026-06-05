from langchain_community.llms import Ollama
from config import OLLAMA_MODEL, OLLAMA_BASE_URL, GYM_NAME
from database.db import log_conversation
from datetime import datetime

llm = Ollama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.2
)

ALERT_LABELS = {
    "GREEN":  "✅ Sin alertas",
    "YELLOW": "⚠️  Requiere atención",
    "RED":    "🚨 URGENTE"
}

def generate_explanation(agent1_output: dict, agent2_output: dict) -> str:
    intent = agent1_output.get("intent", "OTRO")
    rule = agent2_output.get("rule_applied", "R0")
    rule_desc = agent2_output.get("rule_description", "")
    explanation = agent2_output.get("explanation", "")
    decision = agent2_output.get("decision", "")
    alert = agent2_output.get("alert_level", "GREEN")
    message = agent1_output.get("original_message", "")

    prompt = f"""Eres el supervisor de un gimnasio llamado {GYM_NAME}.
Resume en 3 líneas lo que ocurrió en esta interacción.

- Mensaje del cliente: "{message}"
- Intención detectada: {intent}
- Regla aplicada: {rule} ({rule_desc})
- Decisión: {decision}
- Explicación: {explanation}
- Alerta: {alert}

Formato exacto:
Línea 1: Qué solicitó el cliente
Línea 2: Qué regla se aplicó y por qué
Línea 3: Qué acción se tomó y si requiere seguimiento

Responde en español, máximo 3 líneas."""

    response = llm.invoke(prompt)
    return response.strip()

def build_summary(agent1_output: dict, agent2_output: dict,
                  explanation: str) -> dict:
    intent = agent1_output.get("intent", "OTRO")
    rule = agent2_output.get("rule_applied", "R0")
    rule_desc = agent2_output.get("rule_description", "")
    alert = agent2_output.get("alert_level", "GREEN")
    requires_human = agent2_output.get("requires_human", False)
    message = agent1_output.get("original_message", "")
    response = agent1_output.get("initial_response", "")
    extracted = agent1_output.get("extracted_data", {})

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "gym_name": GYM_NAME,
        "original_message": message,
        "intent_detected": intent,
        "rule_applied": rule,
        "rule_description": rule_desc,
        "decision": agent2_output.get("decision", ""),
        "bot_response": response,
        "alert_level": alert,
        "alert_label": ALERT_LABELS.get(alert, "✅ Sin alertas"),
        "requires_human": requires_human,
        "explanation": explanation,
        "member_phone": extracted.get("phone"),
    }

def save_to_db(summary: dict):
    log_conversation(
        member_phone=summary.get("member_phone") or "desconocido",
        intent=summary["intent_detected"],
        rule_applied=f"{summary['rule_applied']}: {summary['rule_description']}",
        response=summary["bot_response"],
        required_human=summary["requires_human"]
    )

def print_staff_panel(summary: dict):
    print("\n" + "═" * 55)
    print("       PANEL DEL STAFF — AGENTE 3 SUPERVISOR")
    print("═" * 55)
    print(f"🕐 Timestamp:     {summary['timestamp']}")
    print(f"📨 Mensaje:       {summary['original_message']}")
    print(f"🎯 Intención:     {summary['intent_detected']}")
    print(f"📋 Regla:         {summary['rule_applied']} — {summary['rule_description']}")
    print(f"⚙️  Decisión:      {summary['decision']}")
    print(f"🚦 Alerta:        {summary['alert_label']}")
    print(f"🚨 Humano:        {'SÍ ⚠️' if summary['requires_human'] else 'No'}")
    print(f"\n💡 EXPLICACIÓN:")
    print(f"   {summary['explanation']}")
    print("═" * 55)

def process(agent1_output: dict, agent2_output: dict) -> dict:
    print(f"\n[Agente 3] 🔍 Generando resumen explicable...")

    explanation = generate_explanation(agent1_output, agent2_output)
    summary = build_summary(agent1_output, agent2_output, explanation)
    save_to_db(summary)
    print(f"[Agente 3] 💾 Log guardado en BD")
    print_staff_panel(summary)

    return summary