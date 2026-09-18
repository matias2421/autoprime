"""Registro de ventas.

Un cliente puede comprar (a su nombre y solo a su nombre) y ver lo que ha
comprado. El personal registra ventas de mostrador, ve todas y cambia
estados. Esa separación no está solo en la interfaz: se decide aquí, porque
la interfaz se puede saltar con Postman y este router no.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status

from app.crud import ventas as crud_ventas
from app.dependencias import (
    Personal,
    SesionDep,
    SoloAdmin,
    UsuarioActual,
    VentaRuta,
    usuario_actual,
)
from app.documentacion import (
    CONFLICTO,
    NO_ENCONTRADO,
    NO_VALIDO,
    PROTEGIDO,
    respuestas,
)
from app.errores import PermisoDenegado
from app.schemas.comunes import EstadoVenta
from app.schemas.paginacion import PaginaDep
from app.schemas.sobres import SobreResumenVentas, SobreVenta, SobreVentas
from app.schemas.venta import (
    CambioEstadoVenta,
    ResumenVentas,
    VentaCrear,
    VentaSalida,
)

router = APIRouter(
    prefix="/api/ventas",
    tags=["Ventas"],
    # Ni un solo endpoint de ventas es público, así que la autenticación se
    # exige una vez aquí y no endpoint por endpoint. Lo que cambia es lo que
    # se protege de un olvido: puesta en el router, la cubre también la ruta
    # que alguien añada mañana sin acordarse de pedir el token. Cada endpoint
    # afina después qué rol hace falta.
    #
    # FastAPI resuelve cada dependencia una sola vez por petición, así que
    # repetirla aquí y en la firma del endpoint no vuelve a leer el token.
    dependencies=[Depends(usuario_actual)],
    responses=respuestas(PROTEGIDO),
)

PERSONAL = ("administrador", "empleado")


def _es_personal(usuario) -> bool:
    return usuario.rol.nombre in PERSONAL


@router.get(
    "/resumen",
    response_model=SobreResumenVentas,
    summary="Cifras de cabecera",
    responses=respuestas(NO_VALIDO),
)
async def resumen(
    sesion: SesionDep,
    usuario: UsuarioActual,
    desde: date | None = Query(default=None, description="Desde esta fecha"),
    hasta: date | None = Query(default=None, description="Hasta esta fecha"),
) -> SobreResumenVentas:
    """Un cliente ve el resumen de sus compras; el personal, el del negocio."""
    solo_mias = None if _es_personal(usuario) else usuario.id
    datos = await crud_ventas.resumen(sesion, solo_mias, desde, hasta)
    return SobreResumenVentas(resumen=ResumenVentas(**datos))


@router.get(
    "",
    response_model=SobreVentas,
    summary="Listar ventas",
    responses=respuestas(NO_VALIDO),
)
async def listar(
    sesion: SesionDep,
    usuario: UsuarioActual,
    pagina: PaginaDep,
    estado: EstadoVenta | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> SobreVentas:
    solo_mias = None if _es_personal(usuario) else usuario.id

    # El total se cuenta con los mismos filtros que la página, no con `len()`
    # de lo devuelto: si no, la última página diría que el total es tres.
    total = await crud_ventas.contar(sesion, solo_mias, estado, desde, hasta)
    ventas = await crud_ventas.listar(
        sesion,
        solo_mias,
        estado,
        desde,
        hasta,
        limite=pagina.limite,
        desplazamiento=pagina.desplazamiento,
    )
    return SobreVentas(
        ventas=[VentaSalida.desde_modelo(v) for v in ventas],
        total=total,
        pagina=pagina.resultado(total),
    )


@router.post(
    "",
    response_model=SobreVenta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una venta",
    responses=respuestas(NO_ENCONTRADO, CONFLICTO, NO_VALIDO),
)
async def crear(
    datos: VentaCrear, sesion: SesionDep, usuario: UsuarioActual
) -> SobreVenta:
    """Registra la venta y marca como vendidos los vehículos incluidos.

    Un cliente compra a su nombre: si envía `usuarioId`, se rechaza. Solo el
    personal puede vender a nombre de otra persona, y solo el personal puede
    fijar el precio de una línea; para todos los demás, el precio lo pone el
    catálogo.
    """
    personal = _es_personal(usuario)

    if not personal:
        if datos.usuario_id is not None and datos.usuario_id != usuario.id:
            raise PermisoDenegado("Solo puedes registrar compras a tu nombre.")
        comprador_id = usuario.id
        vendedor_id = None
    else:
        comprador_id = datos.usuario_id or usuario.id
        vendedor_id = usuario.id

    venta = await crud_ventas.crear(
        sesion,
        comprador_id,
        datos.model_dump(),
        vendedor_id=vendedor_id,
        puede_fijar_precio=personal,
    )
    return SobreVenta(venta=VentaSalida.desde_modelo(venta))


@router.get(
    "/{venta_id}",
    response_model=SobreVenta,
    summary="Consultar una venta",
    responses=respuestas(NO_ENCONTRADO),
)
async def obtener(venta: VentaRuta, usuario: UsuarioActual) -> SobreVenta:
    if not _es_personal(usuario) and venta.usuario_id != usuario.id:
        raise PermisoDenegado("Esa venta no te pertenece.")
    return SobreVenta(venta=VentaSalida.desde_modelo(venta))


@router.patch(
    "/{venta_id}/estado",
    response_model=SobreVenta,
    summary="Cambiar el estado",
    responses=respuestas(NO_ENCONTRADO, NO_VALIDO),
)
async def cambiar_estado(
    datos: CambioEstadoVenta, venta: VentaRuta, sesion: SesionDep, _: Personal
) -> SobreVenta:
    """Marcar pagada o anular. Anular devuelve los vehículos al catálogo."""
    actualizada = await crud_ventas.cambiar_estado(sesion, venta, datos.estado)
    return SobreVenta(venta=VentaSalida.desde_modelo(actualizada))


@router.delete(
    "/{venta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una venta",
    responses=respuestas(NO_ENCONTRADO),
)
async def eliminar(venta: VentaRuta, sesion: SesionDep, _: SoloAdmin) -> Response:
    """Borra el registro por completo. Lo normal es anular, no borrar: una
    venta anulada sigue contando en el histórico y esta desaparece.

    Devuelve 204 sin cuerpo, que es lo que significa «hecho, y no hay nada
    que contarte»: el recurso ya no está, así que no hay nada que devolver.
    """
    await crud_ventas.eliminar(sesion, venta)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
