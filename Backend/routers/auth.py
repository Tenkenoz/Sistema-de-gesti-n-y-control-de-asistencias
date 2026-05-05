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


def enviar_nueva_contrasena(destino: str, nueva_contrasena: str):
    """
    Envía la NUEVA CONTRASEÑA al correo del usuario.
    """
    try:
        msg = MIMEMultipart()
        msg["From"]    = CORREO_EMISOR
        msg["To"]      = destino
        msg["Subject"] = "TransControl - Nueva Contraseña"

        cuerpo = (
            f"Hola,\n\n"
            f"Tu contraseña ha sido restablecida exitosamente.\n\n"
            f"Tu nueva contraseña es:\n\n"
            f"🔑 {nueva_contrasena}\n\n"
            f"Ya puedes iniciar sesión con esta contraseña.\n\n"
            f"Si no solicitaste este cambio, comunícate con el administrador."
        )
        msg.attach(MIMEText(cuerpo, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(CORREO_EMISOR, CLAVE_CORREO)
            server.sendmail(CORREO_EMISOR, destino, msg.as_string())

        print(f"✅ Nueva contraseña enviada a {destino}")
        return True

    except Exception as e:
        print(f"[SMTP ERROR] {e}")
        raise


def generar_contrasena(longitud=10):
    """Genera una contraseña aleatoria sin caracteres confusos."""
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'
    return ''.join(secrets.choice(chars) for _ in range(longitud))


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
    """
    Genera una NUEVA CONTRASEÑA, la guarda en la BD y la envía por correo.
    """
    user = db.query(Usuario).filter(Usuario.correo == body.correo).first()

    # Siempre responder igual para no revelar si el correo existe
    if not user or not user.activo:
        return {"mensaje": "Si el correo existe, recibirás tu nueva contraseña."}

    # 1. Generar nueva contraseña
    nueva = generar_contrasena()

    # 2. Guardarla hasheada en la BD
    user.hashed_password = hash_password(nueva)
    user.token_reset = None
    user.token_reset_exp = None
    db.commit()

    # 3. Enviarla por correo
    try:
        enviar_nueva_contrasena(user.correo, nueva)
    except Exception:
        raise HTTPException(500, "Error al enviar el correo, intenta más tarde")

    return {"mensaje": "Si el correo existe, recibirás tu nueva contraseña."}


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