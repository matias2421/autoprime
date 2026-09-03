"""Hash de contraseñas y emisión/validación de tokens JWT."""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.configuracion import configuracion


def hashear_contrasena(contrasena: str) -> str:
    """Devuelve el hash bcrypt de una contraseña en claro."""
    semilla = bcrypt.gensalt(rounds=configuracion.rondas_bcrypt)
    return bcrypt.hashpw(contrasena.encode("utf-8"), semilla).decode("utf-8")


def verificar_contrasena(contrasena: str, hash_almacenado: str) -> bool:
    """Compara una contraseña con su hash.

    Sirve también para los usuarios creados por el backend anterior en Node:
    bcrypt es el mismo algoritmo y el mismo formato (`$2b$10$…`), de modo que
    nadie tiene que volver a registrarse tras el cambio a FastAPI.
    """
    try:
        return bcrypt.checkpw(
            contrasena.encode("utf-8"), hash_almacenado.encode("utf-8")
        )
    except ValueError:
        # Hash con formato inválido en la base: se trata como no coincidente
        # en lugar de reventar la petición.
        return False


def crear_token(usuario_id: int, correo: str, rol: str) -> str:
    """Emite un JWT firmado con el identificador, el correo y el rol."""
    ahora = datetime.now(timezone.utc)
    carga = {
        # La especificación de JWT exige que "sub" sea una cadena.
        "sub": str(usuario_id),
        "correo": correo,
        "rol": rol,
        "iat": ahora,
        "exp": ahora + timedelta(hours=configuracion.horas_expiracion_token),
    }
    return jwt.encode(
        carga, configuracion.secret_key, algorithm=configuracion.algoritmo_jwt
    )


def decodificar_token(token: str) -> dict:
    """Verifica firma y expiración. Propaga `JWTError` si algo falla."""
    return jwt.decode(
        token, configuracion.secret_key, algorithms=[configuracion.algoritmo_jwt]
    )


__all__ = [
    "JWTError",
    "crear_token",
    "decodificar_token",
    "hashear_contrasena",
    "verificar_contrasena",
]
