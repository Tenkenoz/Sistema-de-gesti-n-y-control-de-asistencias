"""
RF-1  Iniciar Sesión
RF-2  Crear Cuenta
RF-3  Recuperar Contraseña
"""
import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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


# ── Configuración SMTP ────────────────────────────────────────────────────────

CORREO_EMISOR = os.getenv("SMTP_USER", "obanderick@gmail.com")
CLAVE_CORREO  = os.getenv("SMTP_PASS", "wkcbeiirqchurtft")

def enviar_correo_smtp(destino: str, token: str):
    try:
        enlace = f"https://tuapp.com/reset-password?token={token}"

        msg = MIMEMultipart()
        msg["From"]    = CORREO_EMISOR
        msg["To"]      = destino
        msg["Subject"] = "Recuperación de Contraseña"

        cuerpo = (
            f"Hemos recibido una solicitud para restablecer tu contraseña.\n\n"
            f"Haz clic en el siguiente enlace para continuar:\n{enlace}\n\n"
            f"Este enlace expira en 2 horas.\n"
            f"Si no solicitaste esto, ignora este mensaje."
        )
        msg.attach(MIMEText(cuerpo, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(CORREO_EMISOR, CLAVE_CORREO)
            server.sendmail(CORREO_EMISOR, destino, msg.as_string())

    except Exception as e:
        print(f"[SMTP ERROR] {e}")
        raise


# ── RF-1: Iniciar Sesión ───────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
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
    db.flush()

    if body.rol == "TRANSPORTISTA":
        db.add(Transportista(usuario_id=nuevo.id))

    db.commit()
    db.refresh(nuevo)
    return nuevo


# ── RF-3: Recuperar Contraseña ────────────────────────────────────────────────

@router.post("/recuperar-password")
def solicitar_recuperacion(body: RecuperarPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.correo == body.correo).first()

    # Siempre responder igual para no revelar si el correo existe
    if not user or not user.activo:
        return {"mensaje": "Si el correo existe recibirás un enlace de recuperación"}

    token = secrets.token_urlsafe(48)
    user.token_reset     = token
    user.token_reset_exp = datetime.utcnow() + timedelta(hours=2)
    db.commit()

    try:
        enviar_correo_smtp(user.correo, token)
    except Exception:
        raise HTTPException(500, "Error al enviar el correo, intenta más tarde")

    return {"mensaje": "Si el correo existe recibirás un enlace de recuperación"}


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
    user.token_reset      = None
    user.token_reset_exp  = None
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