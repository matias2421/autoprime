"""Canal de PQR: peticiones, quejas, reclamos y sugerencias.

Un cliente radica y consulta lo suyo. El personal ve la bandeja entera y
responde. Un cliente no puede leer el reclamo de otro —que en un canal de
quejas es justo el dato más delicado que hay— ni marcar el suyo como
respondido.
"""

from fastapi import APIRouter, Depends, Response, status

from app.crud import pqr as crud_pqr
from app.dependencias import Personal, PqrRuta, SesionDep, SoloAdmin, UsuarioActual
from app.dependencias import usuario_actual
from app.documentacion import (
    CONFLICTO,
    NO_ENCONTRADO,
    NO_VALIDO,
    PROTEGIDO,
    respuestas,
)
from app.errores import PermisoDenegado
from app.schemas.comunes import EstadoPqr, TipoPqr
from app.schemas.paginacion import PaginaDep
from app.schemas.pqr import (
    CambioEstadoPqr,
    PqrCrear,
    PqrResponder,
    PqrSalida,
    ResumenPqr,
)
from app.schemas.sobres import SobrePqr, SobrePqrs, SobreResumenPqr

router = APIRouter(
    prefix="/api/pqr",
    tags=["PQR"],
    dependencies=[Depends(usuario_actual)],
    responses=respuestas(PROTEGIDO),
)

PERSONAL = ("administrador", "empleado")


def _es_personal(usuario) -> bool:
    return usuario.rol.nombre in PERSONAL


def _exigir_acceso(usuario, registro) -> None:
    if not _es_personal(usuario) and registro.usuario_id != usuario.id:
        raise PermisoDenegado("Esa PQR no te pertenece.")


@router.get(
    "/resumen", response_model=SobreResumenPqr, summary="Contadores por estado"
)
async def resumen(sesion: SesionDep, usuario: UsuarioActual) -> SobreResumenPqr:
    solo_mias = None if _es_personal(usuario) else usuario.id
    return SobreResumenPqr(resumen=ResumenPqr(**await crud_pqr.resumen(sesion, solo_mias)))


@router.get(
    "",
    response_model=SobrePqrs,
    summary="Listar PQR",
    responses=respuestas(NO_VALIDO),
)
async def listar(
    sesion: SesionDep,
    usuario: UsuarioActual,
    pagina: PaginaDep,
    estado: EstadoPqr | None = None,
    tipo: TipoPqr | None = None,
) -> SobrePqrs:
    """Para el personal es una bandeja de trabajo, así que lo pendiente va
    primero; para un cliente, la lista de lo que ha radicado."""
    solo_mias = None if _es_personal(usuario) else usuario.id
    total = await crud_pqr.contar(sesion, solo_mias, estado, tipo)
    registros = await crud_pqr.listar(
        sesion,
        solo_mias,
        estado,
        tipo,
        limite=pagina.limite,
        desplazamiento=pagina.desplazamiento,
    )
    return SobrePqrs(
        pqr=[PqrSalida.desde_modelo(p) for p in registros],
        total=total,
        pagina=pagina.resultado(total),
    )


@router.post(
    "",
    response_model=SobrePqr,
    status_code=status.HTTP_201_CREATED,
    summary="Radicar una PQR",
    responses=respuestas(NO_VALIDO),
)
async def crear(
    datos: PqrCrear, sesion: SesionDep, usuario: UsuarioActual
) -> SobrePqr:
    """Quien radica sale del token. El estado y el número los pone el sistema."""
    registro = await crud_pqr.crear(sesion, usuario.id, datos.model_dump())
    return SobrePqr(pqr=PqrSalida.desde_modelo(registro))


@router.get(
    "/{pqr_id}",
    response_model=SobrePqr,
    summary="Consultar una PQR",
    responses=respuestas(NO_ENCONTRADO),
)
async def obtener(registro: PqrRuta, usuario: UsuarioActual) -> SobrePqr:
    _exigir_acceso(usuario, registro)
    return SobrePqr(pqr=PqrSalida.desde_modelo(registro))


@router.patch(
    "/{pqr_id}/responder",
    response_model=SobrePqr,
    summary="Responder",
    responses=respuestas(NO_ENCONTRADO, CONFLICTO, NO_VALIDO),
)
async def responder(
    datos: PqrResponder,
    registro: PqrRuta,
    sesion: SesionDep,
    usuario: Personal,
) -> SobrePqr:
    """Deja la respuesta y quién la firmó. Una PQR cerrada ya no se responde."""
    actualizada = await crud_pqr.responder(
        sesion, registro, datos.respuesta, datos.estado, usuario.id
    )
    return SobrePqr(pqr=PqrSalida.desde_modelo(actualizada))


@router.patch(
    "/{pqr_id}/estado",
    response_model=SobrePqr,
    summary="Cambiar el estado",
    responses=respuestas(NO_ENCONTRADO, CONFLICTO, NO_VALIDO),
)
async def cambiar_estado(
    datos: CambioEstadoPqr, registro: PqrRuta, sesion: SesionDep, _: Personal
) -> SobrePqr:
    actualizada = await crud_pqr.cambiar_estado(sesion, registro, datos.estado)
    return SobrePqr(pqr=PqrSalida.desde_modelo(actualizada))


@router.delete(
    "/{pqr_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una PQR",
    responses=respuestas(NO_ENCONTRADO),
)
async def eliminar(registro: PqrRuta, sesion: SesionDep, _: SoloAdmin) -> Response:
    """Reservado al administrador. Lo normal es cerrarla, no borrarla: un
    canal de quejas que permite hacer desaparecer una queja no sirve de
    canal de quejas."""
    await crud_pqr.eliminar(sesion, registro)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
