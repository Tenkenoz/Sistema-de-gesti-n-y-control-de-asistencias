-- ============================================================
-- TRANS CONTROL - DATOS DE PRUEBA
-- Se ejecuta automáticamente al crear el contenedor PostgreSQL
-- ============================================================

-- SECRETARIA
INSERT INTO usuarios (cedula, nombres, correo, hashed_password, rol, activo, telefono)
SELECT '0000000002', 'María Elena Vargas', 'secretaria@transcontrol.ec',
        '$2b$12$LJ3m4ys3Lk0TSwHCpNqrAOg7zMAZqHBQU2rpHGRqNsG5bV5VJ7n3y',
        'SECRETARIA', TRUE, '0990000002'
WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE correo = 'secretaria@transcontrol.ec');

-- COORDINADOR
INSERT INTO usuarios (cedula, nombres, correo, hashed_password, rol, activo, telefono)
SELECT '0000000003', 'Juan Carlos Martinez', 'coordinador@transcontrol.ec',
        '$2b$12$LJ3m4ys3Lk0TSwHCpNqrAOg7zMAZqHBQU2rpHGRqNsG5bV5VJ7n3y',
        'COORDINADOR', TRUE, '0990000003'
WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE correo = 'coordinador@transcontrol.ec');

-- TRANSPORTISTA 1 - Carlos Mendoza
INSERT INTO usuarios (cedula, nombres, correo, hashed_password, rol, activo, telefono)
SELECT '1712345678', 'Carlos Mendoza', 'transportista@transcontrol.ec',
        '$2b$12$LJ3m4ys3Lk0TSwHCpNqrAOg7zMAZqHBQU2rpHGRqNsG5bV5VJ7n3y',
        'TRANSPORTISTA', TRUE, '0991112233'
WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE correo = 'transportista@transcontrol.ec');

-- TRANSPORTISTA 2 - Luis Silva
INSERT INTO usuarios (cedula, nombres, correo, hashed_password, rol, activo, telefono)
SELECT '1709876543', 'Luis Alberto Silva', 'luis.silva@transcontrol.ec',
        '$2b$12$LJ3m4ys3Lk0TSwHCpNqrAOg7zMAZqHBQU2rpHGRqNsG5bV5VJ7n3y',
        'TRANSPORTISTA', TRUE, '0992223344'
WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE correo = 'luis.silva@transcontrol.ec');

-- PERFILES DE TRANSPORTISTAS
INSERT INTO transportistas (usuario_id, placa_vehiculo, tipo_vehiculo, capacidad_ton)
SELECT id, 'PBA-1234', 'Camión de Carga Pesada', 15.0
FROM usuarios WHERE correo = 'transportista@transcontrol.ec'
AND NOT EXISTS (SELECT 1 FROM transportistas WHERE placa_vehiculo = 'PBA-1234');

INSERT INTO transportistas (usuario_id, placa_vehiculo, tipo_vehiculo, capacidad_ton)
SELECT id, 'GYA-9876', 'Tráiler', 20.0
FROM usuarios WHERE correo = 'luis.silva@transcontrol.ec'
AND NOT EXISTS (SELECT 1 FROM transportistas WHERE placa_vehiculo = 'GYA-9876');

-- Documentos Carlos Mendoza (6 APROBADOS)
DO $$
DECLARE
    t_id INTEGER;
    s_id INTEGER;
BEGIN
    SELECT id INTO t_id FROM transportistas WHERE placa_vehiculo = 'PBA-1234';
    SELECT id INTO s_id FROM usuarios WHERE correo = 'secretaria@transcontrol.ec';
    
    IF t_id IS NOT NULL AND s_id IS NOT NULL THEN
        INSERT INTO documentos (transportista_id, tipo, ruta_archivo, nombre_archivo, estado, revisado_por_id, subido_en, revisado_en)
        SELECT t_id, 'CEDULA', '/uploads/1/CEDULA.pdf', 'CEDULA.pdf', 'APROBADO', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days'
        WHERE NOT EXISTS (SELECT 1 FROM documentos WHERE transportista_id = t_id AND tipo = 'CEDULA');
        
        INSERT INTO documentos (transportista_id, tipo, ruta_archivo, nombre_archivo, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        SELECT t_id, 'LICENCIA_E', '/uploads/1/LICENCIA_E.pdf', 'LICENCIA_E.pdf', 'APROBADO', NOW() + INTERVAL '2 years', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days'
        WHERE NOT EXISTS (SELECT 1 FROM documentos WHERE transportista_id = t_id AND tipo = 'LICENCIA_E');
        
        INSERT INTO documentos (transportista_id, tipo, ruta_archivo, nombre_archivo, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        SELECT t_id, 'MATRICULA', '/uploads/1/MATRICULA.pdf', 'MATRICULA.pdf', 'APROBADO', NOW() + INTERVAL '1 year', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days'
        WHERE NOT EXISTS (SELECT 1 FROM documentos WHERE transportista_id = t_id AND tipo = 'MATRICULA');
        
        INSERT INTO documentos (transportista_id, tipo, ruta_archivo, nombre_archivo, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        SELECT t_id, 'REVISION_TECNICA', '/uploads/1/REVISION_TECNICA.pdf', 'REVISION_TECNICA.pdf', 'APROBADO', NOW() + INTERVAL '6 months', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days'
        WHERE NOT EXISTS (SELECT 1 FROM documentos WHERE transportista_id = t_id AND tipo = 'REVISION_TECNICA');
        
        INSERT INTO documentos (transportista_id, tipo, ruta_archivo, nombre_archivo, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        SELECT t_id, 'SOAT', '/uploads/1/SOAT.pdf', 'SOAT.pdf', 'APROBADO', NOW() + INTERVAL '8 months', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days'
        WHERE NOT EXISTS (SELECT 1 FROM documentos WHERE transportista_id = t_id AND tipo = 'SOAT');
        
        INSERT INTO documentos (transportista_id, tipo, ruta_archivo, nombre_archivo, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        SELECT t_id, 'PERMISO_PESOS', '/uploads/1/PERMISO_PESOS.pdf', 'PERMISO_PESOS.pdf', 'APROBADO', NOW() + INTERVAL '1 year', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days'
        WHERE NOT EXISTS (SELECT 1 FROM documentos WHERE transportista_id = t_id AND tipo = 'PERMISO_PESOS');
    END IF;
END$$;
