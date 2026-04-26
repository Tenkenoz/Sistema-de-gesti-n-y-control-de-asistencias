"""
RF-6.1  Controlar Viaje
RF-6.2  Modificar Ruta
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.security import get_current_user, require_roles
from database import get_db
from models.models import EstadoViajeEnum, Transportista, Viaje
from schemas.viaje_schemas import ModificarRutaRequest
from utils.auditoria import registrar_auditoria

router = APIRouter(prefix="/api/monitoreo", tags=["Monitoreo"])


def _viaje_monitoreo(v: Viaje) -> dict:
    nombres = v.transportista.usuario.nombres if v.transportista else None
    placa = v.transportista.placa_vehiculo if v.transportista else None
    return {
        "id": v.id,
        "codigo": v.codigo,
        "estado": v.estado,
        "origen": v.origen,
        "destino": v.destino,
        "ruta_json": v.ruta_json,
        "fecha_salida": v.fecha_salida,
        "fecha_llegada_est": v.fecha_llegada_est,
        "horas_retraso": float(v.horas_retraso) if v.horas_retraso else 0,
        "transportista_nombres": nombres,
        "placa_vehiculo": placa,
        "observaciones": v.observaciones,
    }


# ── RF-6.1  Controlar Viaje ───────────────────────────────────────────────────

@router.get("/viajes-en-ejecucion")
def viajes_en_ejecucion(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("COORDINADOR", "GERENTE", "PRESIDENTE")),
):
    """Lista todos los viajes activos para monitoreo, priorizando sin revisión."""
    viajes = (
        db.query(Viaje)
        .filter(Viaje.estado.in_([
            EstadoViajeEnum.EN_EJECUCION,
            EstadoViajeEnum.TRANSPORTISTA_ASIGNADO,
        ]))
        .order_by(Viaje.fecha_salida)
        .all()
    )
    return [_viaje_monitoreo(v) for v in viajes]


@router.post("/viajes/{viaje_id}/iniciar")
def iniciar_viaje(
    viaje_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("COORDINADOR", "SECRETARIA")),
    request: Request = None,
):
    v = db.query(Viaje).filter(Viaje.id == viaje_id).first()
    if not v:
        raise HTTPException(404, "Viaje no encontrado")
    if v.estado != EstadoViajeEnum.TRANSPORTISTA_ASIGNADO:
        raise HTTPException(409, f"El viaje no está listo para iniciar (estado: {v.estado})")

    v.estado = EstadoViajeEnum.EN_EJECUCION
    v.fecha_salida = v.fecha_salida or datetime.utcnow()
    db.commit()

    registrar_auditoria(
        db, "INICIAR_VIAJE", usuario_id=current_user.id, viaje_id=viaje_id,
        descripcion=f"Viaje {v.codigo} iniciado",
        ip_address=request.client.host if request else None,
    )
    return _viaje_monitoreo(v)


@router.post("/viajes/{viaje_id}/completar")
def completar_viaje(
    viaje_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("COORDINADOR", "SECRETARIA")),
    request: Request = None,
):
    v = db.query(Viaje).filter(Viaje.id == viaje_id).first()
    if not v:
        raise HTTPException(404, "Viaje no encontrado")
    if v.estado != EstadoViajeEnum.EN_EJECUCION:
        raise HTTPException(409, "El viaje no está en ejecución")

    v.estado = EstadoViajeEnum.COMPLETADO
    v.fecha_llegada_real = datetime.utcnow()
    db.commit()

    registrar_auditoria(
        db, "COMPLETAR_VIAJE", usuario_id=current_user.id, viaje_id=viaje_id,
        descripcion=f"Viaje {v.codigo} completado",
        ip_address=request.client.host if request else None,
    )
    return _viaje_monitoreo(v)


# ── RF-6.2  Modificar Ruta ────────────────────────────────────────────────────

@router.patch("/viajes/{viaje_id}/ruta")
def modificar_ruta(
    viaje_id: int,
    body: ModificarRutaRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("COORDINADOR")),
    request: Request = None,
):
    v = db.query(Viaje).filter(Viaje.id == viaje_id).first()
    if not v:
        raise HTTPException(404, "Viaje no encontrado")
    if v.estado != EstadoViajeEnum.EN_EJECUCION:
        raise HTTPException(409, "Solo se puede modificar la ruta de un viaje en ejecución")

    if not body.nueva_ruta_json:
        raise HTTPException(400, "La nueva ruta no puede estar vacía")

    v.ruta_json = body.nueva_ruta_json
    db.commit()

    registrar_auditoria(
        db, "MODIFICAR_RUTA", usuario_id=current_user.id, viaje_id=viaje_id,
        descripcion=f"Ruta modificada para viaje {v.codigo}. Motivo: {body.motivo}",
        ip_address=request.client.host if request else None,
    )
    return _viaje_monitoreo(v)


# ── Pista de auditoría (solo admin) ───────────────────────────────────────────

@router.get("/auditoria")
def ver_auditoria(
    viaje_id: Optional[int] = None,
    usuario_id: Optional[int] = None,
    limite: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("GERENTE", "PRESIDENTE")),
):
    from models.models import Auditoria
    q = db.query(Auditoria)
    if viaje_id:
        q = q.filter(Auditoria.viaje_id == viaje_id)
    if usuario_id:
        q = q.filter(Auditoria.usuario_id == usuario_id)
    registros = q.order_by(Auditoria.fecha.desc()).limit(limite).all()
    return [
        {
            "id": r.id,
            "accion": r.accion,
            "descripcion": r.descripcion,
            "usuario_id": r.usuario_id,
            "viaje_id": r.viaje_id,
            "ip": r.ip_address,
            "fecha": r.fecha,
        }
        for r in registros
    ]