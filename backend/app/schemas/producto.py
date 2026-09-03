"""Esquemas de producto (los vehículos del catálogo)."""

from datetime import datetime

from pydantic import Field

from app.schemas.comunes import Esquema, EstadoProducto, Familia


class Especificaciones(Esquema):
    """Ficha técnica, anidada en la respuesta.

    En la base son seis columnas sueltas; el frontend las consume agrupadas
    desde el segundo avance, así que la API las arma aquí.
    """

    motor: str
    potencia: str
    aceleracion: str
    velocidad: str
    transmision: str
    traccion: str


class ProductoBase(Esquema):
    slug: str = Field(min_length=3, max_length=60, pattern=r"^[a-z0-9-]+$")
    marca: str = Field(min_length=1, max_length=40)
    modelo: str = Field(min_length=1, max_length=60)
    familia: Familia = "gama"
    base: str = Field(min_length=1, max_length=60)
    lema: str = Field(min_length=1, max_length=120)
    descripcion: str = Field(min_length=1, max_length=1000)
    imagen: str = Field(min_length=1, max_length=120)
    anio: int = Field(ge=1950, le=2100)
    kilometraje: int = Field(default=0, ge=0)

    # Nulo significa "precio bajo consulta": es el caso de las piezas únicas.
    precio: int | None = Field(default=None, ge=0)
    unidades: int | None = Field(default=None, ge=1)

    motor: str = Field(min_length=1, max_length=60)
    potencia: str = Field(min_length=1, max_length=20)
    aceleracion: str = Field(min_length=1, max_length=20)
    velocidad: str = Field(min_length=1, max_length=20)
    transmision: str = Field(min_length=1, max_length=40)
    traccion: str = Field(min_length=1, max_length=20)
    estado: EstadoProducto = "disponible"


class ProductoCrear(ProductoBase):
    pass


class ProductoActualizar(Esquema):
    """Edición parcial."""

    slug: str | None = Field(default=None, min_length=3, max_length=60, pattern=r"^[a-z0-9-]+$")
    marca: str | None = Field(default=None, min_length=1, max_length=40)
    modelo: str | None = Field(default=None, min_length=1, max_length=60)
    familia: Familia | None = None
    base: str | None = Field(default=None, min_length=1, max_length=60)
    lema: str | None = Field(default=None, min_length=1, max_length=120)
    descripcion: str | None = Field(default=None, min_length=1, max_length=1000)
    imagen: str | None = Field(default=None, min_length=1, max_length=120)
    anio: int | None = Field(default=None, ge=1950, le=2100)
    kilometraje: int | None = Field(default=None, ge=0)
    precio: int | None = Field(default=None, ge=0)
    unidades: int | None = Field(default=None, ge=1)
    motor: str | None = Field(default=None, min_length=1, max_length=60)
    potencia: str | None = Field(default=None, min_length=1, max_length=20)
    aceleracion: str | None = Field(default=None, min_length=1, max_length=20)
    velocidad: str | None = Field(default=None, min_length=1, max_length=20)
    transmision: str | None = Field(default=None, min_length=1, max_length=40)
    traccion: str | None = Field(default=None, min_length=1, max_length=20)
    estado: EstadoProducto | None = None


class ProductoSalida(Esquema):
    id: int
    slug: str
    marca: str
    modelo: str
    titulo: str
    familia: str
    base: str
    lema: str
    descripcion: str
    imagen: str
    anio: int
    kilometraje: int
    precio: int | None
    unidades: int | None
    estado: str
    creado_en: datetime
    specs: Especificaciones

    @classmethod
    def desde_modelo(cls, p) -> "ProductoSalida":
        """Agrupa la ficha técnica y compone el título."""
        return cls(
            id=p.id,
            slug=p.slug,
            marca=p.marca,
            modelo=p.modelo,
            titulo=f"{p.marca} {p.modelo}",
            familia=p.familia,
            base=p.base,
            lema=p.lema,
            descripcion=p.descripcion,
            imagen=p.imagen,
            anio=p.anio,
            kilometraje=p.kilometraje,
            precio=p.precio,
            unidades=p.unidades,
            estado=p.estado,
            creado_en=p.creado_en,
            specs=Especificaciones(
                motor=p.motor,
                potencia=p.potencia,
                aceleracion=p.aceleracion,
                velocidad=p.velocidad,
                transmision=p.transmision,
                traccion=p.traccion,
            ),
        )
