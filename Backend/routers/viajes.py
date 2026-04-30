"""
RF-5.1  Crear Viajes
RF-5.2  Cancelar Viajes
RF-5.3  Consultar Viajes
RF-5.4  Reprogramar Viajes
RF-5.5  Asignar Transportista al Viaje
RF-5.6  Planificar Ruta
"""
import random
import string
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.security import get_current_user, require_roles
from database import get_db
from models.models import (
    Documento, EstadoDocEnum, EstadoViajeEnum,
    Transportista, Usuario, Viaje,
)
from schemas.viaje_schemas import (
    AsignarTransportistaRequest,  # ⚠️ NUEVO SCHEMA (agregar abajo)
    CancelarViajeRequest,
    PlanificarRutaRequest,
    ReprogramarViajeRequest,
    ViajeCreate,
    ViajeUpdate,
)
from utils.auditoria import registrar_auditoria

router = APIRouter(prefix="/api/viajes", tags=["Viajes"])


# ── helpers ────────────────────────────────────────────────────────────────────

def _generar_codigo() -> str:
    """Genera un código único de viaje tipo VJ-YYYYMMDD-XXXX"""
    sufijo = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"VJ-{datetime.utcnow().strftime('%Y%m%d')}-{sufijo}"


def _extraer_estado(estado) -> str:
    """Extrae el valor string de un Enum de SQLAlchemy"""
    return estado.value if hasattr(estado, 'value') else str(estado)


def _viaje_out(v: Viaje) -> dict:
    nombres = v.transportista.usuario.nombres if v.transportista else None
    placa = v.transportista.placa_vehiculo if v.transportista else None
    return {
        "id": v.id,
        "codigo": v.codigo,
        "estado": _extraer_estado(v.estado),
        "tipo_mercancia": v.tipo_mercancia,
        "peso_total_kg": float(v.peso_total_kg) if v.peso_total_kg else 0,
        "dimensiones": v.dimensiones,
        "numero_contenedor": v.numero_contenedor,
        "peso_contenedor_kg": float(v.peso_contenedor_kg) if v.peso_contenedor_kg else None,
        "origen": v.origen,
        "destino": v.destino,
        "punto_recepcion": v.punto_recepcion,
        "destinatario_nombre": v.destinatario_nombre,
        "destinatario_tel": v.destinatario_tel,
        "destinatario_correo": v.destinatario_correo,
        "fecha_salida": v.fecha_salida,
        "fecha_llegada_est": v.fecha_llegada_est,
        "fecha_llegada_real": v.fecha_llegada_real,
        "horas_retraso": float(v.horas_retraso) if v.horas_retraso else 0,
        "causa_retraso": v.causa_retraso,
        "causa_cancelacion": v.causa_cancelacion,
        "observaciones": v.observaciones,
        "transportista_id": v.transportista_id,
        "transportista_nombres": nombres,
        "placa_vehiculo": placa,
        "ruta_json": v.ruta_json,
        "creado_en": v.creado_en,
        "actualizado_en": v.actualizado_en,
    }


def _verificar_docs_transportista(t: Transportista) -> bool:
    """
    Verifica que el transportista tiene TODOS los 6 documentos aprobados.
    ⚠️ CORRECCIÓN: Ahora incluye PERMISO_PESOS (el front lo exige).
    """
    tipos_requeridos = {"CEDULA", "LICENCIA_E", "MATRICULA", "REVISION_TECNICA", "SOAT", "PERMISO_PESOS"}
    
    docs_aprobados = set()
    for d in t.documentos:
        estado_doc = _extraer_estado(d.estado)
        tipo_doc = _extraer_estado(d.tipo)
        if estado_doc == "APROBADO":
            docs_aprobados.add(tipo_doc)
    
    return tipos_requeridos.issubset(docs_aprobados)


# ── RF-5.1  Crear Viaje ───────────────────────────────────────────────────────

@router.post("/", status_code=201)
def crear_viaje(
    body: ViajeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("SECRETARIA", "GERENTE")),
    request: Request = None,
):
    import re
    
    # Validar contenedor
    if body.numero_contenedor:
        if not re.match(r"^[A-Z]{4}\d{7}$", body.numero_contenedor.upper()):
            raise HTTPException(
                400,
                "Formato de contenedor inválido. Debe ser 4 letras + 7 dígitos (ej. MSCU1234567)",
            )
    
    # Validar origen != destino
    if body.origen.strip().upper() == body.destino.strip().upper():
        raise HTTPException(400, "El origen y destino no pueden ser iguales")

    viaje = Viaje(
        codigo=_generar_codigo(),
        creado_por_id=current_user.id,
        tipo_mercancia=body.tipo_mercancia,
        peso_total_kg=body.peso_total_kg,
        dimensiones=body.dimensiones,
        numero_contenedor=body.numero_contenedor.upper() if body.numero_contenedor else None,
        peso_contenedor_kg=body.peso_contenedor_kg,
        origen=body.origen.upper(),
        destino=body.destino.upper(),
        punto_recepcion=body.punto_recepcion,
        destinatario_nombre=body.destinatario_nombre,
        destinatario_tel=body.destinatario_tel,
        destinatario_correo=body.destinatario_correo,
        fecha_salida=body.fecha_salida,
        fecha_llegada_est=body.fecha_llegada_est,
        observaciones=body.observaciones,
        estado=EstadoViajeEnum.DISPONIBLE,
    )
    db.add(viaje)
    db.commit()
    db.refresh(viaje)

    registrar_auditoria(
        db, "CREAR_VIAJE", usuario_id=current_user.id, viaje_id=viaje.id,
        descripcion=f"Viaje {viaje.codigo} creado. {body.origen} → {body.destino}",
        ip_address=request.client.host if request else None,
    )
    return _viaje_out(viaje)


# ── RF-5.3  Consultar Viajes ──────────────────────────────────────────────────

@router.get("/")
def listar_viajes(
    estado: Optional[str] = None,
    transportista_id: Optional[int] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(Viaje)

    if estado:
        q = q.filter(Viaje.estado == estado)
    if transportista_id:
        q = q.filter(Viaje.transportista_id == transportista_id)
    if fecha_desde:
        q = q.filter(Viaje.fecha_salida >= datetime.fromisoformat(fecha_desde))
    if fecha_hasta:
        q = q.filter(Viaje.fecha_salida <= datetime.fromisoformat(fecha_hasta))

    # Transportista SOLO ve sus propios viajes (no los DISPONIBLES)
    rol_usuario = current_user.rol.value if hasattr(current_user.rol, 'value') else current_user.rol
    if rol_usuario == "TRANSPORTISTA":
        t = db.query(Transportista).filter(Transportista.usuario_id == current_user.id).first()
        if t:
            q = q.filter(Viaje.transportista_id == t.id)
        else:
            return []

    viajes = q.order_by(Viaje.fecha_salida.desc()).all()
    return [_viaje_out(v) for v in viajes]


@router.get("/{viaje_id}")
def obtener_viaje(
    viaje_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    v = db.query(Viaje).filter(Viaje.id == viaje_id).first()
    if not v:
        raise HTTPException(404, "Viaje no encontrado")
    return _viaje_out(v)


# ── RF-5.5  Asignar Transportista al Viaje (LA SECRETARIA ASIGNA) ─────────────

@router.patch("/{viaje_id}/asignar")
def asignar_transportista(
    viaje_id: int,
    body: AsignarTransportistaRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("SECRETARIA")),  # ⚠️ CORREGIDO: Solo Secretaria
    request: Request = None,
):
    """
    La Secretaria asigna un transportista aprobado a un viaje DISPONIBLE.
    """
    v = db.query(Viaje).filter(Viaje.id == viaje_id).first()
    if not v:
        raise HTTPException(404, "Viaje no encontrado")

    if v.estado != EstadoViajeEnum.DISPONIBLE:
        raise HTTPException(
            409,
            f"El viaje no está disponible para asignación (estado: {_extraer_estado(v.estado)})"
        )

    # Buscar transportista
    t = db.query(Transportista).filter(Transportista.id == body.transportista_id).first()
    if not t:
        raise HTTPException(404, "Transportista no encontrado")

    if not t.usuario.activo:
        raise HTTPException(403, "El transportista no está activo")

    if not _verificar_docs_transportista(t):
        raise HTTPException(
            403,
            "El transportista no tiene toda su documentación aprobada. "
            "Se requieren: CÉDULA, LICENCIA_E, MATRÍCULA, REVISIÓN_TÉCNICA, SOAT y PERMISO_PESOS."
        )

    # Verificar que no tiene otro viaje activo
    en_ejecucion = (
        db.query(Viaje)
        .filter(
            Viaje.transportista_id == t.id,
            Viaje.estado.in_([
                EstadoViajeEnum.EN_EJECUCION,
                EstadoViajeEnum.TRANSPORTISTA_ASIGNADO,
            ]),
        )
        .first()
    )
    if en_ejecucion:
        raise HTTPException(
            409,
            f"El transportista ya tiene un viaje activo: {en_ejecucion.codigo}"
        )

    v.transportista_id = t.id
    v.estado = EstadoViajeEnum.TRANSPORTISTA_ASIGNADO
    db.commit()
    db.refresh(v)

    registrar_auditoria(
        db, "ASIGNAR_TRANSPORTISTA", usuario_id=current_user.id, viaje_id=viaje_id,
        descripcion=(
            f"Transportista {t.usuario.nombres} ({t.usuario.cedula}) "
            f"asignado al viaje {v.codigo}"
        ),
        ip_address=request.client.host if request else None,
    )
    return _viaje_out(v)


# ── RF-5.4  Reprogramar Viajes ────────────────────────────────────────────────

@router.patch("/{viaje_id}/reprogramar")
def reprogramar_viaje(
    viaje_id: int,
    body: ReprogramarViajeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("SECRETARIA", "GERENTE")),
    request: Request = None,
):
    v = db.query(Viaje).filter(Viaje.id == viaje_id).first()
    if not v:
        raise HTTPException(404, "Viaje no encontrado")

    if body.horas_retraso <= 0:
        raise HTTPException(400, "Las horas de retraso deben ser un valor positivo")
    if not body.causa or len(body.causa.strip()) < 5:
        raise HTTPException(400, "Debe especificar una causa de reprogramación (mínimo 5 caracteres)")

    v.horas_retraso = body.horas_retraso
    v.causa_retraso = body.causa
    v.estado = EstadoViajeEnum.REPROGRAMADO
    if v.fecha_llegada_est:
        v.fecha_llegada_est = v.fecha_llegada_est + timedelta(hours=body.horas_retraso)

    db.commit()

    registrar_auditoria(
        db, "REPROGRAMAR_VIAJE", usuario_id=current_user.id, viaje_id=viaje_id,
        descripcion=f"Viaje {v.codigo} reprogramado. Retraso: {body.horas_retraso}h. Causa: {body.causa}",
        ip_address=request.client.host if request else None,
    )
    return _viaje_out(v)


# ── RF-5.2  Cancelar Viajes ───────────────────────────────────────────────────

@router.patch("/{viaje_id}/cancelar")
def cancelar_viaje(
    viaje_id: int,
    body: CancelarViajeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("SECRETARIA", "GERENTE")),
    request: Request = None,
):
    v = db.query(Viaje).filter(Viaje.id == viaje_id).first()
    if not v:
        raise HTTPException(404, "Viaje no encontrado")

    estados_no_cancelables = [EstadoViajeEnum.COMPLETADO, EstadoViajeEnum.CANCELADO]
    if v.estado in estados_no_cancelables:
        raise HTTPException(
            409,
            f"No se puede cancelar un viaje en estado {_extraer_estado(v.estado)}"
        )

    if not body.causa_cancelacion or len(body.causa_cancelacion.strip()) < 10:
        raise HTTPException(
            400,
            "Debe proporcionar una causa de cancelación detallada (mínimo 10 caracteres)"
        )

    v.estado = EstadoViajeEnum.CANCELADO
    v.causa_cancelacion = body.causa_cancelacion
    db.commit()

    registrar_auditoria(
        db, "CANCELAR_VIAJE", usuario_id=current_user.id, viaje_id=viaje_id,
        descripcion=f"Viaje {v.codigo} cancelado. Causa: {body.causa_cancelacion}",
        ip_address=request.client.host if request else None,
    )
    return _viaje_out(v)


# ── RF-5.6  Planificar Ruta ───────────────────────────────────────────────────

@router.patch("/{viaje_id}/planificar-ruta")
def planificar_ruta(
    viaje_id: int,
    body: PlanificarRutaRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("SECRETARIA", "GERENTE")),
    request: Request = None,
):
    """
    Planificar/detallar la ruta de un viaje.
    NOTA: Cambié la ruta a /planificar-ruta para no colisionar con el PATCH
    de modificar ruta del monitoreo.
    """
    v = db.query(Viaje).filter(Viaje.id == viaje_id).first()
    if not v:
        raise HTTPException(404, "Viaje no encontrado")

    if not body.origen or not body.destino:
        raise HTTPException(400, "Origen y destino son obligatorios para planificar la ruta")

    v.origen = body.origen.upper()
    v.destino = body.destino.upper()
    v.ruta_json = body.ruta_json
    db.commit()

    registrar_auditoria(
        db, "PLANIFICAR_RUTA", usuario_id=current_user.id, viaje_id=viaje_id,
        descripcion=f"Ruta planificada: {body.origen} → {body.destino}",
        ip_address=request.client.host if request else None,
    )
    return _viaje_out(v)


# ── Actualizar Viaje (genérico) ───────────────────────────────────────────────

@router.patch("/{viaje_id}")
def actualizar_viaje(
    viaje_id: int,
    body: ViajeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("SECRETARIA", "GERENTE")),
    request: Request = None,
):
    v = db.query(Viaje).filter(Viaje.id == viaje_id).first()
    if not v:
        raise HTTPException(404, "Viaje no encontrado")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(v, field, value)

    db.commit()
    db.refresh(v)

    registrar_auditoria(
        db, "ACTUALIZAR_VIAJE", usuario_id=current_user.id, viaje_id=viaje_id,
        descripcion=f"Viaje {v.codigo} actualizado",
        ip_address=request.client.host if request else None,
    )
    return _viaje_out(v)