"""Esquemas de servicio (lo que se puede agendar en el taller)."""

from pydantic import Field

from app.schemas.comunes import Esquema, EstadoCuenta


class ServicioBase(Esquema):
    nombre: str = Field(min_length=1, max_length=60)
    descripcion: str = Field(min_length=1, max_length=200)
    duracion_min: int = Field(default=60, ge=15, le=480)
    precio: int = Field(default=0, ge=0)
    estado: EstadoCuenta = "activo"


class ServicioCrear(ServicioBase):
    pass


class ServicioActualizar(Esquema):
    nombre: str | None = Field(default=None, min_length=1, max_length=60)
    descripcion: str | None = Field(default=None, min_length=1, max_length=200)
    duracion_min: int | None = Field(default=None, ge=15, le=480)
    precio: int | None = Field(default=None, ge=0)
    estado: EstadoCuenta | None = None


class ServicioSalida(ServicioBase):
    id: int
