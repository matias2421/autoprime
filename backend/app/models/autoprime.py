"""Modelos SQLAlchemy: el mapeo de las tablas que ya existen en MySQL.

El esquema es el del tercer avance (`sql/autoprime.sql`) y no cambia: aquí
solo se describe para que SQLAlchemy sepa leerlo y escribirlo. Por eso las
tablas NO se crean desde el código — se cargan con el script SQL, que es la
fuente de verdad del esquema.
"""

from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
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

    usuario: Mapped["Usuario"] = relationship(back_populates="citas")
    producto: Mapped["Producto | None"] = relationship(lazy="joined")
    servicio: Mapped["Servicio"] = relationship(lazy="joined")
