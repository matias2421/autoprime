"""Esquemas de autenticación."""

from pydantic import EmailStr, Field

from app.schemas.comunes import Esquema

from app.schemas.usuario import UsuarioSalida


class Credenciales(Esquema):
    """Cuerpo de `POST /api/auth/login`."""

    correo: EmailStr
    password: str = Field(min_length=1)


class Sesion(Esquema):
    """Respuesta del login: el token y quién lo pidió.

    Se devuelve también el usuario para que el frontend pinte el Navbar sin
    tener que decodificar el token ni hacer una segunda petición.
    """

    token: str
    tipo: str = "bearer"
    expira_en_horas: int
    usuario: UsuarioSalida
