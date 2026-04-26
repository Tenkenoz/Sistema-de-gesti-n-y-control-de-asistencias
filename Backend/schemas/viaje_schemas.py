from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class ViajeCreate(BaseModel):
    tipo_mercancia: str
    peso_total_kg: float
    dimensiones: Optional[str] = None
    numero_contenedor: Optional[str] = None
    peso_contenedor_kg: Optional[float] = None
    origen: str
    destino: str
    punto_recepcion: Optional[str] = None
    destinatario_nombre: Optional[str] = None
    destinatario_tel: Optional[str] = None
    destinatario_correo: Optional[str] = None
    fecha_salida: Optional[datetime] = None
    fecha_llegada_est: Optional[datetime] = None
    observaciones: Optional[str] = None


class ViajeUpdate(BaseModel):
    ruta_json: Optional[str] = None
    fecha_salida: Optional[datetime] = None
    fecha_llegada_est: Optional[datetime] = None
    observaciones: Optional[str] = None


class ReprogramarViajeRequest(BaseModel):
    causa: str
    horas_retraso: float
    observaciones: Optional[str] = None


class CancelarViajeRequest(BaseModel):
    causa_cancelacion: str
    evidencia_url: Optional[str] = None


class PlanificarRutaRequest(BaseModel):
    origen: str
    destino: str
    tramos_intermedios: Optional[List[str]] = []
    ruta_json: Optional[str] = None    # GeoJSON calculado por el frontend


class ViajeOut(BaseModel):
    id: int
    codigo: str
    estado: str
    tipo_mercancia: str
    peso_total_kg: float
    dimensiones: Optional[str]
    numero_contenedor: Optional[str]
    origen: str
    destino: str
    punto_recepcion: Optional[str]
    destinatario_nombre: Optional[str]
    destinatario_tel: Optional[str]
    destinatario_correo: Optional[str]
    fecha_salida: Optional[datetime]
    fecha_llegada_est: Optional[datetime]
    fecha_llegada_real: Optional[datetime]
    horas_retraso: Optional[float]
    causa_retraso: Optional[str]
    causa_cancelacion: Optional[str]
    observaciones: Optional[str]
    transportista_id: Optional[int]
    transportista_nombres: Optional[str]
    ruta_json: Optional[str]
    creado_en: datetime

    class Config:
        from_attributes = True


class ModificarRutaRequest(BaseModel):
    nueva_ruta_json: str
    motivo: str