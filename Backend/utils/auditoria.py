from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from models.models import Auditoria


def registrar_auditoria(
    db: Session,
    accion: str,
    usuario_id: Optional[int] = None,
    viaje_id: Optional[int] = None,
    descripcion: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    """
    Registra una acción en la pista de auditoría.
    Llamar después de cada operación importante.
    """
    entrada = Auditoria(
        usuario_id=usuario_id,
        viaje_id=viaje_id,
        accion=accion,
        descripcion=descripcion,
        ip_address=ip_address,
        fecha=datetime.utcnow(),
    )
    db.add(entrada)
    db.commit()