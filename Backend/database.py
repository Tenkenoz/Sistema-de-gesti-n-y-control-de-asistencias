"""
Configuración de la base de datos PostgreSQL usando SQLAlchemy 2.0+ con psycopg 3
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings

# ⚠️ IMPORTANTE: Para psycopg 3, la URL debe tener el prefijo "postgresql+psycopg://"
# Si tu DATABASE_URL usa "postgresql://", lo corregimos automáticamente
DATABASE_URL = settings.DATABASE_URL

# Corregir URL para usar psycopg 3 en lugar de psycopg2
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

print(f"🔗 Conectando a: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

# Crear engine (sin necesidad de instalar psycopg2)
engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # Número de conexiones en el pool
    max_overflow=20,        # Conexiones extra si el pool se llena
    pool_pre_ping=True,     # Verificar que las conexiones están activas
    echo=False,             # Cambiar a True para ver queries SQL en consola
)

# Fábrica de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base para modelos
Base = declarative_base()


def get_db():
    """
    Dependencia de FastAPI para obtener una sesión de base de datos.
    Cierra la sesión automáticamente después de cada request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Crear todas las tablas definidas en los modelos."""
    Base.metadata.create_all(bind=engine)