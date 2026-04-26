from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re


# ── Auth ───────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str          # puede ser correo o cédula
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    nombres: str
    id: int


class RecuperarPasswordRequest(BaseModel):
    correo: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    nueva_password: str

    @field_validator("nueva_password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


# ── Usuarios ───────────────────────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    cedula: str
    nombres: str
    correo: EmailStr
    password: str
    rol: str = "TRANSPORTISTA"
    direccion: Optional[str] = None
    telefono: Optional[str] = None

    @field_validator("cedula")
    @classmethod
    def validar_cedula(cls, v):
        if not re.match(r"^\d{10,13}$", v):
            raise ValueError("La cédula debe tener entre 10 y 13 dígitos")
        return v

    @field_validator("password")
    @classmethod
    def password_len(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


class UsuarioOut(BaseModel):
    id: int
    cedula: str
    nombres: str
    correo: str
    rol: str
    activo: bool
    direccion: Optional[str]
    telefono: Optional[str]
    creado_en: datetime

    class Config:
        from_attributes = True


class UsuarioUpdate(BaseModel):
    nombres: Optional[str] = None
    correo: Optional[EmailStr] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None