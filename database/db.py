import sqlite3
from datetime import datetime, date
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'gym.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Crea las tablas e inserta datos de prueba si no existen."""
    conn = get_connection()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente")

def get_member_by_phone(phone: str):
    """Busca un cliente por teléfono."""
    conn = get_connection()
    member = conn.execute(
        "SELECT * FROM members WHERE phone = ?", (phone,)
    ).fetchone()
    conn.close()
    return dict(member) if member else None

def get_active_membership(member_id: int):
    """Obtiene la membresía activa de un cliente."""
    conn = get_connection()
    membership = conn.execute("""
        SELECT m.*, p.name as plan_name, p.price, p.duration_days
        FROM memberships m
        JOIN plans p ON m.plan_id = p.id
        WHERE m.member_id = ? AND m.is_active = 1
        ORDER BY m.end_date DESC LIMIT 1
    """, (member_id,)).fetchone()
    conn.close()
    return dict(membership) if membership else None

def get_all_plans():
    """Obtiene todos los planes disponibles."""
    conn = get_connection()
    plans = conn.execute("SELECT * FROM plans").fetchall()
    conn.close()
    return [dict(p) for p in plans]

def days_until_expiry(end_date: str) -> int:
    """Calcula cuántos días faltan para que venza la membresía."""
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    today = date.today()
    return (end - today).days

def create_support_ticket(member_id, issue_type: str,
                          description: str, priority: str = 'NORMAL'):
    """Crea un ticket de soporte."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO tickets (member_id, issue_type, description, priority, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (member_id, issue_type, description, priority,
          datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def log_conversation(member_phone: str, intent: str,
                     rule_applied: str, response: str,
                     required_human: bool = False):
    """Guarda el log de cada conversación para el Agente 3."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO conversation_logs
        (member_phone, intent_detected, rule_applied,
         agent_response, required_human, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (member_phone, intent, rule_applied, response,
          1 if required_human else 0,
          datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_recent_tickets(limit: int = 5):
    """Obtiene los últimos tickets para el panel del staff."""
    conn = get_connection()
    tickets = conn.execute("""
        SELECT t.*, m.name as member_name
        FROM tickets t
        LEFT JOIN members m ON t.member_id = m.id
        ORDER BY t.created_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(t) for t in tickets]
def get_member_by_name(name: str):
    """Busca un cliente por nombre (búsqueda parcial)."""
    conn = get_connection()
    members = conn.execute(
        "SELECT * FROM members WHERE name LIKE ?", (f'%{name}%',)
    ).fetchall()
    conn.close()
    return [dict(m) for m in members]

def get_expired_memberships():
    """Obtiene todos los clientes con membresía vencida."""
    conn = get_connection()
    expired = conn.execute("""
        SELECT m.name, m.phone, mem.end_date, p.name as plan_name
        FROM members m
        JOIN memberships mem ON m.id = mem.member_id
        JOIN plans p ON mem.plan_id = p.id
        WHERE mem.is_active = 0
        ORDER BY mem.end_date DESC
    """).fetchall()
    conn.close()
    return [dict(e) for e in expired]

def get_plan_by_id(plan_id: int):
    """Obtiene un plan por su ID."""
    conn = get_connection()
    plan = conn.execute(
        "SELECT * FROM plans WHERE id = ?", (plan_id,)
    ).fetchone()
    conn.close()
    return dict(plan) if plan else None

def update_ticket_status(ticket_id: int, status: str):
    """Actualiza el estado de un ticket (ABIERTO, EN_PROCESO, CERRADO)."""
    conn = get_connection()
    conn.execute(
        "UPDATE tickets SET status = ? WHERE id = ?",
        (status, ticket_id)
    )
    conn.commit()
    conn.close()

def get_conversation_logs(limit: int = 10):
    """Obtiene los últimos logs de conversación."""
    conn = get_connection()
    logs = conn.execute("""
        SELECT * FROM conversation_logs
        ORDER BY created_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(l) for l in logs]

def get_member_stats():
    """Estadísticas generales para el panel del staff."""
    conn = get_connection()
    total = conn.execute(
        "SELECT COUNT(*) as total FROM members"
    ).fetchone()['total']
    active = conn.execute(
        "SELECT COUNT(*) as total FROM memberships WHERE is_active = 1"
    ).fetchone()['total']
    expired = conn.execute(
        "SELECT COUNT(*) as total FROM memberships WHERE is_active = 0"
    ).fetchone()['total']
    open_tickets = conn.execute(
        "SELECT COUNT(*) as total FROM tickets WHERE status = 'ABIERTO'"
    ).fetchone()['total']
    conn.close()
    return {
        'total_members': total,
        'active_memberships': active,
        'expired_memberships': expired,
        'open_tickets': open_tickets
    }