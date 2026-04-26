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
from datetime import datetime
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
    CancelarViajeRequest, ModificarRutaRequest,
    PlanificarRutaRequest, ReprogramarViajeRequest,
    ViajeCreate, ViajeOut, ViajeUpdate,
)
from utils.auditoria import registrar_auditoria

router = APIRouter(prefix="/api/viajes", tags=["Viajes"])


# ── helpers ────────────────────────────────────────────────────────────────────

def _generar_codigo() -> str:
    """Genera un código único de viaje tipo TC-YYYYMMDD-XXXX"""
    sufijo = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"TC-{datetime.utcnow().strftime('%Y%m%d')}-{sufijo}"


def _viaje_out(v: Viaje) -> dict:
    nombres = None
    if v.transportista:
        nombres = v.transportista.usuario.nombres
    return {
        "id": v.id,
        "codigo": v.codigo,
        "estado": v.estado,
        "tipo_mercancia": v.tipo_mercancia,
        "peso_total_kg": float(v.peso_total_kg),
        "dimensiones": v.dimensiones,
        "numero_contenedor": v.numero_contenedor,
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
        "ruta_json": v.ruta_json,
        "creado_en": v.creado_en,
    }


def _verificar_docs_transportista(t: Transportista, db: Session) -> bool:
    """Verifica que el transportista tiene todos los docs aprobados."""
    tipos_requeridos = {"CEDULA", "LICENCIA_E", "MATRICULA", "REVISION_TECNICA", "SOAT"}
    docs_aprobados = {
        d.tipo for d in t.documentos if d.estado == EstadoDocEnum.APROBADO
    }
    return tipos_requeridos.issubset(docs_aprobados)


# ── RF-5.1  Crear Viaje ───────────────────────────────────────────────────────

@router.post("/", status_code=201)
def crear_viaje(
    body: ViajeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("SECRETARIA", "GERENTE")),
    request: Request = None,
):
    # validar número de contenedor si se provee
    if body.numero_contenedor:
        import re
        if not re.match(r"^[A-Z]{4}\d{7}$", body.numero_contenedor.upper()):
            raise HTTPException(
                400,
                "Formato de contenedor inválido. Debe ser 4 letras + 7 dígitos (ej. MSCU1234567)",
            )

    viaje = Viaje(
        codigo=_generar_codigo(),
        creado_por_id=current_user.id,
        tipo_mercancia=body.tipo_mercancia,
        peso_total_kg=body.peso_total_kg,
        dimensiones=body.dimensiones,
        numero_contenedor=body.numero_contenedor.upper() if body.numero_contenedor else None,
        peso_contenedor_kg=body.peso_contenedor_kg,
        origen=body.origen,
        destino=body.destino,
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

    # transportista solo ve sus propios viajes y los disponibles
    if current_user.rol == "TRANSPORTISTA":
        t = db.query(Transportista).filter(Transportista.usuario_id == current_user.id).first()
        if t:
            q = q.filter(
                (Viaje.transportista_id == t.id) |
                (Viaje.estado == EstadoViajeEnum.DISPONIBLE)
            )

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
    if not body.causa:
        raise HTTPException(400, "Debe especificar una causa de reprogramación")

    v.horas_retraso = body.horas_retraso
    v.causa_retraso = body.causa
    v.estado = EstadoViajeEnum.REPROGRAMADO
    if v.fecha_llegada_est:
        from datetime import timedelta
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
        raise HTTPException(409, f"No se puede cancelar un viaje en estado {v.estado}")

    v.estado = EstadoViajeEnum.CANCELADO
    v.causa_cancelacion = body.causa_cancelacion
    db.commit()

    registrar_auditoria(
        db, "CANCELAR_VIAJE", usuario_id=current_user.id, viaje_id=viaje_id,
        descripcion=f"Viaje {v.codigo} cancelado. Causa: {body.causa_cancelacion}",
        ip_address=request.client.host if request else None,
    )
    return _viaje_out(v)


# ── RF-5.5  Asignar Transportista al Viaje ────────────────────────────────────

@router.patch("/{viaje_id}/asignar")
def asignar_transportista(
    viaje_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("TRANSPORTISTA")),
    request: Request = None,
):
    v = db.query(Viaje).filter(Viaje.id == viaje_id).first()
    if not v:
        raise HTTPException(404, "Viaje no encontrado")

    if v.estado != EstadoViajeEnum.DISPONIBLE:
        raise HTTPException(409, "Viaje no disponible")

    t = db.query(Transportista).filter(Transportista.usuario_id == current_user.id).first()
    if not t:
        raise HTTPException(404, "Perfil de transportista no encontrado")

    if not t.usuario.activo:
        raise HTTPException(403, "Su cuenta no está activa")

    if not _verificar_docs_transportista(t, db):
        raise HTTPException(
            403,
            "Su documentación no está completa o aprobada. "
            "Suba y espere aprobación de todos los documentos requeridos.",
        )

    # verificar que no tiene otro viaje en ejecución
    en_ejecucion = (
        db.query(Viaje)
        .filter(
            Viaje.transportista_id == t.id,
            Viaje.estado.in_([EstadoViajeEnum.EN_EJECUCION, EstadoViajeEnum.TRANSPORTISTA_ASIGNADO]),
        )
        .first()
    )
    if en_ejecucion:
        raise HTTPException(409, "Ya tiene un viaje asignado o en ejecución")

    v.transportista_id = t.id
    v.estado = EstadoViajeEnum.TRANSPORTISTA_ASIGNADO
    db.commit()

    registrar_auditoria(
        db, "ASIGNAR_TRANSPORTISTA", usuario_id=current_user.id, viaje_id=viaje_id,
        descripcion=f"Transportista {current_user.nombres} asignado al viaje {v.codigo}",
        ip_address=request.client.host if request else None,
    )
    return _viaje_out(v)


# ── RF-5.6  Planificar Ruta ───────────────────────────────────────────────────

@router.patch("/{viaje_id}/ruta")
def planificar_ruta(
    viaje_id: int,
    body: PlanificarRutaRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("SECRETARIA", "GERENTE")),
    request: Request = None,
):
    v = db.query(Viaje).filter(Viaje.id == viaje_id).first()
    if not v:
        raise HTTPException(404, "Viaje no encontrado")

    if not body.origen or not body.destino:
        raise HTTPException(400, "Origen y destino son obligatorios para planificar la ruta")

    v.origen = body.origen
    v.destino = body.destino
    v.ruta_json = body.ruta_json
    db.commit()

    registrar_auditoria(
        db, "PLANIFICAR_RUTA", usuario_id=current_user.id, viaje_id=viaje_id,
        descripcion=f"Ruta planificada: {body.origen} → {body.destino}",
        ip_address=request.client.host if request else None,
    )
    return _viaje_out(v)