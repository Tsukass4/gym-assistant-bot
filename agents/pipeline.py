from agents.agent1 import process_message
from agents.agent2 import apply_rules
from agents.agent3 import process

def run_pipeline(message: str, phone: str = None) -> dict:
    """
    Ejecuta el pipeline completo de los tres agentes.
    Recibe mensaje del cliente y devuelve respuesta + resumen del staff.
    """
    print("\n" + "━" * 55)
    print("🏋️  GYMBOT — PIPELINE INICIADO")
    print("━" * 55)

    # Agente 1 — Recepcionista virtual
    agent1_output = process_message(message, phone)

    # Agente 2 — Motor de reglas
    agent2_output = apply_rules(agent1_output)

    # Agente 3 — Supervisor
    agent3_output = process(agent1_output, agent2_output)

    print("\n" + "━" * 55)
    print("✅ PIPELINE COMPLETADO")
    print("━" * 55)

    return {
        "message": message,
        "bot_response": agent1_output.get("response", ""),
        "intent": agent1_output.get("intent", "OTRO"),
        "rule_applied": agent2_output.get("rule_applied", "R0"),
        "rule_description": agent2_output.get("rule_description", ""),
        "alert_level": agent2_output.get("alert_level", "GREEN"),
        "requires_human": agent2_output.get("requires_human", False),
        "explanation": agent3_output.get("explanation", ""),
        "timestamp": agent3_output.get("timestamp", ""),
        "decision": agent2_output.get("decision", ""),
    }