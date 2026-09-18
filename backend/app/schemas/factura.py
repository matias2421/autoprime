"""Esquemas de factura.

No hay `FacturaCrear`: una factura no se redacta, se emite a partir de una
venta. Todo lo que la compone ya está decidido cuando se emite, así que el
endpoint recibe el id de la venta y nada más. Aceptar importes en el cuerpo
sería aceptar que la factura diga algo distinto de lo que se vendió.
"""

from datetime import datetime

from app.schemas.comunes import Dinero, Esquema


class LineaFacturaSalida(Esquema):
    id: int
    descripcion: str
    cantidad: int
    precio_unitario: Dinero
    subtotal: Dinero


class FacturaSalida(Esquema):
    id: int
    numero: str
    venta_id: int
    venta_numero: str | None = None
    fecha_emision: datetime
    subtotal: Dinero
    impuestos: Dinero
    total: Dinero
    estado: str

    cliente: str | None = None
    cliente_documento: str | None = None
    cliente_correo: str | None = None
    lineas: list[LineaFacturaSalida] = []

    @classmethod
    def desde_modelo(cls, f) -> "FacturaSalida":
        comprador = f.venta.cliente if f.venta else None
        return cls(
            id=f.id,
            numero=f.numero,
            venta_id=f.venta_id,
            venta_numero=f.venta.numero if f.venta else None,
            fecha_emision=f.fecha_emision,
            subtotal=f.subtotal,
            impuestos=f.impuestos,
            total=f.total,
            estado=f.estado,
            cliente=(
                f"{comprador.nombre} {comprador.apellido}" if comprador else None
            ),
            cliente_documento=(
                f"{comprador.tipo_documento} {comprador.numero_documento}"
                if comprador
                else None
            ),
            cliente_correo=comprador.correo if comprador else None,
            lineas=[LineaFacturaSalida.model_validate(l) for l in f.lineas],
        )
