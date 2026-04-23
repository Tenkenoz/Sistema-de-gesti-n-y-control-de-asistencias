## Requisitos previos
Instalar antes de continuar:
- Node.js v18+: https://nodejs.org/
- Python 3.10+: https://www.python.org/ (marcar "Add to PATH" al instalar)
- Git: https://git-scm.com/

## Verificar instalación (cmd o PowerShell)
node --version
npm --version
python --version
git --version

## Instalación
1. Clonar el repositorio
   git clone https://github.com/Tenkenoz/Sistema-de-gesti-n-y-control-de-asistencias.git
   cd Sistema-de-gesti-n-y-control-de-asistencias

2. Instalar dependencias Electron
   npm install

3. Instalar dependencias Python
   cd Backend
   pip install -r requirements.txt
   cd ..

## Ejecución
Terminal 1 (Backend):
   cd Backend
   uvicorn main:app --reload --port 8000

Terminal 2 (Electron):
   npm start