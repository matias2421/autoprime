"""Esquemas de PQR: peticiones, quejas, reclamos y sugerencias.

Quien radica no elige el estado ni el número: los pone el sistema. Si el
estado viniera en el cuerpo, cualquiera podría radicar una queja ya marcada
como «respondida», que es exactamente lo que un canal de reclamos no puede
permitir.
"""

from datetime import datetime

from pydantic import Field

from app.schemas.comunes import con_ejemplo, Esquema, EstadoPqr, TipoPqr


class PqrCrear(Esquema):
    """Cuerpo de `POST /api/pqr`."""

    model_config = con_ejemplo(
        tipo="reclamo",
        asunto="Demora en la entrega del peritaje",
        descripcion=("Agendé el peritaje para el lunes y aún no "
                     "recibo el informe. Necesito saber cuándo estará."),
    )

    tipo: TipoPqr
    asunto: str = Field(min_length=5, max_length=120)
    descripcion: str = Field(min_length=20, max_length=800)


class PqrResponder(Esquema):
    """Cuerpo de `PATCH /api/pqr/{id}/responder`, solo para el personal."""

    respuesta: str = Field(min_length=10, max_length=800)

    # Responder normalmente cierra el caso, pero no siempre: a veces se
    # contesta un avance y el caso sigue abierto.
    estado: EstadoPqr = "respondida"


class CambioEstadoPqr(Esquema):
    estado: EstadoPqr


class PqrSalida(Esquema):
    id: int
    numero: str
    usuario_id: int
    tipo: str
    asunto: str
    descripcion: str
    estado: str
    respuesta: str | None
    creado_en: datetime
    actualizado_en: datetime

    autor: str | None = None
    autor_correo: str | None = None
    responsable: str | None = None

    @classmethod
    def desde_modelo(cls, p) -> "PqrSalida":
        return cls(
            id=p.id,
            numero=p.numero,
            usuario_id=p.usuario_id,
            tipo=p.tipo,
            asunto=p.asunto,
            descripcion=p.descripcion,
            estado=p.estado,
            respuesta=p.respuesta,
            creado_en=p.creado_en,
            actualizado_en=p.actualizado_en,
            autor=f"{p.autor.nombre} {p.autor.apellido}" if p.autor else None,
            autor_correo=p.autor.correo if p.autor else None,
            responsable=(
                f"{p.responsable.nombre} {p.responsable.apellido}"
                if p.responsable
                else None
            ),
        )


class ResumenPqr(Esquema):
    """Contadores para la cabecera del panel de atención."""

    total: int
    pendientes: int
    en_proceso: int
    respondidas: int
    cerradas: int
