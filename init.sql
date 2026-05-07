-- ============================================================
-- TRANS CONTROL - DATOS DE PRUEBA
-- Se ejecuta automáticamente al crear el contenedor PostgreSQL
-- ============================================================
-- Los documentos se crean sin PDF real (contenido_pdf=NULL)
-- para pruebas de flujo. Los PDFs se cargan desde la app.
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

-- ============================================================
-- DOCUMENTOS DE PRUEBA (contenido_pdf = NULL)
-- Se insertan solo registros; los PDFs se suben desde la app.
-- Carlos Mendoza: 6 documentos APROBADOS
-- Luis Silva: documentos PENDIENTE / RECHAZADO
-- ============================================================
DO $$
DECLARE
    t_id    INTEGER;
    s_id    INTEGER;
BEGIN
    -- IDs de Carlos y Secretaria
    SELECT id INTO t_id FROM transportistas WHERE placa_vehiculo = 'PBA-1234';
    SELECT id INTO s_id FROM usuarios WHERE correo = 'secretaria@transcontrol.ec';

    IF t_id IS NOT NULL AND s_id IS NOT NULL THEN
        -- CÉDULA (APROBADO)
        INSERT INTO documentos (transportista_id, tipo, nombre_archivo, ruta_archivo, contenido_pdf, estado, revisado_por_id, subido_en, revisado_en)
        VALUES (t_id, 'CEDULA', 'CEDULA_ejemplo.pdf', NULL, NULL, 'APROBADO', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days');

        -- LICENCIA E (APROBADO)
        INSERT INTO documentos (transportista_id, tipo, nombre_archivo, ruta_archivo, contenido_pdf, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        VALUES (t_id, 'LICENCIA_E', 'LICENCIA_E_ejemplo.pdf', NULL, NULL, 'APROBADO', NOW() + INTERVAL '2 years', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days');

        -- MATRÍCULA (APROBADO)
        INSERT INTO documentos (transportista_id, tipo, nombre_archivo, ruta_archivo, contenido_pdf, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        VALUES (t_id, 'MATRICULA', 'MATRICULA_ejemplo.pdf', NULL, NULL, 'APROBADO', NOW() + INTERVAL '1 year', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days');

        -- REVISIÓN TÉCNICA (APROBADO)
        INSERT INTO documentos (transportista_id, tipo, nombre_archivo, ruta_archivo, contenido_pdf, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        VALUES (t_id, 'REVISION_TECNICA', 'REVISION_TECNICA_ejemplo.pdf', NULL, NULL, 'APROBADO', NOW() + INTERVAL '6 months', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days');

        -- SOAT (APROBADO)
        INSERT INTO documentos (transportista_id, tipo, nombre_archivo, ruta_archivo, contenido_pdf, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        VALUES (t_id, 'SOAT', 'SOAT_ejemplo.pdf', NULL, NULL, 'APROBADO', NOW() + INTERVAL '8 months', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days');

        -- PERMISO DE PESOS (APROBADO)
        INSERT INTO documentos (transportista_id, tipo, nombre_archivo, ruta_archivo, contenido_pdf, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        VALUES (t_id, 'PERMISO_PESOS', 'PERMISO_PESOS_ejemplo.pdf', NULL, NULL, 'APROBADO', NOW() + INTERVAL '1 year', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days');
    END IF;

    -- Luis Silva (transportista con placa GYA-9876)
    SELECT id INTO t_id FROM transportistas WHERE placa_vehiculo = 'GYA-9876';

    IF t_id IS NOT NULL AND s_id IS NOT NULL THEN
        -- CÉDULA (PENDIENTE)
        INSERT INTO documentos (transportista_id, tipo, nombre_archivo, ruta_archivo, contenido_pdf, estado, subido_en)
        VALUES (t_id, 'CEDULA', 'CEDULA_luis.pdf', NULL, NULL, 'PENDIENTE', NOW() - INTERVAL '1 day');

        -- LICENCIA E (RECHAZADA)
        INSERT INTO documentos (transportista_id, tipo, nombre_archivo, ruta_archivo, contenido_pdf, estado, observacion, revisado_por_id, subido_en, revisado_en)
        VALUES (t_id, 'LICENCIA_E', 'LICENCIA_E_luis.pdf', NULL, NULL, 'RECHAZADO', 'La licencia no corresponde al Tipo E exigido', s_id, NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day');

        -- MATRÍCULA (PENDIENTE)
        INSERT INTO documentos (transportista_id, tipo, nombre_archivo, ruta_archivo, contenido_pdf, estado, subido_en)
        VALUES (t_id, 'MATRICULA', 'MATRICULA_luis.pdf', NULL, NULL, 'PENDIENTE', NOW() - INTERVAL '1 day');
    END IF;
END$$;