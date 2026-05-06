-- ============================================================
-- TRANS CONTROL - DATOS DE PRUEBA
-- Se ejecuta automáticamente al crear el contenedor PostgreSQL
-- ============================================================
-- NOTA: contenido_pdf contiene un PDF mínimo válido (1 página en blanco).
--       ruta_archivo queda NULL porque ya no usamos disco.
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
-- PDF MÍNIMO VÁLIDO (1 página en blanco, ~700 bytes)
-- Se reutiliza en todos los documentos de prueba.
-- Puedes abrirlo en cualquier visor PDF.
-- ============================================================
DO $$
DECLARE
    t_id    INTEGER;
    s_id    INTEGER;
    pdf_min BYTEA;
BEGIN
    -- PDF mínimo válido (1 página en blanco, compatible con Adobe/Chrome)
    pdf_min := decode(
        '255044462d312e340a312030206f626a0a3c3c202f54797065202f436174616c6f67202f50616765'
        '7320322030205220203e3e0a656e646f626a0a322030206f626a0a3c3c202f54797065202f506167'
        '6573202f4b696473205b332030205d202f436f756e7420312020203e3e0a656e646f626a0a332030'
        '206f626a0a3c3c202f54797065202f50616765202f506172656e7420322030205220202f4d656469'
        '61426f78205b302030203539352e323820383431203832205d20203e3e0a656e646f626a0a787265'
        '660a302034200a303030303030303030302036353533352066200a303030303030303030392030303'
        '030302066200a303030303030303035352030303030302066200a30303030303030303935203030303'
        '030302066200a747261696c65720a3c3c202f53697a6520342020202f526f6f74203120302052203e'
        '3e0a7374617274787265660a3133370a2525454f46',
        'hex'
    );
 
    SELECT id INTO t_id FROM transportistas WHERE placa_vehiculo = 'PBA-1234';
    SELECT id INTO s_id FROM usuarios WHERE correo = 'secretaria@transcontrol.ec';
 
    IF t_id IS NOT NULL AND s_id IS NOT NULL THEN
 
        INSERT INTO documentos (transportista_id, tipo, ruta_archivo, nombre_archivo, contenido_pdf, estado, revisado_por_id, subido_en, revisado_en)
        SELECT t_id, 'CEDULA', NULL, 'CEDULA_prueba.pdf', pdf_min, 'APROBADO', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days'
        WHERE NOT EXISTS (SELECT 1 FROM documentos WHERE transportista_id = t_id AND tipo = 'CEDULA');
 
        INSERT INTO documentos (transportista_id, tipo, ruta_archivo, nombre_archivo, contenido_pdf, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        SELECT t_id, 'LICENCIA_E', NULL, 'LICENCIA_E_prueba.pdf', pdf_min, 'APROBADO', NOW() + INTERVAL '2 years', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days'
        WHERE NOT EXISTS (SELECT 1 FROM documentos WHERE transportista_id = t_id AND tipo = 'LICENCIA_E');
 
        INSERT INTO documentos (transportista_id, tipo, ruta_archivo, nombre_archivo, contenido_pdf, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        SELECT t_id, 'MATRICULA', NULL, 'MATRICULA_prueba.pdf', pdf_min, 'APROBADO', NOW() + INTERVAL '1 year', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days'
        WHERE NOT EXISTS (SELECT 1 FROM documentos WHERE transportista_id = t_id AND tipo = 'MATRICULA');
 
        INSERT INTO documentos (transportista_id, tipo, ruta_archivo, nombre_archivo, contenido_pdf, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        SELECT t_id, 'REVISION_TECNICA', NULL, 'REVISION_TECNICA_prueba.pdf', pdf_min, 'APROBADO', NOW() + INTERVAL '6 months', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days'
        WHERE NOT EXISTS (SELECT 1 FROM documentos WHERE transportista_id = t_id AND tipo = 'REVISION_TECNICA');
 
        INSERT INTO documentos (transportista_id, tipo, ruta_archivo, nombre_archivo, contenido_pdf, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        SELECT t_id, 'SOAT', NULL, 'SOAT_prueba.pdf', pdf_min, 'APROBADO', NOW() + INTERVAL '8 months', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days'
        WHERE NOT EXISTS (SELECT 1 FROM documentos WHERE transportista_id = t_id AND tipo = 'SOAT');
 
        INSERT INTO documentos (transportista_id, tipo, ruta_archivo, nombre_archivo, contenido_pdf, estado, fecha_vencimiento, revisado_por_id, subido_en, revisado_en)
        SELECT t_id, 'PERMISO_PESOS', NULL, 'PERMISO_PESOS_prueba.pdf', pdf_min, 'APROBADO', NOW() + INTERVAL '1 year', s_id, NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days'
        WHERE NOT EXISTS (SELECT 1 FROM documentos WHERE transportista_id = t_id AND tipo = 'PERMISO_PESOS');
 
    END IF;
END$$;