from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class TransportistaCreate(BaseModel):
    placa_vehiculo: Optional[str] = None
    tipo_vehiculo: Optional[str] = None
    capacidad_ton: Optional[float] = None


class TransportistaUpdate(BaseModel):
    placa_vehiculo: Optional[str] = None
    tipo_vehiculo: Optional[str] = None
    capacidad_ton: Optional[float] = None


class DocumentoOut(BaseModel):
    id: int
    tipo: str
    nombre_archivo: str
    estado: str
    fecha_vencimiento: Optional[datetime]
    observacion: Optional[str]
    subido_en: datetime
    revisado_en: Optional[datetime]

    class Config:
        from_attributes = True


class TransportistaOut(BaseModel):
    id: int
    usuario_id: int
    cedula: str
    nombres: str
    correo: str
    telefono: Optional[str]
    direccion: Optional[str]
    placa_vehiculo: Optional[str]
    tipo_vehiculo: Optional[str]
    capacidad_ton: Optional[float]
    activo: bool
    documentos: List[DocumentoOut] = []
    estado_documentacion: str   # PENDIENTE | APROBADO | RECHAZADO | SIN_DOCS

    class Config:
        from_attributes = True


class RevisionDocumentoRequest(BaseModel):
    estado: str             # APROBADO | RECHAZADO
    observacion: Optional[str] = None
    fecha_vencimiento: Optional[datetime] = None


class EliminarTransportistaRequest(BaseModel):
    razon: str              # DESPIDO | RENUNCIA | JUBILACION
    observaciones: Optional[str] = None