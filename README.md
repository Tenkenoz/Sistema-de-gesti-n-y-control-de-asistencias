"# Sistema-de-gesti-n-y-control-de-asistencias" 
## ⚙️ Instalación

1. Clonar repositorio

   git clone https://github.com/Tenkenoz/Sistema-de-gesti-n-y-control-de-asistencias.git

   cd Sistema-de-gesti-n-y-control-de-asistencias

2. Configurar variables de entorno (Backend/.env)


3. Instalar dependencias

   cd Backend

   pip install -r requirements.txt

   cd ..

## ▶️ Primera ejecución

   npm install

   docker-compose up -d --build

   npm start

## ▶️ Ejecutar después

   docker-compose up -d
   
   npm start

# 🚛 TransControl - Sistema de Gestión y Control de Viajes

Sistema integral para gestión de transportistas, validación documental, control de despacho y monitoreo de rutas.

---


## 🔄 Flujo del Sistema

1. Coordinador crea transportista → entrega credenciales
2. Transportista sube 6 documentos obligatorios
3. Secretaria revisa y aprueba/rechaza cada documento
4. Transportista corrige rechazados → reenvía
5. Secretaria aprueba todo → expediente completo
6. Secretaria crea viaje → asigna transportista → inicia ruta 🚛

---


---

## 📋 FLUJO DEL SISTEMA

```
1️⃣ COORDINADOR
   │
   ├── Inicia sesión con su correo y contraseña
   ├── Crea un nuevo transportista (nombre, cédula, correo, placa)
   ├── El sistema genera una contraseña aleatoria automáticamente
   └── Entrega las credenciales al transportista (correo + contraseña)
   
2️⃣ TRANSPORTISTA
   │
   ├── Inicia sesión con el correo y contraseña que le dio el Coordinador
   ├── Ve 6 tarjetas de documentos obligatorios (Cédula, Licencia E, Matrícula, SOAT, Revisión Técnica, Permiso de Pesos)
   ├── Sube cada documento en formato PDF (uno por uno, máximo 2MB cada uno)
   ├── Cada documento queda en estado "Pendiente" hasta que Secretaría lo revise
   └── Si un documento es rechazado, ve el motivo y puede corregirlo y reenviarlo

3️⃣ SECRETARIA
   │
   ├── Inicia sesión con su correo y contraseña
   ├── Va a "Validación Documental" y ve todos los documentos pendientes de revisión
   ├── Revisa cada documento y decide: APROBAR o RECHAZAR
   ├── Si rechaza, debe escribir el motivo (obligatorio)
   ├── Los documentos rechazados se muestran en rojo en la tabla
   └── Cuando un transportista tiene los 6 documentos aprobados, aparece como disponible

4️⃣ SECRETARIA (Control de Despacho)
   │
   ├── Va a "Control de Despacho"
   ├── Crea un nuevo viaje (tipo de mercancía, peso, origen, destino, destinatario)
   ├── El viaje se crea en estado "DISPONIBLE"
   ├── Asigna un transportista (solo aparecen los que tienen documentos aprobados)
   ├── El viaje pasa a estado "TRANSPORTISTA_ASIGNADO"
   ├── Inicia el viaje → estado "EN_EJECUCION"
   └── Marca la llegada → estado "COMPLETADO"

5️⃣ TRANSPORTISTA
   │
   ├── Cuando tiene todos los documentos aprobados, puede ver "Mi Viaje Actual"
   ├── Ve los detalles del viaje asignado (origen, destino, carga, destinatario)
   └── Sigue las instrucciones operativas del viaje
```

---

## 🔄 DIAGRAMA DE ESTADOS DE DOCUMENTOS

```
FALTANTE ──(Transportista sube PDF)──> PENDIENTE ──(Secretaria revisa)──> APROBADO ✅
                                         │
                                         └──(Secretaria rechaza)──> RECHAZADO ❌
                                                                       │
                                                                       └──(Transportista corrige y reenvía)──> PENDIENTE
```

---

## 🔄 DIAGRAMA DE ESTADOS DE VIAJES

```
DISPONIBLE ──(Secretaria asigna transportista)──> TRANSPORTISTA_ASIGNADO
                                                       │
                                                       └──(Secretaria inicia)──> EN_EJECUCION
                                                                                    │
                                                                                    └──(Secretaria completa)──> COMPLETADO ✅
```

---
