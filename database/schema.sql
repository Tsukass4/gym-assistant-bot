-- Tabla de clientes
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    email TEXT,
    join_date TEXT NOT NULL,
    membership_id INTEGER,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (membership_id) REFERENCES memberships(id)
);

-- Tabla de planes disponibles
CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    duration_days INTEGER NOT NULL,
    price REAL NOT NULL,
    description TEXT
);

-- Tabla de membresías activas
CREATE TABLE IF NOT EXISTS memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (plan_id) REFERENCES plans(id)
);

-- Tabla de tickets de soporte
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    issue_type TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT DEFAULT 'NORMAL',
    status TEXT DEFAULT 'ABIERTO',
    created_at TEXT NOT NULL,
    FOREIGN KEY (member_id) REFERENCES members(id)
);

-- Tabla de logs de conversación (para el Agente 3)
CREATE TABLE IF NOT EXISTS conversation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_phone TEXT,
    intent_detected TEXT,
    rule_applied TEXT,
    agent_response TEXT,
    required_human INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

-- ─────────────────────────────────────────
-- DATOS DE PRUEBA
-- ─────────────────────────────────────────

-- Planes del gimnasio
INSERT INTO plans (name, duration_days, price, description) VALUES
('Open Gym', 30, 1500.00, 'Acceso libre al gimnasio por 30 días'),
('3 Meses', 90, 4800.00, 'Acceso completo por 3 meses'),
('6 Meses', 180, 9000.00, 'Acceso completo por 6 meses'),
('Mensualidad con Coach', 30, 1800.00, 'Acceso + entrenador personal por 30 días'),
('10 Clases', 30, 1550.00, 'Paquete de 10 clases grupales'),
('6 Clases', 30, 900.00, 'Paquete de 6 clases grupales'),
('Clase Individual', 1, 270.00, 'Una clase grupal individual');

-- Clientes de prueba
INSERT INTO members (name, phone, email, join_date, is_active) VALUES
('Juan Pérez', '4491234567', 'juan@email.com', '2024-01-15', 1),
('María López', '4497654321', 'maria@email.com', '2023-06-10', 1),
('Carlos Rodríguez', '4499876543', 'carlos@email.com', '2024-03-20', 1),
('Ana González', '4492345678', 'ana@email.com', '2023-11-05', 1),
('Luis Martínez', '4498765432', 'luis@email.com', '2022-08-30', 1),
('Sofia Hernández', '4493456789', 'sofia@email.com', '2024-05-01', 1),
('Diego Torres', '4494567890', 'diego@email.com', '2023-09-15', 1),
('Valentina Ruiz', '4495678901', 'vale@email.com', '2024-02-28', 1),
('Roberto Sánchez', '4496789012', 'roberto@email.com', '2023-04-20', 1),
('Isabella Flores', '4490123456', 'isa@email.com', '2024-04-10', 1);

-- Membresías (algunas activas, algunas por vencer, una vencida)
INSERT INTO memberships (member_id, plan_id, start_date, end_date, is_active) VALUES
(1, 1, '2025-05-01', '2025-05-31', 1),  -- Juan: vence hoy/mañana
(2, 2, '2025-03-01', '2025-05-29', 0),  -- María: VENCIDA
(3, 3, '2025-01-01', '2025-06-30', 1),  -- Carlos: activa
(4, 4, '2025-01-01', '2026-01-01', 1),  -- Ana: anual activa
(5, 1, '2025-05-25', '2025-06-24', 1),  -- Luis: activa, vence en ~3 días
(6, 2, '2025-03-01', '2025-05-30', 1),  -- Sofia: por vencer
(7, 1, '2025-05-01', '2025-05-31', 1),  -- Diego: activa
(8, 3, '2025-02-01', '2025-07-31', 1),  -- Valentina: activa
(9, 1, '2025-04-01', '2025-04-30', 0),  -- Roberto: VENCIDA
(10, 4, '2024-04-10', '2025-04-10', 0); -- Isabella: VENCIDA