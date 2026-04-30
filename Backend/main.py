"""
TransControl – Sistema de Gestión y Control de Viajes (SGCV)
Punto de entrada principal de la API.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from database import create_tables, engine

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

# ── CORS (Frontend desde localhost o Electron) ─────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # ⚠️ En producción limitar a tu dominio
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
    """Inicializa la base de datos y crea el usuario administrador por defecto."""
    create_tables()
    print("✅  Tablas verificadas/creadas en PostgreSQL")
    _crear_admin_inicial()


def _crear_admin_inicial():
    """
    Crea un usuario administrador (GERENTE) si no existe ninguno.
    También crea roles de prueba para Secretaria y Coordinador.
    """
    from database import SessionLocal
    from models.models import Usuario, Transportista
    from core.security import hash_password

    db = SessionLocal()
    try:
        # ── GERENTE ──────────────────────────────────────────
        existe_gerente = db.query(Usuario).filter(Usuario.rol == "GERENTE").first()
        if not existe_gerente:
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
            print("✅  GERENTE creado: admin@transcontrol.ec / Admin1234!")

        # ── SECRETARIA (pruebas) ─────────────────────────────
        existe_secretaria = db.query(Usuario).filter(
            Usuario.correo == "secretaria@transcontrol.ec"
        ).first()
        if not existe_secretaria:
            sec = Usuario(
                cedula="0000000002",
                nombres="María Secretaria",
                correo="secretaria@transcontrol.ec",
                hashed_password=hash_password("Admin1234!"),
                rol="SECRETARIA",
                activo=True,
            )
            db.add(sec)
            db.commit()
            print("✅  SECRETARIA creada: secretaria@transcontrol.ec / Admin1234!")

        # ── COORDINADOR (pruebas) ────────────────────────────
        existe_coordinador = db.query(Usuario).filter(
            Usuario.correo == "coordinador@transcontrol.ec"
        ).first()
        if not existe_coordinador:
            coord = Usuario(
                cedula="0000000003",
                nombres="Juan Coordinador",
                correo="coordinador@transcontrol.ec",
                hashed_password=hash_password("Admin1234!"),
                rol="COORDINADOR",
                activo=True,
            )
            db.add(coord)
            db.commit()
            print("✅  COORDINADOR creado: coordinador@transcontrol.ec / Admin1234!")

        # ── TRANSPORTISTA (pruebas) ──────────────────────────
        existe_transportista = db.query(Usuario).filter(
            Usuario.correo == "transportista@transcontrol.ec"
        ).first()
        if not existe_transportista:
            trans_user = Usuario(
                cedula="1712345678",
                nombres="Carlos Mendoza",
                correo="transportista@transcontrol.ec",
                hashed_password=hash_password("Admin1234!"),
                rol="TRANSPORTISTA",
                activo=True,
            )
            db.add(trans_user)
            db.flush()  # Para obtener el ID
            
            # Crear perfil de transportista
            trans_perfil = Transportista(
                usuario_id=trans_user.id,
                placa_vehiculo="PBA-1234",
                tipo_vehiculo="Camión",
                capacidad_ton=15.0,
            )
            db.add(trans_perfil)
            db.commit()
            print("✅  TRANSPORTISTA creado: transportista@transcontrol.ec / Admin1234!")

    except Exception as e:
        print(f"⚠️  Error creando usuarios iniciales: {e}")
        db.rollback()
    finally:
        db.close()


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Root"])
def health():
    return {"status": "ok", "database": "connected"}