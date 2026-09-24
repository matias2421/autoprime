"""Esquemas de venta.

La decisión que gobierna este archivo: el precio NO se acepta de un cliente.
Llega del catálogo en el momento de vender. Si el importe viniera en el cuerpo
de la petición, cualquiera con Postman podría comprarse un Phantom por mil
pesos, y el formulario del navegador no sería ninguna defensa.

El personal sí puede fijarlo, porque hay piezas sin precio de lista y ventas
negociadas; pero eso es una operación de mostrador, hecha por alguien con rol,
no algo que decida quien compra.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import Field, model_validator

from app.schemas.comunes import con_ejemplo, Dinero, Esquema


class LineaCrear(Esquema):
    """Una línea del carrito: un vehículo o un servicio, nunca los dos."""

    producto_id: int | None = Field(default=None, ge=1)
    servicio_id: int | None = Field(default=None, ge=1)
    cantidad: int = Field(default=1, ge=1, le=99)
    descuento: Decimal = Field(default=Decimal(0), ge=0)

    # Solo lo honra el personal; en una petición de cliente se ignora.
    precio_unitario: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _uno_u_otro(self) -> "LineaCrear":
        if (self.producto_id is None) == (self.servicio_id is None):
            raise ValueError(
                "Cada línea lleva un vehículo o un servicio, no ambos ni ninguno."
            )
        return self


class VentaCrear(Esquema):
    """Cuerpo de `POST /api/ventas`.

    `usuario_id` solo lo puede usar el personal, para registrar la venta a
    nombre de un cliente. Sin él, el comprador es quien trae el token.
    """

    model_config = con_ejemplo(
        usuarioId=12,
        lineas=[{"productoId": 3, "cantidad": 1},
                {"servicioId": 2, "cantidad": 1}],
        notas="Entrega en el concesionario.",
    )

    lineas: list[LineaCrear] = Field(min_length=1, max_length=20)
    usuario_id: int | None = Field(default=None, ge=1)
    descuento: Decimal = Field(default=Decimal(0), ge=0)
    notas: str | None = Field(default=None, max_length=300)


class CambioEstadoVenta(Esquema):
    """Cuerpo de `PATCH /api/ventas/{id}/estado`."""

    estado: str = Field(pattern="^(pendiente|pagada|anulada)$")


class LineaSalida(Esquema):
    id: int
    producto_id: int | None
    servicio_id: int | None
    descripcion: str
    cantidad: int
    precio_unitario: Dinero
    descuento: Dinero
    subtotal: Dinero


class VentaSalida(Esquema):
    id: int
    numero: str
    usuario_id: int
    vendedor_id: int | None
    fecha: datetime
    subtotal: Dinero
    descuento: Dinero
    impuestos: Dinero
    total: Dinero
    estado: str
    notas: str | None

    # Nombres ya resueltos, para que la tabla del panel no cruce tablas.
    cliente: str | None = None
    vendedor: str | None = None
    lineas: list[LineaSalida] = []
    factura_numero: str | None = None

    @classmethod
    def desde_modelo(cls, v) -> "VentaSalida":
        return cls(
            id=v.id,
            numero=v.numero,
            usuario_id=v.usuario_id,
            vendedor_id=v.vendedor_id,
            fecha=v.fecha,
            subtotal=v.subtotal,
            descuento=v.descuento,
            impuestos=v.impuestos,
            total=v.total,
            estado=v.estado,
            notas=v.notas,
            cliente=(
                f"{v.cliente.nombre} {v.cliente.apellido}" if v.cliente else None
            ),
            vendedor=(
                f"{v.vendedor.nombre} {v.vendedor.apellido}" if v.vendedor else None
            ),
            lineas=[LineaSalida.model_validate(l) for l in v.lineas],
            factura_numero=v.factura.numero if v.factura else None,
        )


class ResumenVentas(Esquema):
    """Cifras de cabecera del panel. Las calcula la base, no Python."""

    total: int
    pendientes: int
    pagadas: int
    anuladas: int
    ingresos: Dinero
    ticket_promedio: Dinero
