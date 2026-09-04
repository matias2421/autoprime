"""Esquemas de autenticación."""

from pydantic import EmailStr, Field, model_validator

from app.schemas.comunes import Contrasena, Esquema, MezclaContrasena

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


class SolicitudRecuperacion(Esquema):
    """Cuerpo de `POST /api/auth/recuperar`."""

    correo: EmailStr


class AvisoRecuperacion(Esquema):
    """Respuesta a la solicitud de recuperación.

    Deliberadamente no dice si el correo tiene cuenta: responder distinto en
    cada caso convertiría este endpoint en una forma cómoda de averiguar qué
    correos están registrados.
    """

    ok: bool = True
    mensaje: str
    expira_en_minutos: int
    # En un despliegue real el token viaja por correo y nunca vuelve aquí.
    # Este proyecto no tiene servidor de correo, así que en desarrollo se
    # devuelve para poder completar y demostrar el flujo entero.
    token: str | None = None


class RestablecerContrasena(MezclaContrasena):
    """Cuerpo de `POST /api/auth/restablecer`.

    La contraseña nueva pasa por las mismas reglas que en el registro: no
    porque el formulario ya las aplique, sino porque la API no puede fiarse
    de que la petición venga de ese formulario.
    """

    token: str = Field(min_length=20)
    password: Contrasena
    confirmar_password: str | None = None

    @model_validator(mode="after")
    def _contrasenas_coinciden(self) -> "RestablecerContrasena":
        if self.confirmar_password is not None:
            if self.password != self.confirmar_password:
                raise ValueError("Las contraseñas no coinciden.")
        return self
