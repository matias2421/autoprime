"""Hash de contraseñas y emisión/validación de tokens JWT."""

import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.configuracion import configuracion

# Los dos tokens que emite la API llevan marcado su tipo. Ambos identifican al
# mismo usuario, así que sin esta marca el de recuperación serviría como
# cabecera `Authorization` y bastaría con decir "olvidé mi contraseña" para
# entrar en la cuenta sin llegar a cambiarla.
TIPO_SESION = "sesion"
TIPO_RECUPERACION = "recuperacion"


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
    """Emite el JWT de sesión, firmado con el identificador, el correo y el rol."""
    ahora = datetime.now(timezone.utc)
    carga = {
        # La especificación de JWT exige que "sub" sea una cadena.
        "sub": str(usuario_id),
        "tipo": TIPO_SESION,
        "correo": correo,
        "rol": rol,
        "iat": ahora,
        "exp": ahora + timedelta(hours=configuracion.horas_expiracion_token),
    }
    return jwt.encode(
        carga, configuracion.secret_key, algorithm=configuracion.algoritmo_jwt
    )


def huella_contrasena(password_hash: str) -> str:
    """Resumen corto del hash actual de la contraseña.

    No se guarda en ninguna parte: se recalcula al validar. Su única función
    es que el token de recuperación deje de servir en cuanto la contraseña
    cambie.
    """
    return hashlib.sha256(password_hash.encode("utf-8")).hexdigest()[:16]


def crear_token_recuperacion(usuario_id: int, password_hash: str) -> str:
    """Emite el token de un solo uso para restablecer la contraseña.

    Va firmado igual que el de sesión, pero vive minutos en lugar de horas y
    lleva la huella de la contraseña vigente. Al restablecerla, el hash cambia
    y la huella deja de coincidir: el enlace queda inservible aunque todavía
    no haya expirado, y de paso caducan los que se hubieran pedido antes. Así
    se consigue el uso único sin necesidad de una tabla de tokens gastados.
    """
    ahora = datetime.now(timezone.utc)
    carga = {
        "sub": str(usuario_id),
        "tipo": TIPO_RECUPERACION,
        "huella": huella_contrasena(password_hash),
        "iat": ahora,
        "exp": ahora
        + timedelta(minutes=configuracion.minutos_expiracion_recuperacion),
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
    "TIPO_RECUPERACION",
    "TIPO_SESION",
    "crear_token",
    "crear_token_recuperacion",
    "decodificar_token",
    "hashear_contrasena",
    "huella_contrasena",
    "verificar_contrasena",
]
