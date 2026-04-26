"""
TransControl – Sistema de Gestión y Control de Viajes (SGCV)
Punto de entrada principal de la API.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from database import create_tables

# importar modelos para que SQLAlchemy los registre antes de create_tables()
import models.models  # noqa: F401

from routers import auth, transportistas, viajes, monitoreo

# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description="API REST para el sistema TransControl (SRS Rev 1.0)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS (Electron hace peticiones desde file:// o localhost) ──────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # en producción limitar a tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Servir archivos subidos ────────────────────────────────────────────────────

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(transportistas.router)
app.include_router(viajes.router)
app.include_router(monitoreo.router)

# ── Eventos ────────────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    create_tables()
    print("✅  Tablas verificadas/creadas en PostgreSQL")
    _crear_admin_inicial()


def _crear_admin_inicial():
    """Crea un usuario administrador (GERENTE) si no existe ninguno."""
    from sqlalchemy.orm import Session
    from database import SessionLocal
    from models.models import Usuario
    from core.security import hash_password

    db: Session = SessionLocal()
    try:
        existe = db.query(Usuario).filter(Usuario.rol == "GERENTE").first()
        if not existe:
            admin = Usuario(
                cedula="0000000001",
                nombres="Administrador TransControl",
                correo="admin@transcontrol.ec",
                hashed_password=hash_password("Admin1234!"),
                rol="GERENTE",
                activo=True,
            )
            db.add(admin)
            db.commit()
            print("✅  Usuario administrador creado: admin@transcontrol.ec / Admin1234!")
    finally:
        db.close()


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    return {"app": settings.APP_NAME, "version": "1.0.0", "status": "running"}


@app.get("/health", tags=["Root"])
def health():
    return {"status": "ok"}