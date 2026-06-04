from database.db import (
    create_support_ticket,
    get_member_by_phone,
    get_active_membership,
    get_all_plans,
    days_until_expiry
)
from datetime import date

# ─────────────────────────────────────────
# BASE DE REGLAS DEL GIMNASIO
# ─────────────────────────────────────────

RULES = {
    "R1": "cliente_nuevo → mostrar_planes_disponibles",
    "R2a": "consulta_membresia → solicitar_telefono",
    "R2b": "telefono_no_encontrado → sugerir_verificar",
    "R2c": "membresia_vencida → ofrecer_renovacion",
    "R2d": "membresia_por_vencer_7_dias → recordatorio_urgente",
    "R2e": "membresia_activa → mostrar_estatus_normal",
    "R2f": "cliente_6_meses_plan_mensual → sugerir_plan_anual",
    "R3a": "problema_app → crear_ticket_normal",
    "R3b": "problema_acceso → crear_ticket_alta_prioridad",
    "R0":  "intencion_desconocida → pedir_clarificacion",
}

def apply_rules(agent1_output: dict) -> dict:
    """
    Función principal del Agente 2.
    Recibe el output del Agente 1 y aplica las reglas de negocio.
    Devuelve decisión + regla aplicada + datos para el Agente 3.
    """
    intent = agent1_output.get("intent", "OTRO")
    context = agent1_output.get("context", {})
    extracted = agent1_output.get("extracted_data", {})
    message = agent1_output.get("original_message", "")

    print(f"\n[Agente 2] ⚙️  Procesando intención: {intent}")

    # ── REGLA R1: Cliente nuevo pidiendo informes ──────────────
    if intent == "NUEVO_INFORME":
        plans = context.get("plans", [])
        
        # Regla extra: si pregunta por más de un plan → destacar anual
        suggest_annual = len(plans) > 1
        
        result = {
            "rule_applied": "R1",
            "rule_description": RULES["R1"],
            "decision": "mostrar_planes",
            "data": {
                "plans": plans,
                "suggest_annual": suggest_annual,
                "discount_message": "¡El plan anual te ahorra $1,400 vs pagar mensual!" if suggest_annual else None
            },
            "requires_human": False,
            "priority": "NORMAL",
            "alert_level": "GREEN",
            "explanation": "Se detectó un cliente nuevo. Se mostraron todos los planes disponibles. Se destacó el plan anual por ser el de mayor ahorro."
        }

    # ── REGLAS R2: Consulta de membresía ──────────────────────
    elif intent == "CONSULTA_MEMBRESIA":
        member = context.get("member")
        membership = context.get("membership")
        waiting_for = context.get("waiting_for")

        # R2a: No tenemos teléfono aún
        if waiting_for == "phone":
            result = {
                "rule_applied": "R2a",
                "rule_description": RULES["R2a"],
                "decision": "esperar_telefono",
                "data": {},
                "requires_human": False,
                "priority": "NORMAL",
                "alert_level": "GREEN",
                "explanation": "El cliente consulta su membresía pero no proporcionó teléfono. Se solicitó el número para buscar en la base de datos."
            }

        # R2b: Teléfono no encontrado en BD
        elif member is None and not waiting_for:
            result = {
                "rule_applied": "R2b",
                "rule_description": RULES["R2b"],
                "decision": "telefono_no_encontrado",
                "data": {"phone": extracted.get("phone")},
                "requires_human": False,
                "priority": "NORMAL",
                "alert_level": "GREEN",
                "explanation": "Se buscó el teléfono en la base de datos y no se encontró ningún socio registrado con ese número."
            }

        # R2c: Membresía vencida
        elif member and not membership:
            result = {
                "rule_applied": "R2c",
                "rule_description": RULES["R2c"],
                "decision": "ofrecer_renovacion",
                "data": {"member": member},
                "requires_human": False,
                "priority": "NORMAL",
                "alert_level": "YELLOW",
                "explanation": f"El socio {member['name']} no tiene membresía activa. Se ofreció renovación con los planes disponibles."
            }

        elif member and membership:
            days = days_until_expiry(membership["end_date"])

            # R2d: Membresía por vencer en 7 días o menos
            if 0 <= days <= 7:
                result = {
                    "rule_applied": "R2d",
                    "rule_description": RULES["R2d"],
                    "decision": "recordatorio_urgente",
                    "data": {
                        "member": member,
                        "membership": membership,
                        "days_remaining": days
                    },
                    "requires_human": False,
                    "priority": "MEDIA",
                    "alert_level": "YELLOW",
                    "explanation": f"Membresía del socio {member['name']} vence en {days} días. Se activó recordatorio urgente de renovación."
                }

            # R2f: Cliente con más de 6 meses en plan mensual → sugerir anual
            elif days > 7:
                join_date = member.get("join_date", "")
                months_member = 0
                if join_date:
                    try:
                        from datetime import datetime
                        jd = datetime.strptime(join_date, "%Y-%m-%d").date()
                        months_member = (date.today() - jd).days // 30
                    except:
                        months_member = 0

                if months_member >= 6 and membership.get("plan_id") == 1:
                    plans = get_all_plans()
                    annual = next((p for p in plans if p["name"] == "Anual"), None)
                    result = {
                        "rule_applied": "R2f",
                        "rule_description": RULES["R2f"],
                        "decision": "sugerir_plan_anual",
                        "data": {
                            "member": member,
                            "membership": membership,
                            "days_remaining": days,
                            "months_as_member": months_member,
                            "annual_plan": annual
                        },
                        "requires_human": False,
                        "priority": "NORMAL",
                        "alert_level": "GREEN",
                        "explanation": f"Socio {member['name']} lleva {months_member} meses con plan mensual. Se sugirió cambio a plan anual para mayor ahorro."
                    }
                else:
                    # R2e: Membresía activa normal
                    result = {
                        "rule_applied": "R2e",
                        "rule_description": RULES["R2e"],
                        "decision": "mostrar_estatus",
                        "data": {
                            "member": member,
                            "membership": membership,
                            "days_remaining": days
                        },
                        "requires_human": False,
                        "priority": "NORMAL",
                        "alert_level": "GREEN",
                        "explanation": f"Membresía del socio {member['name']} está activa con {days} días restantes. Sin alertas."
                    }
            else:
                # Membresía vencida (days < 0)
                result = {
                    "rule_applied": "R2c",
                    "rule_description": RULES["R2c"],
                    "decision": "ofrecer_renovacion",
                    "data": {"member": member, "membership": membership},
                    "requires_human": False,
                    "priority": "NORMAL",
                    "alert_level": "YELLOW",
                    "explanation": f"Membresía del socio {member['name']} está vencida. Se ofreció renovación."
                }
        else:
            result = {
                "rule_applied": "R2a",
                "rule_description": RULES["R2a"],
                "decision": "esperar_telefono",
                "data": {},
                "requires_human": False,
                "priority": "NORMAL",
                "alert_level": "GREEN",
                "explanation": "No se pudo determinar el estado de la membresía. Se solicitó teléfono."
            }

    # ── REGLA R3a: Problema con la app ────────────────────────
    elif intent == "PROBLEMA_APP":
        issue = context.get("description", message)
        member_id = None
        phone = extracted.get("phone")
        if phone:
            member = get_member_by_phone(phone)
            if member:
                member_id = member["id"]

        create_support_ticket(
            member_id=member_id,
            issue_type="PROBLEMA_APP",
            description=issue,
            priority="NORMAL"
        )

        result = {
            "rule_applied": "R3a",
            "rule_description": RULES["R3a"],
            "decision": "ticket_creado",
            "data": {
                "issue_type": "PROBLEMA_APP",
                "description": issue,
                "priority": "NORMAL"
            },
            "requires_human": True,
            "priority": "NORMAL",
            "alert_level": "YELLOW",
            "explanation": "Se detectó problema con la aplicación. Se creó ticket de soporte con prioridad NORMAL. Staff notificado para seguimiento."
        }

    # ── REGLA R3b: Problema de acceso ─────────────────────────
    elif intent == "PROBLEMA_ACCESO":
        issue = context.get("description", message)
        member_id = None
        phone = extracted.get("phone")
        if phone:
            member = get_member_by_phone(phone)
            if member:
                member_id = member["id"]

        create_support_ticket(
            member_id=member_id,
            issue_type="PROBLEMA_ACCESO",
            description=issue,
            priority="ALTA"
        )

        result = {
            "rule_applied": "R3b",
            "rule_description": RULES["R3b"],
            "decision": "ticket_urgente_creado",
            "data": {
                "issue_type": "PROBLEMA_ACCESO",
                "description": issue,
                "priority": "ALTA"
            },
            "requires_human": True,
            "priority": "ALTA",
            "alert_level": "RED",
            "explanation": "Se detectó problema de acceso físico al gimnasio. Se creó ticket URGENTE de prioridad ALTA. Staff debe atender de inmediato."
        }

    # ── REGLA R0: Intención desconocida ───────────────────────
    else:
        result = {
            "rule_applied": "R0",
            "rule_description": RULES["R0"],
            "decision": "pedir_clarificacion",
            "data": {},
            "requires_human": False,
            "priority": "NORMAL",
            "alert_level": "GREEN",
            "explanation": "No se pudo clasificar la intención del mensaje. Se pidió al cliente que aclare su consulta."
        }

    print(f"[Agente 2] 📋 Regla aplicada: {result['rule_applied']} — {result['rule_description']}")
    print(f"[Agente 2] 🚦 Nivel de alerta: {result['alert_level']}")
    print(f"[Agente 2] 💡 Explicación: {result['explanation']}")

    return result