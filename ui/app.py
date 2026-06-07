import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.pipeline import run_pipeline
from database.db import get_recent_tickets, get_member_stats

# ─── CONFIGURACIÓN DE PÁGINA ───────────────────────────
st.set_page_config(
    page_title="GymBot — The Field",
    page_icon="🏋️",
    layout="wide"
)

# ─── ESTILOS ───────────────────────────────────────────
st.markdown("""
<style>
.alert-green {
    background-color: #d4edda;
    border-left: 4px solid #28a745;
    padding: 10px 15px;
    border-radius: 5px;
    margin: 5px 0;
}
.alert-yellow {
    background-color: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 10px 15px;
    border-radius: 5px;
    margin: 5px 0;
}
.alert-red {
    background-color: #f8d7da;
    border-left: 4px solid #dc3545;
    padding: 10px 15px;
    border-radius: 5px;
    margin: 5px 0;
}
.rule-badge {
    background-color: #e9ecef;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-family: monospace;
}
.stat-box {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    text-align: center;
    border: 1px solid #dee2e6;
}
</style>
""", unsafe_allow_html=True)

# ─── INICIALIZAR ESTADO ────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ─── LAYOUT: DOS COLUMNAS ──────────────────────────────
col_chat, col_staff = st.columns([3, 2])

# ══════════════════════════════════════════════════════
# COLUMNA IZQUIERDA — CHAT
# ══════════════════════════════════════════════════════
with col_chat:
    st.markdown("## 🏋️ GymBot — The Field")
    st.markdown("*Tu asistente virtual de gimnasio*")
    st.divider()

    # Mostrar historial de mensajes
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Mensaje de bienvenida si no hay mensajes
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.write("¡Hola! Soy GymBot 🤖, tu asistente virtual.")
            st.write("Puedo ayudarte con:\n\n• 💪 Precios y planes\n• 🏅 Consulta de membresía\n• 📱 Problemas con la app\n• 🚪 Problemas de acceso\n\n¿En qué te puedo ayudar hoy?")

    # Input del usuario
    if prompt := st.chat_input("Escribe tu mensaje aquí..."):

        # Agregar mensaje del usuario
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.write(prompt)

        # Correr el pipeline
        with st.chat_message("assistant"):
            with st.spinner("GymBot está procesando..."):
                result = run_pipeline(prompt)
                st.session_state.last_result = result

            st.write(result["bot_response"])

        # Agregar respuesta del bot
        st.session_state.messages.append({
            "role": "assistant",
            "content": result["bot_response"]
        })

        st.rerun()

# ══════════════════════════════════════════════════════
# COLUMNA DERECHA — PANEL DEL STAFF
# ══════════════════════════════════════════════════════
with col_staff:
    st.markdown("## 👥 Panel del Staff")
    st.divider()

    # ── Estadísticas generales ──────────────────────
    st.markdown("### 📊 Estadísticas")
    try:
        stats = get_member_stats()
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Total socios", stats["total_members"])
            st.metric("Activos", stats["active_memberships"])
        with c2:
            st.metric("Vencidos", stats["expired_memberships"])
            st.metric("Tickets abiertos", stats["open_tickets"])
    except:
        st.info("Cargando estadísticas...")

    st.divider()

    # ── Última interacción ──────────────────────────
    st.markdown("### 🤖 Última interacción")

    if st.session_state.last_result:
        result = st.session_state.last_result
        alert = result.get("alert_level", "GREEN")

        # Badge de alerta con color
        if alert == "GREEN":
            st.markdown(
                '<div class="alert-green">✅ Sin alertas — Todo en orden</div>',
                unsafe_allow_html=True
            )
        elif alert == "YELLOW":
            st.markdown(
                '<div class="alert-yellow">⚠️ Requiere atención del staff</div>',
                unsafe_allow_html=True
            )
        elif alert == "RED":
            st.markdown(
                '<div class="alert-red">🚨 URGENTE — Atención inmediata</div>',
                unsafe_allow_html=True
            )

        st.markdown(f"**Intención:** `{result.get('intent', '-')}`")
        st.markdown(
            f"**Regla aplicada:** "
            f"<span class='rule-badge'>{result.get('rule_applied', '-')}</span>",
            unsafe_allow_html=True
        )
        st.markdown(f"**Decisión:** {result.get('decision', '-')}")
        st.markdown(f"**Requiere humano:** {'⚠️ Sí' if result.get('requires_human') else '✅ No'}")

        st.markdown("**💡 Explicación del Agente 3:**")
        st.info(result.get("explanation", "Sin explicación disponible"))

    else:
        st.markdown("*Esperando primera interacción...*")

    st.divider()

    # ── Tickets recientes ───────────────────────────
    st.markdown("### 🎫 Tickets recientes")
    try:
        tickets = get_recent_tickets(5)
        if tickets:
            for t in tickets:
                priority_icon = "🔴" if t["priority"] == "ALTA" else "🟡"
                st.markdown(
                    f"{priority_icon} **{t['issue_type']}** — "
                    f"{t['description'][:50]}..."
                    if len(t.get('description', '')) > 50
                    else f"{priority_icon} **{t['issue_type']}** — {t.get('description', '')}"
                )
        else:
            st.markdown("*No hay tickets abiertos*")
    except:
        st.info("Cargando tickets...")

    st.divider()

    # ── Botón limpiar chat ──────────────────────────
    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_result = None
        st.rerun()