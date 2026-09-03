"""Esquemas de usuario: lo que entra por la API y lo que sale de ella.

Entrada y salida no son el mismo objeto y por eso son clases distintas: al
registrarse llega una contraseña, y al leer un usuario nunca debe salir ni
ella ni su hash.
"""

from datetime import datetime

from pydantic import EmailStr, Field, model_validator

from app.schemas.comunes import (
    Contrasena,
    Esquema,
    EstadoCuenta,
    MezclaContrasena,
    NombreRol,
    SoloDigitos,
    SoloLetras,
    Telefono,
    TipoDocumento,
)


class UsuarioBase(Esquema):
    """Los campos que el formulario de registro pide desde el primer avance."""

    nombre: SoloLetras
    apellido: SoloLetras
    tipo_documento: TipoDocumento
    numero_documento: SoloDigitos = Field(min_length=6, max_length=15)
    direccion: str = Field(min_length=5, max_length=80)
    telefono: Telefono
    correo: EmailStr = Field(max_length=60)


class UsuarioRegistro(UsuarioBase, MezclaContrasena):
    """Alta pública: quien se registra siempre entra como cliente.

    El rol no se acepta desde fuera a propósito. Si viniera en el cuerpo,
    cualquiera podría darse de alta como administrador.
    """

    password: Contrasena
    confirmar_password: str | None = None

    @model_validator(mode="after")
    def _contrasenas_coinciden(self) -> "UsuarioRegistro":
        if self.confirmar_password is not None:
            if self.password != self.confirmar_password:
                raise ValueError("Las contraseñas no coinciden.")
        return self


class UsuarioCrear(UsuarioBase, MezclaContrasena):
    """Alta desde el panel de administración: aquí sí se elige el rol."""

    password: Contrasena
    rol: NombreRol = "cliente"
    estado: EstadoCuenta = "activo"


class UsuarioActualizar(Esquema):
    """Edición parcial: solo se toca lo que venga en el cuerpo."""

    nombre: SoloLetras | None = None
    apellido: SoloLetras | None = None
    tipo_documento: TipoDocumento | None = None
    numero_documento: SoloDigitos | None = Field(default=None, min_length=6, max_length=15)
    direccion: str | None = Field(default=None, min_length=5, max_length=80)
    telefono: Telefono | None = None
    correo: EmailStr | None = Field(default=None, max_length=60)
    rol: NombreRol | None = None
    estado: EstadoCuenta | None = None


class CambioEstado(Esquema):
    """Cuerpo de `PATCH /usuarios/{id}/estado`."""

    estado: EstadoCuenta


class UsuarioSalida(Esquema):
    """Lo que la API devuelve de un usuario. Sin contraseña ni hash."""

    id: int
    nombre: str
    apellido: str
    tipo_documento: str
    numero_documento: str
    direccion: str
    telefono: str
    correo: str
    estado: str
    creado_en: datetime
    rol: str

    @classmethod
    def desde_modelo(cls, usuario) -> "UsuarioSalida":
        """Aplana `usuario.rol.nombre` a una cadena simple.

        El frontend solo necesita el nombre del rol; devolver el objeto
        entero obligaría a cambiar todos los sitios que hoy leen `rol`.
        """
        return cls(
            id=usuario.id,
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            tipo_documento=usuario.tipo_documento,
            numero_documento=usuario.numero_documento,
            direccion=usuario.direccion,
            telefono=usuario.telefono,
            correo=usuario.correo,
            estado=usuario.estado,
            creado_en=usuario.creado_en,
            rol=usuario.rol.nombre,
        )
