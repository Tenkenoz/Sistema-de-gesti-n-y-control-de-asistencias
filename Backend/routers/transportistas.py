"""
RF-4.1  Crear Transportista
RF-4.2  Editar Transportista
RF-4.3  Eliminar Transportista (Desactivar)
RF-4.3b Activar Transportista
RF-4.3c Eliminar Permanentemente
RF-4.4  Importar Documentación (Individual) — PDF guardado en BD (BYTEA)
RF-4.5  Consultar y Revisar Documentos
"""
import os
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter, Depends, File, Form,
    HTTPException, Request, UploadFile, status,
)
from fastapi.responses import Response          # ← para servir bytes desde BD
from sqlalchemy.orm import Session

from core.config import settings
from core.security import get_current_user, require_roles
from database import get_db
from models.models import Documento, EstadoDocEnum, Transportista, Usuario, Viaje, EstadoViajeEnum
from schemas.transportista_schemas import (
    EliminarTransportistaRequest,
    RevisionDocumentoRequest,
    TransportistaUpdate,
)
from utils.auditoria import registrar_auditoria

router = APIRouter(prefix="/api/transportistas", tags=["Transportistas"])


# ── helpers ────────────────────────────────────────────────────────────────────

def _extraer_estado(estado) -> str:
    return estado.value if hasattr(estado, 'value') else str(estado)


def _estado_documentacion(docs: list) -> str:
    if not docs:
        return "SIN_DOCS"
    estados = {_extraer_estado(d.estado) for d in docs}
    if "RECHAZADO" in estados:
        return "RECHAZADO"
    if "PENDIENTE" in estados:
        return "PENDIENTE"
    return "APROBADO"


def _build_out(t: Transportista) -> dict:
    return {
        "id": t.id,
        "usuario_id": t.usuario_id,
        "cedula": t.usuario.cedula,
        "nombres": t.usuario.nombres,
        "correo": t.usuario.correo,
        "telefono": t.usuario.telefono,
        "direccion": t.usuario.direccion,
        "placa_vehiculo": t.placa_vehiculo,
        "tipo_vehiculo": t.tipo_vehiculo,
        "capacidad_ton": float(t.capacidad_ton) if t.capacidad_ton else None,
        "activo": t.usuario.activo,
        "documentos": [
            {
                "id": d.id,
                "tipo": _extraer_estado(d.tipo),
                "nombre_archivo": d.nombre_archivo,
                "estado": _extraer_estado(d.estado),
                "fecha_vencimiento": d.fecha_vencimiento,
                "observacion": d.observacion,
                "subido_en": d.subido_en,
                "revisado_en": d.revisado_en,
                # indica si el PDF ya está guardado en BD
                "tiene_archivo": d.contenido_pdf is not None,
            }
            for d in t.documentos
        ],
        "estado_documentacion": _estado_documentacion(t.documentos),
    }


# ── RF-4.1  Crear Transportista ───────────────────────────────────────────────

@router.post("/", status_code=201)
def crear_transportista(
    cedula: str = Form(...),
    nombres: str = Form(...),
    correo: str = Form(...),
    password: str = Form(...),
    placa_vehiculo: Optional[str] = Form(None),
    tipo_vehiculo: Optional[str] = Form(None),
    capacidad_ton: Optional[float] = Form(None),
    direccion: Optional[str] = Form(None),
    telefono: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("COORDINADOR")),
    request: Request = None,
):
    from core.security import hash_password

    if db.query(Usuario).filter(Usuario.correo == correo).first():
        raise HTTPException(400, "El correo ya está registrado")
    if db.query(Usuario).filter(Usuario.cedula == cedula).first():
        raise HTTPException(400, "La cédula ya está registrada")

    usuario = Usuario(
        cedula=cedula, nombres=nombres, correo=correo,
        hashed_password=hash_password(password),
        rol="TRANSPORTISTA", direccion=direccion, telefono=telefono,
    )
    db.add(usuario)
    db.flush()

    trans = Transportista(
        usuario_id=usuario.id,
        placa_vehiculo=placa_vehiculo,
        tipo_vehiculo=tipo_vehiculo,
        capacidad_ton=capacidad_ton,
    )
    db.add(trans)
    db.commit()
    db.refresh(trans)

    registrar_auditoria(
        db, "CREAR_TRANSPORTISTA", usuario_id=current_user.id,
        descripcion=f"Transportista creado: {nombres} ({cedula})",
        ip_address=request.client.host if request else None,
    )
    return _build_out(trans)


# ── Listar Transportistas ─────────────────────────────────────────────────────

@router.get("/")
def listar_transportistas(
    solo_activos: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Transportista).join(Transportista.usuario)
    if solo_activos:
        query = query.filter(Usuario.activo == True)
    lista = query.order_by(Usuario.nombres).all()
    return [_build_out(t) for t in lista]


@router.get("/{transportista_id}")
def obtener_transportista(
    transportista_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    t = db.query(Transportista).filter(Transportista.id == transportista_id).first()
    if not t:
        raise HTTPException(404, "Transportista no encontrado")
    return _build_out(t)


# ── RF-4.2  Editar Transportista ──────────────────────────────────────────────

@router.put("/{transportista_id}")
def editar_transportista(
    transportista_id: int,
    body: TransportistaUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("COORDINADOR")),
    request: Request = None,
):
    t = db.query(Transportista).filter(Transportista.id == transportista_id).first()
    if not t:
        raise HTTPException(404, "Transportista no encontrado")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(t, field, value)

    db.commit()
    db.refresh(t)

    registrar_auditoria(
        db, "EDITAR_TRANSPORTISTA", usuario_id=current_user.id,
        descripcion=f"Editado transportista id={transportista_id}",
        ip_address=request.client.host if request else None,
    )
    return _build_out(t)


# ── RF-4.3  Desactivar Transportista ─────────────────────────────────────────

@router.delete("/{transportista_id}")
def desactivar_transportista(
    transportista_id: int,
    body: EliminarTransportistaRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("COORDINADOR")),
    request: Request = None,
):
    t = db.query(Transportista).filter(Transportista.id == transportista_id).first()
    if not t:
        raise HTTPException(404, "Transportista no encontrado")

    en_ejecucion = (
        db.query(Viaje)
        .filter(
            Viaje.transportista_id == transportista_id,
            Viaje.estado == EstadoViajeEnum.EN_EJECUCION,
        )
        .first()
    )
    if en_ejecucion:
        raise HTTPException(409, "El transportista tiene viajes en ejecución. No se puede desactivar.")

    t.usuario.activo = False
    db.commit()

    registrar_auditoria(
        db, "DESACTIVAR_TRANSPORTISTA", usuario_id=current_user.id,
        descripcion=f"Transportista id={transportista_id} desactivado. Razón: {body.razon}. {body.observaciones or ''}",
        ip_address=request.client.host if request else None,
    )
    return {"mensaje": "Transportista desactivado correctamente"}


# ── RF-4.3b  Activar Transportista ────────────────────────────────────────────

@router.patch("/{transportista_id}/activar")
def activar_transportista(
    transportista_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("COORDINADOR")),
    request: Request = None,
):
    t = db.query(Transportista).filter(Transportista.id == transportista_id).first()
    if not t:
        raise HTTPException(404, "Transportista no encontrado")

    t.usuario.activo = True
    db.commit()

    registrar_auditoria(
        db, "ACTIVAR_TRANSPORTISTA", usuario_id=current_user.id,
        descripcion=f"Transportista id={transportista_id} activado",
        ip_address=request.client.host if request else None,
    )
    return {"mensaje": "Transportista activado correctamente"}


# ── RF-4.3c  Eliminar Permanentemente ─────────────────────────────────────────

@router.delete("/{transportista_id}/permanente")
def eliminar_permanentemente(
    transportista_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("COORDINADOR")),
    request: Request = None,
):
    t = db.query(Transportista).filter(Transportista.id == transportista_id).first()
    if not t:
        raise HTTPException(404, "Transportista no encontrado")

    en_ejecucion = (
        db.query(Viaje)
        .filter(
            Viaje.transportista_id == transportista_id,
            Viaje.estado.in_([EstadoViajeEnum.EN_EJECUCION, EstadoViajeEnum.TRANSPORTISTA_ASIGNADO]),
        )
        .first()
    )
    if en_ejecucion:
        raise HTTPException(409, "El transportista tiene viajes activos. No se puede eliminar permanentemente.")

    usuario = t.usuario
    db.query(Documento).filter(Documento.transportista_id == transportista_id).delete()
    db.delete(t)
    db.delete(usuario)
    db.commit()

    registrar_auditoria(
        db, "ELIMINAR_PERMANENTE", usuario_id=current_user.id,
        descripcion=f"Transportista id={transportista_id} eliminado permanentemente",
        ip_address=request.client.host if request else None,
    )
    return {"mensaje": "Transportista eliminado permanentemente"}


# ── RF-4.4  Importar Documentación — PDF se guarda en BD (BYTEA) ──────────────

@router.post("/{transportista_id}/documentos", status_code=201)
async def importar_documento(
    transportista_id: int,
    tipo: str = Form(...),
    fecha_vencimiento: Optional[str] = Form(None),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    request: Request = None,
):
    """
    Sube un PDF y lo persiste directamente en PostgreSQL como BYTEA.
    No se escribe ningún archivo en disco.
    """
    t = db.query(Transportista).filter(Transportista.id == transportista_id).first()
    if not t:
        raise HTTPException(404, "Transportista no encontrado")

    # Solo el propio transportista o roles administrativos pueden subir
    rol_usuario = _extraer_estado(current_user.rol)
    if rol_usuario == "TRANSPORTISTA" and t.usuario_id != current_user.id:
        raise HTTPException(403, "No tiene permiso para subir documentos de otro transportista")

    # Validar tipo
    tipos_validos = ["CEDULA", "LICENCIA_E", "MATRICULA", "REVISION_TECNICA", "SOAT", "PERMISO_PESOS"]
    if tipo not in tipos_validos:
        raise HTTPException(400, f"Tipo inválido. Válidos: {', '.join(tipos_validos)}")

    # Validar formato PDF
    if archivo.content_type != "application/pdf":
        raise HTTPException(400, "Solo se aceptan archivos en formato PDF")

    # Leer el contenido completo
    content: bytes = await archivo.read()

    # Validar tamaño (default 10 MB si no está en settings)
    max_bytes = getattr(settings, "MAX_FILE_SIZE_MB", 10) * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            400,
            f"El archivo excede el límite de {getattr(settings, 'MAX_FILE_SIZE_MB', 10)} MB"
        )

    # Nombre del archivo (para descarga posterior)
    nombre = f"{tipo}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{archivo.filename}"

    # Fecha de vencimiento
    venc = None
    if fecha_vencimiento:
        try:
            venc = datetime.fromisoformat(fecha_vencimiento)
        except ValueError:
            pass

    # Si ya existe un documento del mismo tipo → actualizar
    doc_existente = (
        db.query(Documento)
        .filter(
            Documento.transportista_id == transportista_id,
            Documento.tipo == tipo,
        )
        .first()
    )

    if doc_existente:
        doc_existente.nombre_archivo   = nombre
        doc_existente.contenido_pdf    = content          # ← bytes en BD
        doc_existente.ruta_archivo     = None             # ya no usamos disco
        doc_existente.estado           = EstadoDocEnum.PENDIENTE
        doc_existente.fecha_vencimiento = venc
        doc_existente.subido_en        = datetime.utcnow()
        doc_existente.revisado_en      = None
        doc_existente.observacion      = None
        doc_existente.revisado_por_id  = None
        doc = doc_existente
    else:
        doc = Documento(
            transportista_id=transportista_id,
            tipo=tipo,
            nombre_archivo=nombre,
            contenido_pdf=content,                        # ← bytes en BD
            ruta_archivo=None,
            estado=EstadoDocEnum.PENDIENTE,
            fecha_vencimiento=venc,
        )
        db.add(doc)

    db.commit()
    db.refresh(doc)

    registrar_auditoria(
        db, "SUBIR_DOCUMENTO", usuario_id=current_user.id,
        descripcion=f"Documento {tipo} subido para transportista id={transportista_id} ({len(content) // 1024} KB)",
        ip_address=request.client.host if request else None,
    )
    return {
        "mensaje": "Documento subido y guardado en base de datos correctamente",
        "documento_id": doc.id,
        "nombre_archivo": doc.nombre_archivo,
        "tamano_kb": len(content) // 1024,
    }


# ── RF-4.5  Consultar Documentos ──────────────────────────────────────────────

@router.get("/{transportista_id}/documentos")
def consultar_documentos(
    transportista_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    t = db.query(Transportista).filter(Transportista.id == transportista_id).first()
    if not t:
        raise HTTPException(404, "Transportista no encontrado")
    return {
        "transportista": _build_out(t),
        "documentos": [
            {
                "id": d.id,
                "tipo": _extraer_estado(d.tipo),
                "nombre_archivo": d.nombre_archivo,
                "estado": _extraer_estado(d.estado),
                "fecha_vencimiento": d.fecha_vencimiento,
                "observacion": d.observacion,
                "subido_en": d.subido_en,
                "revisado_en": d.revisado_en,
                "tiene_archivo": d.contenido_pdf is not None,
            }
            for d in t.documentos
        ],
    }


# ── Revisar Documento (Secretaria) ────────────────────────────────────────────

@router.put("/{transportista_id}/documentos/{doc_id}/revisar")
def revisar_documento(
    transportista_id: int,
    doc_id: int,
    body: RevisionDocumentoRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("SECRETARIA")),
    request: Request = None,
):
    doc = (
        db.query(Documento)
        .filter(Documento.id == doc_id, Documento.transportista_id == transportista_id)
        .first()
    )
    if not doc:
        raise HTTPException(404, "Documento no encontrado")

    if body.estado not in ["APROBADO", "RECHAZADO"]:
        raise HTTPException(400, "Estado debe ser APROBADO o RECHAZADO")

    if body.estado == "RECHAZADO" and not body.observacion:
        raise HTTPException(400, "Debe proporcionar una observación cuando rechaza un documento")

    doc.estado          = body.estado
    doc.observacion     = body.observacion
    doc.revisado_por_id = current_user.id
    doc.revisado_en     = datetime.utcnow()
    if body.fecha_vencimiento:
        doc.fecha_vencimiento = body.fecha_vencimiento

    db.commit()

    registrar_auditoria(
        db, "REVISAR_DOCUMENTO", usuario_id=current_user.id,
        descripcion=f"Documento id={doc_id} marcado como {body.estado}",
        ip_address=request.client.host if request else None,
    )
    return {"mensaje": f"Documento {body.estado.lower()} correctamente"}


# ── Descargar / Ver PDF desde BD ──────────────────────────────────────────────

@router.get("/{transportista_id}/documentos/{doc_id}/descargar")
def descargar_documento(
    transportista_id: int,
    doc_id: int,
    inline: bool = False,       # ?inline=true → abrir en el navegador; false → descargar
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Devuelve el PDF almacenado en la base de datos.

    - ?inline=false  (default) → dispara descarga del archivo
    - ?inline=true             → lo muestra dentro del navegador / visor
    """
    doc = (
        db.query(Documento)
        .filter(Documento.id == doc_id, Documento.transportista_id == transportista_id)
        .first()
    )
    if not doc:
        raise HTTPException(404, "Documento no encontrado")

    if not doc.contenido_pdf:
        raise HTTPException(
            404,
            "El archivo PDF no está disponible en la base de datos. "
            "Es posible que haya sido subido con la versión anterior del sistema."
        )

    disposition = "inline" if inline else "attachment"

    return Response(
        content=doc.contenido_pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="{doc.nombre_archivo}"',
            "Content-Length": str(len(doc.contenido_pdf)),
        },
    )