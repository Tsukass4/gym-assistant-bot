import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from database.db import (
    get_recent_tickets,
    get_conversation_logs,
    get_member_stats,
    get_all_plans,
    update_ticket_status
)

st.set_page_config(
    page_title="Admin — GymBot",
    page_icon="⚙️",
    layout="wide"
)

st.markdown("""
<style>
.stApp { background-color: #F8F9FA; }
.ticket-card {
    background: white;
    border: 1px solid #DEE2E6;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 13px;
}
.ticket-alta   { border-left: 4px solid #DC3545; }
.ticket-normal { border-left: 4px solid #FFC107; }
</style>
""", unsafe_allow_html=True)

st.title("⚙️ Panel de Administración — GymBot")
st.markdown("Vista interna del sistema para el staff del gimnasio.")
st.divider()

# ── Tabs ────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📊 Resumen general",
    "🎫 Tickets de soporte",
    "📋 Logs de conversación"
])

# ══════════════════════════════════════════════════
# TAB 1 — RESUMEN GENERAL
# ══════════════════════════════════════════════════
with tab1:
    st.markdown("### Estadísticas del gimnasio")
    try:
        stats = get_member_stats()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total socios", stats["total_members"])
        c2.metric("Membresías activas", stats["active_memberships"])
        c3.metric("Membresías vencidas", stats["expired_memberships"],
                  delta=f"-{stats['expired_memberships']}", delta_color="inverse")
        c4.metric("Tickets abiertos", stats["open_tickets"],
                  delta=f"+{stats['open_tickets']}" if stats["open_tickets"] > 0 else "0",
                  delta_color="inverse")
    except Exception as e:
        st.error(f"Error cargando estadísticas: {e}")

    st.divider()
    st.markdown("### 💰 Planes disponibles")
    try:
        plans = get_all_plans()
        cols = st.columns(len(plans))
        for i, plan in enumerate(plans):
            with cols[i]:
                st.markdown(f"""
                <div style="background:white;border:1px solid #DEE2E6;
                border-radius:10px;padding:16px;text-align:center">
                    <div style="font-size:20px;font-weight:700;
                    color:#1F3864">${plan['price']:.0f}</div>
                    <div style="font-weight:600;margin:4px 0">{plan['name']}</div>
                    <div style="font-size:12px;color:#6C757D">
                    {plan['duration_days']} días</div>
                    <div style="font-size:11px;color:#6C757D;margin-top:4px">
                    {plan['description']}</div>
                </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error cargando planes: {e}")

# ══════════════════════════════════════════════════
# TAB 2 — TICKETS
# ══════════════════════════════════════════════════
with tab2:
    st.markdown("### Tickets de soporte")
    try:
        tickets = get_recent_tickets(20)
        if tickets:
            for t in tickets:
                css = "ticket-alta" if t["priority"] == "ALTA" else "ticket-normal"
                icon = "🔴" if t["priority"] == "ALTA" else "🟡"
                status_color = (
                    "#28A745" if t["status"] == "CERRADO"
                    else "#FFC107" if t["status"] == "EN_PROCESO"
                    else "#DC3545"
                )
                st.markdown(f"""
                <div class="ticket-card {css}">
                    {icon} <strong>{t['issue_type']}</strong>
                    &nbsp;&nbsp;
                    <span style="background:{status_color};color:white;
                    padding:2px 8px;border-radius:10px;font-size:11px">
                    {t['status']}</span>
                    <br>
                    <span style="color:#495057">{t['description']}</span>
                    <br>
                    <small style="color:#6C757D">
                    🕐 {t['created_at']} · Prioridad: {t['priority']}
                    </small>
                </div>""", unsafe_allow_html=True)
        else:
            st.success("No hay tickets abiertos 🎉")
    except Exception as e:
        st.error(f"Error: {e}")

# ══════════════════════════════════════════════════
# TAB 3 — LOGS
# ══════════════════════════════════════════════════
with tab3:
    st.markdown("### Logs de conversación — Agente 3")
    try:
        logs = get_conversation_logs(20)
        if logs:
            for log in logs:
                alert_icon = (
                    "🚨" if log.get("required_human") == 1
                    else "✅"
                )
                st.markdown(f"""
                <div class="ticket-card">
                    {alert_icon} <strong>{log['intent_detected']}</strong>
                    &nbsp;·&nbsp;
                    <small style="color:#6C757D">{log['created_at']}</small>
                    <br>
                    <span style="font-size:12px;color:#495057">
                    📋 {log['rule_applied']}</span>
                    <br>
                    <span style="font-size:12px;color:#6C757D">
                    📱 {log.get('member_phone','desconocido')}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No hay logs registrados aún.")
    except Exception as e:
        st.error(f"Error: {e}")