"""Piezas compartidas por varios esquemas: tipos, validadores y errores.

Las reglas son las mismas que ya aplicaba el frontend y el backend anterior;
aquí se expresan una sola vez y Pydantic las hace cumplir en cada entrada.
"""

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator
from pydantic.alias_generators import to_camel

class Esquema(BaseModel):
    """Base de todos los esquemas de la API.

    El código Python usa `snake_case` porque es lo idiomático, pero la API
    habla `camelCase` porque es lo que el frontend en React ya envía y lee
    desde el primer avance. El generador de alias traduce entre ambos, así
    que ningún componente tuvo que cambiar al pasar de Express a FastAPI.

    `populate_by_name` deja aceptar además el nombre original, de modo que
    una petición desde Postman escrita en `snake_case` también funciona.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


# --- Vocabularios del dominio (coinciden con los ENUM de MySQL) ---
TipoDocumento = Literal["CC", "TI", "CE", "PA", "NIT"]
EstadoCuenta = Literal["activo", "inactivo"]
EstadoProducto = Literal["disponible", "vendido", "inactivo"]
Familia = Literal["gama", "edicion", "coleccion"]
EstadoCita = Literal["pendiente", "confirmada", "cancelada", "completada"]
NombreRol = Literal["administrador", "empleado", "cliente"]

# --- Cadenas con forma ---
Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

SoloDigitos = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^\d+$")
]

Telefono = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^\d{7,10}$")
]

# Letras (con tildes y ñ), espacios, apóstrofos y guiones: nada más.
SoloLetras = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=2,
        max_length=40,
        pattern=r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü' -]+$",
    ),
]

_MAYUSCULA = re.compile(r"[A-ZÁÉÍÓÚÑ]")
_MINUSCULA = re.compile(r"[a-záéíóúñ]")
_DIGITO = re.compile(r"\d")
_ESPECIAL = re.compile(r"[^A-Za-z0-9]")


def validar_contrasena(valor: str) -> str:
    """Exige la misma fortaleza que pedía el formulario de registro.

    Se comprueba aquí y no solo en el frontend porque una petición puede
    llegar desde Postman o desde cualquier cliente, saltándose el formulario.
    """
    if len(valor) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    if len(valor) > 72:
        # Límite propio de bcrypt: ignora en silencio lo que pase de 72 bytes,
        # así que se rechaza en lugar de aceptar una contraseña recortada.
        raise ValueError("La contraseña no puede superar los 72 caracteres.")
    if not _MAYUSCULA.search(valor):
        raise ValueError("La contraseña debe incluir una mayúscula.")
    if not _MINUSCULA.search(valor):
        raise ValueError("La contraseña debe incluir una minúscula.")
    if not _DIGITO.search(valor):
        raise ValueError("La contraseña debe incluir un número.")
    if not _ESPECIAL.search(valor):
        raise ValueError("La contraseña debe incluir un carácter especial.")
    return valor


Contrasena = Annotated[str, Field(min_length=8, max_length=72)]


class MezclaContrasena(Esquema):
    """Aplica `validar_contrasena` al campo `password` de quien la herede."""

    @field_validator("password", check_fields=False)
    @classmethod
    def _comprobar_contrasena(cls, valor: str) -> str:
        return validar_contrasena(valor)


# --- Formato único de error de toda la API ---
class DetalleError(Esquema):
    campo: str
    problema: str


class RespuestaError(Esquema):
    """Todo error de la API sale con esta forma, venga de donde venga.

    `codigo` es estable y sirve para decidir en el frontend; `mensaje` está
    redactado para mostrarse al usuario y puede cambiar.
    """

    codigo: str
    mensaje: str
    ruta: str
    detalles: list[DetalleError] | None = None


class RespuestaSimple(Esquema):
    """Confirmación breve para operaciones que no devuelven un recurso."""

    ok: bool = True
    mensaje: str
