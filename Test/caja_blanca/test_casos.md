# 📋 Casos de Prueba - TransControl (Todas las Vistas)

---

## 🔐 LOGIN (`index.html`)

| ID | Caso | Pasos | Datos de Entrada | Resultado Esperado |
|----|------|-------|------------------|-------------------|
| L01 | Login exitoso Secretaria | Ingresar credenciales y enviar | `secretaria@transcontrol.ec` / `Admin1234!` | Redirige a `views/secretaria_view.html` |
| L02 | Login exitoso Coordinador | Ingresar credenciales y enviar | `coordinador@transcontrol.ec` / `Admin1234!` | Redirige a `views/coordinador_view.html` |
| L03 | Login exitoso Transportista | Ingresar credenciales y enviar | `transportista@transcontrol.ec` / `Admin1234!` | Redirige a `views/transportista_view.html` |
| L04 | Correo inválido | Ingresar texto sin @ | `noesuncorreo` / `Admin1234!` | Muestra "Ingrese un correo electrónico válido" |
| L05 | Contraseña corta | Contraseña < 8 caracteres | `admin@transcontrol.ec` / `123` | Muestra "Al menos 8 caracteres" |
| L06 | Credenciales incorrectas | Correo existe pero contraseña mal | `secretaria@transcontrol.ec` / `mala` | Muestra "Contraseña incorrecta" |
| L07 | Recuperar contraseña | Clic en "¿Olvidaste?" → ingresar correo | `secretaria@transcontrol.ec` | Muestra "Si el correo existe..." |
| L08 | Recuperar con correo inválido | Ingresar correo sin formato | `noesuncorreo` | Muestra "Ingrese un correo válido" |
| L09 | Sesión expirada | Dejar token viejo en localStorage | Token expirado | Muestra "Tu sesión ha expirado" |

---

## 🟦 COORDINADOR (`coordinador_view.html`)

| ID | Caso | Pasos | Resultado Esperado |
|----|------|-------|-------------------|
| C01 | Ver transportistas activos | Ir a "Gestión de Personal" | Tabla muestra transportistas con estado "Activo" |
| C02 | Ver inactivos | Activar checkbox "Ver inactivos" | Tabla muestra transportistas inactivos |
| C03 | Crear transportista | Clic en "Nuevo Transportista" → llenar datos | Modal muestra credenciales generadas (correo + contraseña) |
| C04 | Crear con cédula inválida | Ingresar cédula de 5 dígitos | Muestra "Cédula inválida (10 o 13 dígitos)" |
| C05 | Crear con correo inválido | Ingresar "malformato" en correo | Muestra "Correo electrónico inválido" |
| C06 | Crear con nombres cortos | Ingresar "AB" en nombres | Muestra "Solo letras y espacios (mín. 3 caracteres)" |
| C07 | Crear con placa inválida | Ingresar "1234ABC" | Muestra "Formato: 3 letras + guión + 3-4 dígitos" |
| C08 | Editar transportista | Clic en ícono de lápiz → cambiar placa | Toast "Transportista actualizado" |
| C09 | Activar transportista | Clic en check verde → confirmar | Cambia a estado "Activo" |
| C10 | Desactivar transportista | Clic en ícono de prohibido → seleccionar razón | Modal pide razón, toast "Transportista desactivado" |
| C11 | Desactivar sin razón | Dejar razón vacía y enviar | Muestra "Seleccione un motivo" |
| C12 | Eliminar permanente | Clic en ícono de basura → confirmar | Toast "Transportista eliminado permanentemente" |
| C13 | Ver viajes activos | Ir a "Monitoreo de Rutas" | Grid muestra viajes en ejecución/asignados |
| C14 | Modificar ruta | Clic en "Modificar Ruta" en viaje en ejecución | Modal pide nueva ruta y motivo |
| C15 | Modificar ruta vacía | Dejar campos vacíos y enviar | Muestra errores de validación |

---

## 🟪 SECRETARIA (`secretaria_view.html`)

| ID | Caso | Pasos | Resultado Esperado |
|----|------|-------|-------------------|
| S01 | Ver documentos pendientes | Ir a "Validación Documental" | Tabla muestra docs con estado PENDIENTE/RECHAZADO |
| S02 | Badge de pendientes | Verificar número en el badge rojo | Muestra cantidad de documentos PENDIENTE |
| S03 | Aprobar documento | Clic en "Revisar" → seleccionar APROBAR → guardar | Toast "Documento revisado correctamente" |
| S04 | Rechazar documento | Seleccionar RECHAZAR → escribir observación → guardar | Toast "Documento revisado correctamente" |
| S05 | Rechazar sin observación | Seleccionar RECHAZAR sin escribir observación | Muestra "Debe escribir una observación al rechazar" |
| S06 | No seleccionar veredicto | Clic en guardar sin seleccionar APROBAR/RECHAZAR | Muestra "Debe seleccionar un veredicto" |
| S07 | Crear viaje | Clic en "Crear Nuevo Viaje" → llenar todos los campos | Toast "Viaje creado exitosamente", aparece en DISPONIBLE |
| S08 | Crear viaje con campos vacíos | Dejar campos obligatorios vacíos | Muestra errores de validación |
| S09 | Crear viaje con peso inválido | Ingresar peso negativo o 0 | Muestra "Debe ser un número positivo" |
| S10 | Crear viaje con teléfono inválido | Ingresar letras en teléfono | Muestra "Solo dígitos (7-15)" |
| S11 | Asignar transportista | Clic en "Asignar Transportista" en viaje DISPONIBLE | Select muestra solo transportistas con docs aprobados |
| S12 | Asignar sin seleccionar | Clic en confirmar sin seleccionar transportista | Muestra "Seleccione un transportista" |
| S13 | Iniciar viaje | Clic en "Iniciar Viaje" en viaje ASIGNADO → confirmar | Toast "Viaje Iniciado", estado cambia a EN_EJECUCION |
| S14 | Completar viaje | Clic en "Marcar Llegada" en viaje EN_EJECUCION | Toast "Viaje Completado" |
| S15 | Filtrar viajes | Clic en botones de filtro (Todos/Disponibles/Asignados/En Ejecución) | Grid muestra solo viajes del estado seleccionado |

---

## 🟩 TRANSPORTISTA (`transportista_view.html`)

| ID | Caso | Pasos | Resultado Esperado |
|----|------|-------|-------------------|
| T01 | Ver expediente | Iniciar sesión como transportista | Sidebar muestra nombre y placa |
| T02 | Ver banner (sin docs) | Primer inicio sin documentos | Banner azul "Sube tu documentación" |
| T03 | Ver 6 tarjetas | Ir a "Mi Expediente" | 6 tarjetas: Cédula, Licencia E, Matrícula, SOAT, Revisión Técnica, Permiso Pesos |
| T04 | Tarjeta "Faltante" | Ver tarjeta sin documento subido | Fondo gris, botón "Subir" |
| T05 | Subir documento PDF | Clic en "Subir" → seleccionar PDF válido (<2MB) | Toast "Documento subido correctamente", tarjeta cambia a "Pendiente" |
| T06 | Subir archivo no PDF | Intentar subir .jpg o .png | Muestra "Solo se permiten archivos PDF" |
| T07 | Subir archivo >2MB | Intentar subir PDF mayor a 2MB | Muestra "El archivo excede el tamaño máximo de 2MB" |
| T08 | Drag & drop | Arrastrar PDF a la zona de carga | Muestra nombre del archivo |
| T09 | Tarjeta "Pendiente" | Después de subir, sin revisión de secretaria | Fondo ámbar, botón "Reenviar" |
| T10 | Tarjeta "Aprobado" | Después de que secretaria aprueba (Carlos) | Fondo verde, check ✅ |
| T11 | Tarjeta "Rechazado" | Después de que secretaria rechaza (Luis) | Fondo rojo, muestra motivo del rechazo |
| T12 | Corregir rechazado | Clic en "Corregir y Reenviar" → subir nuevo PDF | Tarjeta vuelve a "Pendiente" |
| T13 | Badge de alerta | Con documentos rechazados o faltantes | Punto rojo en menú lateral |
| T14 | Banner completo | Con 6 documentos aprobados | Banner verde "¡Expediente Completo!" |
| T15 | Ver viaje (docs completos) | Con expediente aprobado, ir a "Mi Viaje Actual" | Muestra datos del viaje asignado |
| T16 | Viaje bloqueado (docs incompletos) | Con docs faltantes, ir a "Mi Viaje Actual" | Muestra "Documentación Incompleta" con botón a expediente |
| T17 | Sin viaje asignado | Docs completos pero sin viaje | Muestra "No tienes viajes asignados" |
| T18 | Cerrar sesión | Clic en "Cerrar Sesión" | Vuelve al login, token eliminado |