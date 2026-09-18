"""Modelos SQLAlchemy: el mapeo de las tablas que ya existen en MySQL.

El esquema vive en `sql/autoprime.sql`; aquí solo se describe para que
SQLAlchemy sepa leerlo y escribirlo. Por eso las tablas NO se crean desde el
código — se cargan con el script SQL, que es la fuente de verdad del esquema.
"""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_datos import Base

TIPOS_DOCUMENTO = ("CC", "TI", "CE", "PA", "NIT")
ESTADOS_CUENTA = ("activo", "inactivo")
ESTADOS_PRODUCTO = ("disponible", "vendido", "inactivo")
FAMILIAS = ("gama", "edicion", "coleccion")
ESTADOS_CITA = ("pendiente", "confirmada", "cancelada", "completada")
ESTADOS_VENTA = ("pendiente", "pagada", "anulada")
ESTADOS_FACTURA = ("emitida", "anulada")
TIPOS_PQR = ("peticion", "queja", "reclamo", "sugerencia")
ESTADOS_PQR = ("pendiente", "en_proceso", "respondida", "cerrada")
ROLES_MENSAJE = ("usuario", "asistente")


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True)
    descripcion: Mapped[str] = mapped_column(String(150))

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")


class Permiso(Base):
    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), unique=True)
    descripcion: Mapped[str] = mapped_column(String(150))


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("tipo_documento", "numero_documento", name="uq_documento"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40))
    apellido: Mapped[str] = mapped_column(String(40))
    tipo_documento: Mapped[str] = mapped_column(Enum(*TIPOS_DOCUMENTO))
    numero_documento: Mapped[str] = mapped_column(String(15))
    direccion: Mapped[str] = mapped_column(String(80))
    telefono: Mapped[str] = mapped_column(String(10))
    correo: Mapped[str] = mapped_column(String(60), unique=True)

    # El nombre de la columna deja claro que aquí nunca va texto plano.
    password_hash: Mapped[str] = mapped_column(String(255))

    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    estado: Mapped[str] = mapped_column(Enum(*ESTADOS_CUENTA), default="activo")
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    rol: Mapped["Rol"] = relationship(back_populates="usuarios", lazy="joined")
    citas: Mapped[list["Cita"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )


class Producto(Base):
    """Un vehículo del catálogo."""

    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    marca: Mapped[str] = mapped_column(String(40))
    modelo: Mapped[str] = mapped_column(String(60))
    familia: Mapped[str] = mapped_column(Enum(*FAMILIAS), default="gama")
    base: Mapped[str] = mapped_column(String(60))
    lema: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(String(1000))
    imagen: Mapped[str] = mapped_column(String(120))
    anio: Mapped[int] = mapped_column(SmallInteger)
    kilometraje: Mapped[int] = mapped_column(Integer, default=0)

    # Nulo significa "precio bajo consulta": es el caso de las piezas únicas.
    precio: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    unidades: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    motor: Mapped[str] = mapped_column(String(60))
    potencia: Mapped[str] = mapped_column(String(20))
    aceleracion: Mapped[str] = mapped_column(String(20))
    velocidad: Mapped[str] = mapped_column(String(20))
    transmision: Mapped[str] = mapped_column(String(40))
    traccion: Mapped[str] = mapped_column(String(20))
    estado: Mapped[str] = mapped_column(Enum(*ESTADOS_PRODUCTO), default="disponible")
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Servicio(Base):
    __tablename__ = "servicios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60))
    descripcion: Mapped[str] = mapped_column(String(200))
    duracion_min: Mapped[int] = mapped_column(SmallInteger, default=60)
    precio: Mapped[int] = mapped_column(BigInteger, default=0)
    estado: Mapped[str] = mapped_column(Enum(*ESTADOS_CUENTA), default="activo")


class Cita(Base):
    """Agendamiento: el cliente elige vehículo, servicio, fecha y hora."""

    __tablename__ = "citas"
    __table_args__ = (
        # Impide que dos clientes tomen la misma franja para el mismo vehículo.
        UniqueConstraint("fecha", "hora", "producto_id", name="uq_cupo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    producto_id: Mapped[int | None] = mapped_column(
        ForeignKey("productos.id"), nullable=True
    )
    servicio_id: Mapped[int] = mapped_column(ForeignKey("servicios.id"))
    fecha: Mapped[date] = mapped_column(Date)
    hora: Mapped[time] = mapped_column(Time)
    estado: Mapped[str] = mapped_column(Enum(*ESTADOS_CITA), default="pendiente")
    notas: Mapped[str | None] = mapped_column(String(300), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Se carga con la cita, como sus hermanas. En asincrono una carga
    # perezosa no puede resolverse sola: al tocar `cita.usuario` fuera
    # del contexto salta MissingGreenlet, y el mensaje no menciona ni
    # la relacion ni el atributo que lo provoco.
    usuario: Mapped["Usuario"] = relationship(
        back_populates="citas", lazy="joined"
    )
    producto: Mapped["Producto | None"] = relationship(lazy="joined")
    servicio: Mapped["Servicio"] = relationship(lazy="joined")


# --- Quinto avance: gestión comercial, PQR y chatbot -------------------------


class Venta(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # El consecutivo que ve la gente ("V-2026-0001"). Va aparte del id porque
    # el id es un detalle de la base y este no: sale en la factura, en el
    # reporte y en cualquier reclamo, así que no puede cambiar.
    numero: Mapped[str] = mapped_column(String(20), unique=True)

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    vendedor_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    descuento: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    impuestos: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    estado: Mapped[str] = mapped_column(Enum(*ESTADOS_VENTA), default="pendiente")
    notas: Mapped[str | None] = mapped_column(String(300), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # `selectin` y no `joined`: en una relación de uno a muchos el join
    # repite la fila de la venta por cada línea y luego hay que deduplicar.
    # `selectin` la resuelve en una segunda consulta y trae lo justo.
    lineas: Mapped[list["DetalleVenta"]] = relationship(
        back_populates="venta", lazy="selectin", cascade="all, delete-orphan"
    )
    cliente: Mapped["Usuario"] = relationship(foreign_keys=[usuario_id], lazy="joined")
    vendedor: Mapped["Usuario | None"] = relationship(
        foreign_keys=[vendedor_id], lazy="joined"
    )
    factura: Mapped["Factura | None"] = relationship(
        back_populates="venta", lazy="selectin"
    )


class DetalleVenta(Base):
    """Una línea de la venta.

    Guarda copia de la descripción y del precio en vez de mirarlos en el
    catálogo. Los precios cambian, y una venta de hace tres meses tiene que
    seguir diciendo lo que se cobró entonces; si la línea consultara el precio
    actual del producto, el histórico se reescribiría solo.
    """

    __tablename__ = "detalle_ventas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"))
    producto_id: Mapped[int | None] = mapped_column(
        ForeignKey("productos.id"), nullable=True
    )
    servicio_id: Mapped[int | None] = mapped_column(
        ForeignKey("servicios.id"), nullable=True
    )
    descripcion: Mapped[str] = mapped_column(String(160))
    cantidad: Mapped[int] = mapped_column(Integer, default=1)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    descuento: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    venta: Mapped["Venta"] = relationship(back_populates="lineas")


class Factura(Base):
    __tablename__ = "facturas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"), unique=True)
    fecha_emision: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    impuestos: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    estado: Mapped[str] = mapped_column(Enum(*ESTADOS_FACTURA), default="emitida")
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    venta: Mapped["Venta"] = relationship(back_populates="factura", lazy="joined")
    lineas: Mapped[list["DetalleFactura"]] = relationship(
        back_populates="factura", lazy="selectin", cascade="all, delete-orphan"
    )


class DetalleFactura(Base):
    """Repite el detalle de la venta a propósito.

    Una factura emitida dice lo que dice. Si mañana se corrige una línea de la
    venta, la factura ya emitida no puede cambiar sola: copiarlo es lo que
    permite corregir una cosa sin falsear la otra.
    """

    __tablename__ = "detalle_facturas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    factura_id: Mapped[int] = mapped_column(ForeignKey("facturas.id"))
    descripcion: Mapped[str] = mapped_column(String(160))
    cantidad: Mapped[int] = mapped_column(Integer, default=1)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    factura: Mapped["Factura"] = relationship(back_populates="lineas")


class Pqr(Base):
    """Peticiones, quejas, reclamos y sugerencias."""

    __tablename__ = "pqr"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    tipo: Mapped[str] = mapped_column(Enum(*TIPOS_PQR))
    asunto: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(String(800))
    estado: Mapped[str] = mapped_column(Enum(*ESTADOS_PQR), default="pendiente")
    respuesta: Mapped[str | None] = mapped_column(String(800), nullable=True)
    atendido_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    autor: Mapped["Usuario"] = relationship(foreign_keys=[usuario_id], lazy="joined")
    responsable: Mapped["Usuario | None"] = relationship(
        foreign_keys=[atendido_por], lazy="joined"
    )


class Conversacion(Base):
    """Un hilo de chat.

    `usuario_id` admite nulo porque el chat atiende también a quien todavía no
    tiene cuenta: es lo primero que ve un visitante, antes de registrarse.
    """

    __tablename__ = "conversaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    titulo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ultima_actividad: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    mensajes: Mapped[list["Mensaje"]] = relationship(
        back_populates="conversacion",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="Mensaje.id",
    )


class Mensaje(Base):
    __tablename__ = "mensajes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversacion_id: Mapped[int] = mapped_column(ForeignKey("conversaciones.id"))
    rol: Mapped[str] = mapped_column(Enum(*ROLES_MENSAJE))
    contenido: Mapped[str] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    conversacion: Mapped["Conversacion"] = relationship(back_populates="mensajes")
