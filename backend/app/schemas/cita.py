"""Esquemas de cita (el agendamiento del taller)."""

from datetime import date, datetime, time, timedelta

from pydantic import Field, field_validator

from app.schemas.comunes import Esquema, EstadoCita

# Reglas de agenda, las mismas que ya aplicaba el formulario.
DIAS_MAXIMOS = 60
HORA_APERTURA = time(8, 0)
HORA_CIERRE = time(18, 0)


def _comprobar_fecha(valor: date) -> date:
    """Reglas de agenda, compartidas por el alta y la reprogramacion."""
    hoy = date.today()
    if valor < hoy:
        raise ValueError("No puedes agendar en una fecha pasada.")
    # weekday(): el domingo es 6
    if valor.weekday() == 6:
        raise ValueError("Los domingos no atendemos.")
    if valor > hoy + timedelta(days=DIAS_MAXIMOS):
        raise ValueError(f"Solo agendamos hasta {DIAS_MAXIMOS} dias adelante.")
    return valor


def _comprobar_hora(valor: time) -> time:
    if not (HORA_APERTURA <= valor <= HORA_CIERRE):
        raise ValueError(
            f"El taller atiende de {HORA_APERTURA:%H:%M} a {HORA_CIERRE:%H:%M}."
        )
    return valor


class CitaCrear(Esquema):
    """Cuerpo de `POST /api/citas`.

    El `usuario_id` NO se acepta desde fuera: sale del token. Si viniera en
    el cuerpo, cualquiera podría agendar a nombre de otra persona.
    """

    servicio_id: int = Field(ge=1)
    producto_id: int | None = Field(default=None, ge=1)
    fecha: date
    hora: time
    notas: str | None = Field(default=None, max_length=300)

    _valida_fecha = field_validator("fecha")(_comprobar_fecha)
    _valida_hora = field_validator("hora")(_comprobar_hora)


class CambioEstadoCita(Esquema):
    """Cuerpo de `PATCH /api/citas/{id}/estado`."""

    estado: EstadoCita


class CitaActualizar(Esquema):
    """Reprogramacion: cambiar fecha, hora, servicio, vehiculo o notas."""

    servicio_id: int | None = Field(default=None, ge=1)
    producto_id: int | None = Field(default=None, ge=1)
    fecha: date | None = None
    hora: time | None = None
    notas: str | None = Field(default=None, max_length=300)

    _valida_fecha = field_validator("fecha")(_comprobar_fecha)
    _valida_hora = field_validator("hora")(_comprobar_hora)


class CitaSalida(Esquema):
    id: int
    usuario_id: int
    producto_id: int | None
    servicio_id: int
    fecha: date
    hora: time
    estado: str
    notas: str | None
    creado_en: datetime

    # Nombres legibles, para que el panel no tenga que cruzar tablas.
    cliente: str | None = None
    servicio: str | None = None
    vehiculo: str | None = None

    @classmethod
    def desde_modelo(cls, c) -> "CitaSalida":
        return cls(
            id=c.id,
            usuario_id=c.usuario_id,
            producto_id=c.producto_id,
            servicio_id=c.servicio_id,
            fecha=c.fecha,
            hora=c.hora,
            estado=c.estado,
            notas=c.notas,
            creado_en=c.creado_en,
            cliente=f"{c.usuario.nombre} {c.usuario.apellido}" if c.usuario else None,
            servicio=c.servicio.nombre if c.servicio else None,
            vehiculo=(
                f"{c.producto.marca} {c.producto.modelo}" if c.producto else None
            ),
        )


class FranjaDisponible(Esquema):
    """Una hora libre en la agenda de un dia."""

    hora: str
    disponible: bool


class ResumenCitas(Esquema):
    """Contadores para la cabecera de los paneles."""

    total: int
    pendientes: int
    confirmadas: int
    canceladas: int
    completadas: int
