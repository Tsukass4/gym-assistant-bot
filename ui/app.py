import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.pipeline import run_pipeline
from database.db import get_recent_tickets, get_member_stats, get_conversation_logs

# ─── CONFIGURACIÓN ─────────────────────────────────────
st.set_page_config(
    page_title="GymBot — The Field",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── ESTILOS ───────────────────────────────────────────
st.markdown("""
<style>
/* Fondo general */
.stApp { background-color: #F8F9FA; }

/* Header del gym */
.gym-header {
    background: linear-gradient(135deg, #1F3864, #2E74B5);
    color: white;
    padding: 20px 25px;
    border-radius: 12px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 15px;
}
.gym-header h1 { margin: 0; font-size: 24px; color: white; }
.gym-header p  { margin: 0; font-size: 13px; opacity: 0.85; color: white; }

/* Alertas */
.alert-green {
    background: #D4EDDA;
    border-left: 5px solid #28A745;
    padding: 10px 15px;
    border-radius: 6px;
    color: #155724;
    font-weight: 500;
}
.alert-yellow {
    background: #FFF3CD;
    border-left: 5px solid #FFC107;
    padding: 10px 15px;
    border-radius: 6px;
    color: #856404;
    font-weight: 500;
}
.alert-red {
    background: #F8D7DA;
    border-left: 5px solid #DC3545;
    padding: 10px 15px;
    border-radius: 6px;
    color: #721C24;
    font-weight: 500;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%   { opacity: 1; }
    50%  { opacity: 0.75; }
    100% { opacity: 1; }
}

/* Badge de regla */
.rule-badge {
    background: #E9ECEF;
    border: 1px solid #CED4DA;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-family: monospace;
    color: #495057;
    display: inline-block;
    margin: 4px 0;
}

/* Tarjeta de ticket */
.ticket-card {
    background: white;
    border: 1px solid #DEE2E6;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 13px;
}
.ticket-alta  { border-left: 4px solid #DC3545; }
.ticket-normal{ border-left: 4px solid #FFC107; }

/* Stats */
.stat-card {
    background: white;
    border: 1px solid #DEE2E6;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
}
.stat-number {
    font-size: 28px;
    font-weight: 700;
    color: #1F3864;
    line-height: 1;
}
.stat-label {
    font-size: 12px;
    color: #6C757D;
    margin-top: 4px;
}

/* Separador de sección */
.section-title {
    font-size: 13px;
    font-weight: 600;
    color: #6C757D;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 16px 0 8px;
}
</style>
""", unsafe_allow_html=True)

# ─── ESTADO ────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "conversation_count" not in st.session_state:
    st.session_state.conversation_count = 0

# ─── LAYOUT ────────────────────────────────────────────
col_chat, col_staff = st.columns([3, 2], gap="large")

# ══════════════════════════════════════════════════════
# COLUMNA IZQUIERDA — CHAT
# ══════════════════════════════════════════════════════
with col_chat:
    # Header
    st.markdown("""
    <div class="gym-header">
        <div style="font-size:36px">🏋️</div>
        <div>
            <h1>GymBot — The Field</h1>
            <p>Asistente virtual inteligente · Disponible 24/7</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Historial de mensajes
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown("¡Hola! Soy **GymBot**, tu asistente virtual. 👋")
                st.markdown("Puedo ayudarte con:")
                st.markdown("""
- 💪 **Precios y planes** del gimnasio
- 🏅 **Consulta de membresía** (necesito tu número)
- 📱 **Problemas con la app** de entrenamientos
- 🚪 **Problemas de acceso** al gimnasio
""")
                st.markdown("¿En qué te puedo ayudar hoy?")

        for msg in st.session_state.messages:
            avatar = "🤖" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input("Escribe tu mensaje aquí..."):
        st.session_state.messages.append({
            "role": "user", "content": prompt
        })
        st.session_state.conversation_count += 1

        with st.spinner("GymBot está procesando..."):
            result = run_pipeline(prompt)
            st.session_state.last_result = result

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["bot_response"]
        })
        st.rerun()

# ══════════════════════════════════════════════════════
# COLUMNA DERECHA — PANEL DEL STAFF
# ══════════════════════════════════════════════════════
with col_staff:
    st.markdown("### 👥 Panel del Staff")

    # ── Estadísticas ────────────────────────────────
    st.markdown('<div class="section-title">📊 Estadísticas del gimnasio</div>',
                unsafe_allow_html=True)
    try:
        stats = get_member_stats()
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats['total_members']}</div>
                <div class="stat-label">Socios</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number" style="color:#28A745">{stats['active_memberships']}</div>
                <div class="stat-label">Activos</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number" style="color:#FFC107">{stats['expired_memberships']}</div>
                <div class="stat-label">Vencidos</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number" style="color:#DC3545">{stats['open_tickets']}</div>
                <div class="stat-label">Tickets</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.info("Cargando estadísticas...")

    st.divider()

    # ── Última interacción ───────────────────────────
    st.markdown('<div class="section-title">🤖 Última interacción</div>',
                unsafe_allow_html=True)

    if st.session_state.last_result:
        result = st.session_state.last_result
        alert = result.get("alert_level", "GREEN")

        # Alerta con color
        if alert == "GREEN":
            st.markdown(
                '<div class="alert-green">✅ Sin alertas — Todo en orden</div>',
                unsafe_allow_html=True)
        elif alert == "YELLOW":
            st.markdown(
                '<div class="alert-yellow">⚠️ Requiere atención del staff</div>',
                unsafe_allow_html=True)
        elif alert == "RED":
            st.markdown(
                '<div class="alert-red">🚨 URGENTE — Atención inmediata requerida</div>',
                unsafe_allow_html=True)

        st.markdown(f"**Intención detectada:** `{result.get('intent', '-')}`")
        st.markdown(
            f"**Regla aplicada:** "
            f"<span class='rule-badge'>{result.get('rule_applied', '-')}</span>",
            unsafe_allow_html=True)
        st.markdown(f"**Decisión:** {result.get('decision', '-')}")
        st.markdown(
            f"**Requiere atención humana:** "
            f"{'🚨 **SÍ**' if result.get('requires_human') else '✅ No'}")

        st.markdown("**💡 Explicación del Agente 3:**")
        st.info(result.get("explanation", "Sin explicación"))

        st.markdown(f"<small style='color:#6C757D'>🕐 {result.get('timestamp','')}</small>",
                    unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:30px;color:#6C757D">
            <div style="font-size:40px">💬</div>
            <p>Esperando primera interacción...</p>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Tickets recientes ────────────────────────────
    st.markdown('<div class="section-title">🎫 Tickets recientes</div>',
                unsafe_allow_html=True)
    try:
        tickets = get_recent_tickets(4)
        if tickets:
            for t in tickets:
                css = "ticket-alta" if t["priority"] == "ALTA" else "ticket-normal"
                icon = "🔴" if t["priority"] == "ALTA" else "🟡"
                desc = t.get("description", "")
                desc_short = desc[:55] + "..." if len(desc) > 55 else desc
                st.markdown(f"""
                <div class="ticket-card {css}">
                    {icon} <strong>{t['issue_type']}</strong><br>
                    <span style="color:#6C757D;font-size:12px">{desc_short}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("*No hay tickets abiertos*")
    except:
        st.info("Cargando tickets...")

    st.divider()

    # ── Conversaciones del día ───────────────────────
    st.markdown(
        f'<div class="section-title">💬 Conversaciones esta sesión: '
        f'<strong>{st.session_state.conversation_count}</strong></div>',
        unsafe_allow_html=True)

    # ── Botón limpiar ────────────────────────────────
    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_result = None
        st.session_state.conversation_count = 0
        st.rerun()