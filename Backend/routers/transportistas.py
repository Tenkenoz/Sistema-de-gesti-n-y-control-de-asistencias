"""
RF-4.1  Crear Transportista
RF-4.2  Editar Transportista
RF-4.3  Eliminar Transportista (Desactivar)
RF-4.3b Activar Transportista
RF-4.3c Eliminar Permanentemente
RF-4.4  Importar Documentación (Individual)
RF-4.5  Consultar y Revisar Documentos
"""
import os
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter, Depends, File, Form,
    HTTPException, Request, UploadFile, status,
)
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
    """Extrae el valor string de un Enum de SQLAlchemy"""
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


# ── RF-4.3  Desactivar Transportista (baja lógica) ────────────────────────────

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

    # Verificar sin viajes en ejecución
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

    # Verificar sin viajes en ejecución
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

    # Eliminar documentos asociados
    db.query(Documento).filter(Documento.transportista_id == transportista_id).delete()

    # Eliminar transportista
    db.delete(t)

    # Eliminar usuario
    db.delete(usuario)

    db.commit()

    registrar_auditoria(
        db, "ELIMINAR_PERMANENTE", usuario_id=current_user.id,
        descripcion=f"Transportista id={transportista_id} eliminado permanentemente",
        ip_address=request.client.host if request else None,
    )
    return {"mensaje": "Transportista eliminado permanentemente"}


# ── RF-4.4  Importar Documentación (Individual) ───────────────────────────────

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
    t = db.query(Transportista).filter(Transportista.id == transportista_id).first()
    if not t:
        raise HTTPException(404, "Transportista no encontrado")

    # Validar que solo el propio transportista o admin suban
    rol_usuario = _extraer_estado(current_user.rol)
    if rol_usuario == "TRANSPORTISTA" and t.usuario_id != current_user.id:
        raise HTTPException(403, "No tiene permiso para subir documentos de otro transportista")

    # Validar tipo
    tipos_validos = ["CEDULA", "LICENCIA_E", "MATRICULA", "REVISION_TECNICA", "SOAT", "PERMISO_PESOS"]
    if tipo not in tipos_validos:
        raise HTTPException(400, f"Tipo inválido. Válidos: {', '.join(tipos_validos)}")

    # Validar tamaño
    content = await archivo.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(400, f"El archivo excede el límite de {settings.MAX_FILE_SIZE_MB}MB")

    # Validar formato PDF
    if archivo.content_type != "application/pdf":
        raise HTTPException(400, "Solo se aceptan archivos en formato PDF")

    # Guardar archivo
    folder = os.path.join(settings.UPLOAD_DIR, str(transportista_id))
    os.makedirs(folder, exist_ok=True)
    filename = f"{tipo}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{archivo.filename}"
    filepath = os.path.join(folder, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    # Fecha de vencimiento
    venc = None
    if fecha_vencimiento:
        try:
            venc = datetime.fromisoformat(fecha_vencimiento)
        except ValueError:
            pass

    # Si ya existe un documento del mismo tipo, actualizarlo
    doc_existente = (
        db.query(Documento)
        .filter(
            Documento.transportista_id == transportista_id,
            Documento.tipo == tipo,
        )
        .first()
    )

    if doc_existente:
        doc_existente.nombre_archivo = filename
        doc_existente.ruta_archivo = filepath
        doc_existente.estado = EstadoDocEnum.PENDIENTE
        doc_existente.fecha_vencimiento = venc
        doc_existente.subido_en = datetime.utcnow()
        doc_existente.revisado_en = None
        doc_existente.observacion = None
        doc_existente.revisado_por_id = None
        doc = doc_existente
    else:
        doc = Documento(
            transportista_id=transportista_id,
            tipo=tipo,
            ruta_archivo=filepath,
            nombre_archivo=filename,
            estado=EstadoDocEnum.PENDIENTE,
            fecha_vencimiento=venc,
        )
        db.add(doc)

    db.commit()
    db.refresh(doc)

    registrar_auditoria(
        db, "SUBIR_DOCUMENTO", usuario_id=current_user.id,
        descripcion=f"Documento {tipo} subido para transportista id={transportista_id}",
        ip_address=request.client.host if request else None,
    )
    return {"mensaje": "Documento subido correctamente", "documento_id": doc.id}


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

    doc.estado = body.estado
    doc.observacion = body.observacion
    doc.revisado_por_id = current_user.id
    doc.revisado_en = datetime.utcnow()
    if body.fecha_vencimiento:
        doc.fecha_vencimiento = body.fecha_vencimiento

    db.commit()

    registrar_auditoria(
        db, "REVISAR_DOCUMENTO", usuario_id=current_user.id,
        descripcion=f"Documento id={doc_id} marcado como {body.estado}",
        ip_address=request.client.host if request else None,
    )
    return {"mensaje": f"Documento {body.estado.lower()} correctamente"}