# 🚛 TransControl - Sistema de Gestión y Control de Viajes

Sistema integral para gestión de transportistas, validación documental, control de despacho y monitoreo de rutas.

---

## 🔑 Credenciales de Prueba

| Rol           | Correo                                                                | Contraseña |
| ------------- | --------------------------------------------------------------------- | ---------- |
| GERENTE       | [admin@transcontrol.ec](mailto:admin@transcontrol.ec)                 | Admin1234! |
| SECRETARIA    | [secretaria@transcontrol.ec](mailto:secretaria@transcontrol.ec)       | Admin1234! |
| COORDINADOR   | [coordinador@transcontrol.ec](mailto:coordinador@transcontrol.ec)     | Admin1234! |
| TRANSPORTISTA | [transportista@transcontrol.ec](mailto:transportista@transcontrol.ec) | Admin1234! |

---

## 🔄 Flujo del Sistema

1. Coordinador crea transportista → entrega credenciales
2. Transportista sube 6 documentos obligatorios
3. Secretaria revisa y aprueba/rechaza cada documento
4. Transportista corrige rechazados → reenvía
5. Secretaria aprueba todo → expediente completo
6. Secretaria crea viaje → asigna transportista → inicia ruta 🚛

---

## 📦 Tecnologías

* Frontend: HTML, Tailwind CSS, JavaScript Vanilla, Electron
* Backend: Python, FastAPI, SQLAlchemy
* Base de datos: PostgreSQL 17
* Contenedores: Docker + Docker Compose

---

## 🔧 Requisitos previos

* Node.js v18+: https://nodejs.org/
* Python 3.10+: https://www.python.org/ (marcar "Add to PATH")
* Docker Desktop: https://www.docker.com/products/docker-desktop/
* Git: https://git-scm.com/

---

## ✅ Verificar instalación (cmd o PowerShell)

node --version
npm --version
python --version
docker --version
git --version

---

## ⚙️ Instalación

1. Clonar repositorio
   git clone https://github.com/Tenkenoz/Sistema-de-gesti-n-y-control-de-asistencias.git
   cd Sistema-de-gesti-n-y-control-de-asistencias

2. Instalar dependencias frontend
   npm install

3. Instalar backend
   cd Backend
   pip install -r requirements.txt
   cd ..

---

## ▶️ Ejecución

### Opción A - Docker

Terminal 1:
docker-compose up -d --build

Terminal 2:
npm start

### Opción B - Manual

Terminal 1:
cd Backend
uvicorn main:app --reload --port 8000

Terminal 2:
npm start

---

## 🌐 Accesos

Frontend: Se abre con Electron
Backend: http://localhost:8000
Swagger: http://localhost:8000/docs
