from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Valores por defecto (se sobreescriben con lo que haya en el .env)
    # IMPORTANTE: No hardcodear localhost aquí si planeas usar Docker
    DATABASE_URL: str = "postgresql://transuser:tu_password@db:5432/transcontrol"
    
    SECRET_KEY: str = "CAMBIA_ESTA_CLAVE_EN_PRODUCCION_debe_tener_64_chars_minimo"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    APP_NAME: str = "TransControl"
    DEBUG: bool = True
    
    # Rutas relativas para que funcionen en Linux (Docker)
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 2

    class Config:
        # Esto le dice a Pydantic que busque el archivo .env
        env_file = ".env"
        extra = "ignore" # Ignora variables extra en el .env si las hay

settings = Settings()