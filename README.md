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