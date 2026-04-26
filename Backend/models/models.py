"""
Modelos de base de datos para TransControl.
Tablas: usuarios, transportistas, documentos, viajes, auditoria
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey,
    Integer, Numeric, String, Text, BigInteger,
)
from sqlalchemy.orm import relationship

from database import Base


# ── Enumeraciones ──────────────────────────────────────────────────────────────

class RolEnum(str, enum.Enum):
    GERENTE       = "GERENTE"
    SECRETARIA    = "SECRETARIA"
    COORDINADOR   = "COORDINADOR"
    TRANSPORTISTA = "TRANSPORTISTA"
    PRESIDENTE    = "PRESIDENTE"


class EstadoViajeEnum(str, enum.Enum):
    DISPONIBLE           = "DISPONIBLE"
    TRANSPORTISTA_ASIGNADO = "TRANSPORTISTA_ASIGNADO"
    EN_EJECUCION         = "EN_EJECUCION"
    COMPLETADO           = "COMPLETADO"
    CANCELADO            = "CANCELADO"
    REPROGRAMADO         = "REPROGRAMADO"


class EstadoDocEnum(str, enum.Enum):
    PENDIENTE  = "PENDIENTE"
    APROBADO   = "APROBADO"
    RECHAZADO  = "RECHAZADO"


# ── Tabla: usuarios ────────────────────────────────────────────────────────────

class Usuario(Base):
    __tablename__ = "usuarios"

    id              = Column(Integer, primary_key=True, index=True)
    cedula          = Column(String(13), unique=True, nullable=False, index=True)
    nombres         = Column(String(150), nullable=False)
    correo          = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    rol             = Column(Enum(RolEnum), nullable=False, default=RolEnum.TRANSPORTISTA)
    activo          = Column(Boolean, default=True, nullable=False)
    direccion       = Column(String(255), nullable=True)
    telefono        = Column(String(20), nullable=True)
    token_reset     = Column(String(255), nullable=True)       # para recuperar contraseña
    token_reset_exp = Column(DateTime, nullable=True)
    creado_en       = Column(DateTime, default=datetime.utcnow)
    actualizado_en  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relaciones
    transportista   = relationship("Transportista", back_populates="usuario", uselist=False)
    auditorias      = relationship("Auditoria", back_populates="usuario")


# ── Tabla: transportistas ──────────────────────────────────────────────────────

class Transportista(Base):
    __tablename__ = "transportistas"

    id             = Column(Integer, primary_key=True, index=True)
    usuario_id     = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    placa_vehiculo = Column(String(10), nullable=True)
    tipo_vehiculo  = Column(String(50), nullable=True)
    capacidad_ton  = Column(Numeric(10, 2), nullable=True)
    creado_en      = Column(DateTime, default=datetime.utcnow)

    usuario        = relationship("Usuario", back_populates="transportista")
    documentos     = relationship("Documento", back_populates="transportista", cascade="all, delete-orphan")
    viajes         = relationship("Viaje", back_populates="transportista")


# ── Tabla: documentos ─────────────────────────────────────────────────────────

class TipoDocEnum(str, enum.Enum):
    CEDULA          = "CEDULA"
    LICENCIA_E      = "LICENCIA_E"
    MATRICULA       = "MATRICULA"
    REVISION_TECNICA= "REVISION_TECNICA"
    SOAT            = "SOAT"
    PERMISO_PESOS   = "PERMISO_PESOS"


class Documento(Base):
    __tablename__ = "documentos"

    id               = Column(Integer, primary_key=True, index=True)
    transportista_id = Column(Integer, ForeignKey("transportistas.id"), nullable=False)
    tipo             = Column(Enum(TipoDocEnum), nullable=False)
    ruta_archivo     = Column(String(500), nullable=False)
    nombre_archivo   = Column(String(255), nullable=False)
    estado           = Column(Enum(EstadoDocEnum), default=EstadoDocEnum.PENDIENTE)
    fecha_vencimiento= Column(DateTime, nullable=True)
    observacion      = Column(Text, nullable=True)
    revisado_por_id  = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    subido_en        = Column(DateTime, default=datetime.utcnow)
    revisado_en      = Column(DateTime, nullable=True)

    transportista    = relationship("Transportista", back_populates="documentos")
    revisado_por     = relationship("Usuario", foreign_keys=[revisado_por_id])


# ── Tabla: viajes ─────────────────────────────────────────────────────────────

class Viaje(Base):
    __tablename__ = "viajes"

    id                  = Column(Integer, primary_key=True, index=True)
    codigo              = Column(String(20), unique=True, nullable=False, index=True)
    transportista_id    = Column(Integer, ForeignKey("transportistas.id"), nullable=True)
    creado_por_id       = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Datos de carga
    tipo_mercancia      = Column(String(100), nullable=False)
    peso_total_kg       = Column(Numeric(12, 2), nullable=False)
    dimensiones         = Column(String(100), nullable=True)    # "LxWxH"
    numero_contenedor   = Column(String(50), nullable=True)
    peso_contenedor_kg  = Column(Numeric(12, 2), nullable=True)

    # Ruta
    origen              = Column(String(255), nullable=False)
    destino             = Column(String(255), nullable=False)
    ruta_json           = Column(Text, nullable=True)           # GeoJSON de la ruta

    # Punto de recepción
    punto_recepcion     = Column(String(255), nullable=True)    # almacén o puerto

    # Destinatario
    destinatario_nombre = Column(String(200), nullable=True)
    destinatario_tel    = Column(String(20), nullable=True)
    destinatario_correo = Column(String(200), nullable=True)

    # Estado y fechas
    estado              = Column(Enum(EstadoViajeEnum), default=EstadoViajeEnum.DISPONIBLE)
    fecha_salida        = Column(DateTime, nullable=True)
    fecha_llegada_est   = Column(DateTime, nullable=True)
    fecha_llegada_real  = Column(DateTime, nullable=True)
    horas_retraso       = Column(Numeric(6, 2), default=0)
    causa_retraso       = Column(String(255), nullable=True)
    causa_cancelacion   = Column(String(255), nullable=True)

    observaciones       = Column(Text, nullable=True)
    creado_en           = Column(DateTime, default=datetime.utcnow)
    actualizado_en      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transportista       = relationship("Transportista", back_populates="viajes")
    creado_por          = relationship("Usuario", foreign_keys=[creado_por_id])
    auditorias          = relationship("Auditoria", back_populates="viaje")


# ── Tabla: auditoria ──────────────────────────────────────────────────────────

class Auditoria(Base):
    __tablename__ = "auditoria"

    id          = Column(BigInteger, primary_key=True, index=True)
    usuario_id  = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    viaje_id    = Column(Integer, ForeignKey("viajes.id"), nullable=True)
    accion      = Column(String(100), nullable=False)   # ej. "LOGIN", "CREAR_VIAJE"
    descripcion = Column(Text, nullable=True)
    ip_address  = Column(String(45), nullable=True)
    fecha       = Column(DateTime, default=datetime.utcnow, nullable=False)

    usuario     = relationship("Usuario", back_populates="auditorias")
    viaje       = relationship("Viaje", back_populates="auditorias")