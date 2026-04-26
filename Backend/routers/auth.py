"""
RF-1  Iniciar Sesión
RF-2  Crear Cuenta
RF-3  Recuperar Contraseña
"""
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from core.security import (
    create_access_token, get_current_user,
    hash_password, verify_password,
)
from database import get_db
from models.models import Transportista, Usuario
from schemas.auth_schemas import (
    LoginRequest, RecuperarPasswordRequest,
    ResetPasswordRequest, TokenResponse,
    UsuarioCreate, UsuarioOut, UsuarioUpdate,
)
from utils.auditoria import registrar_auditoria

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


# ── RF-1: Iniciar Sesión ───────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    # buscar por correo O por cédula
    user = (
        db.query(Usuario)
        .filter(
            (Usuario.correo == body.username) | (Usuario.cedula == body.username)
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cuenta no encontrada, verifique el nombre de usuario o correo electrónico",
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta inactiva. Comuníquese con el personal administrativo.",
        )

    if not verify_password(body.password, user.hashed_password):
        registrar_auditoria(
            db, "LOGIN_FALLIDO", usuario_id=user.id,
            descripcion="Contraseña incorrecta",
            ip_address=request.client.host,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta",
        )

    token = create_access_token({"sub": str(user.id), "rol": user.rol})

    registrar_auditoria(
        db, "LOGIN", usuario_id=user.id,
        descripcion="Inicio de sesión exitoso",
        ip_address=request.client.host,
    )

    return TokenResponse(
        access_token=token,
        rol=user.rol,
        nombres=user.nombres,
        id=user.id,
    )


# ── RF-2: Crear Cuenta ────────────────────────────────────────────────────────

@router.post("/registro", response_model=UsuarioOut, status_code=201)
def registrar(body: UsuarioCreate, db: Session = Depends(get_db)):
    # verificar duplicados
    if db.query(Usuario).filter(Usuario.correo == body.correo).first():
        raise HTTPException(400, "El correo ya se encuentra registrado")
    if db.query(Usuario).filter(Usuario.cedula == body.cedula).first():
        raise HTTPException(400, "La cédula ya se encuentra registrada")

    nuevo = Usuario(
        cedula=body.cedula,
        nombres=body.nombres,
        correo=body.correo,
        hashed_password=hash_password(body.password),
        rol=body.rol,
        direccion=body.direccion,
        telefono=body.telefono,
    )
    db.add(nuevo)
    db.flush()   # obtener ID sin commit

    # si es transportista, crear su perfil automáticamente
    if body.rol == "TRANSPORTISTA":
        db.add(Transportista(usuario_id=nuevo.id))

    db.commit()
    db.refresh(nuevo)
    return nuevo


# ── RF-3: Recuperar Contraseña ────────────────────────────────────────────────

@router.post("/recuperar-password")
def solicitar_recuperacion(body: RecuperarPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.correo == body.correo).first()

    # siempre responder igual para no revelar si el correo existe
    if not user or not user.activo:
        return {"mensaje": "Si el correo existe recibirás un enlace de recuperación"}

    token = secrets.token_urlsafe(48)
    user.token_reset = token
    user.token_reset_exp = datetime.utcnow() + timedelta(hours=2)
    db.commit()

    # En producción: enviar correo con el token
    # Por ahora lo devolvemos en la respuesta (útil para pruebas)
    return {
        "mensaje": "Si el correo existe recibirás un enlace de recuperación",
        "debug_token": token,   # ← quitar en producción
    }


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = (
        db.query(Usuario)
        .filter(
            Usuario.token_reset == body.token,
            Usuario.token_reset_exp > datetime.utcnow(),
        )
        .first()
    )
    if not user:
        raise HTTPException(400, "Token inválido o expirado")

    user.hashed_password = hash_password(body.nueva_password)
    user.token_reset = None
    user.token_reset_exp = None
    db.commit()

    return {"mensaje": "Contraseña actualizada correctamente"}


# ── Perfil del usuario actual ─────────────────────────────────────────────────

@router.get("/me", response_model=UsuarioOut)
def mi_perfil(current_user=Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UsuarioOut)
def actualizar_perfil(
    body: UsuarioUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user