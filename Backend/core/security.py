from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.config import settings
from database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Contraseñas ────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Tokens JWT ─────────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Usuario actual ─────────────────────────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    # CORRECCIÓN 1: Ruta de importación exacta
    from models.models import Usuario 

    payload = decode_token(token)
    user_id_str: str = payload.get("sub")
    
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Token inválido: falta identificador")

    try:
        # CORRECCIÓN 2: Asegurar conversión a entero para la búsqueda en Postgres
        user_id = int(user_id_str)
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
    except ValueError:
        raise HTTPException(status_code=401, detail="Token inválido: formato de ID incorrecto")

    if user is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    if not user.activo:
        raise HTTPException(status_code=403, detail="Cuenta inactiva")

    return user

def require_roles(*roles: str):
    """Decorador de dependencia que exige que el usuario tenga uno de los roles dados."""
    def _dependency(current_user=Depends(get_current_user)):
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Roles permitidos: {', '.join(roles)}",
            )
        return current_user
    return _dependency