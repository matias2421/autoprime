"""Facturación.

Emitir es cosa del personal; consultar y descargar, también del cliente, pero
solo lo suyo.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status

from app.crud import facturas as crud_facturas
from app.dependencias import (
    FacturaRuta,
    Personal,
    SesionDep,
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
from app.reportes.pdf import factura_pdf
from app.schemas.comunes import EstadoFactura
from app.schemas.factura import FacturaSalida
from app.schemas.paginacion import PaginaDep
from app.schemas.sobres import SobreFactura, SobreFacturas

router = APIRouter(
    prefix="/api/facturas",
    tags=["Facturas"],
    dependencies=[Depends(usuario_actual)],
    responses=respuestas(PROTEGIDO),
)

PERSONAL = ("administrador", "empleado")


def _es_personal(usuario) -> bool:
    return usuario.rol.nombre in PERSONAL


def _exigir_acceso(usuario, factura) -> None:
    """La factura no guarda a quién se emitió: lo guarda su venta."""
    if _es_personal(usuario):
        return
    if factura.venta is None or factura.venta.usuario_id != usuario.id:
        raise PermisoDenegado("Esa factura no te pertenece.")


@router.get(
    "",
    response_model=SobreFacturas,
    summary="Listar facturas",
    responses=respuestas(NO_VALIDO),
)
async def listar(
    sesion: SesionDep,
    usuario: UsuarioActual,
    pagina: PaginaDep,
    estado: EstadoFactura | None = None,
    desde: date | None = Query(default=None, description="Desde esta fecha"),
    hasta: date | None = Query(default=None, description="Hasta esta fecha"),
) -> SobreFacturas:
    solo_mias = None if _es_personal(usuario) else usuario.id
    total = await crud_facturas.contar(sesion, solo_mias, estado, desde, hasta)
    facturas = await crud_facturas.listar(
        sesion,
        solo_mias,
        estado,
        desde,
        hasta,
        limite=pagina.limite,
        desplazamiento=pagina.desplazamiento,
    )
    return SobreFacturas(
        facturas=[FacturaSalida.desde_modelo(f) for f in facturas],
        total=total,
        pagina=pagina.resultado(total),
    )


@router.post(
    "/venta/{venta_id}",
    response_model=SobreFactura,
    status_code=status.HTTP_201_CREATED,
    summary="Emitir la factura de una venta",
    responses=respuestas(NO_ENCONTRADO, CONFLICTO),
)
async def emitir(venta: VentaRuta, sesion: SesionDep, _: Personal) -> SobreFactura:
    """Una venta, una factura. Reintentarlo responde 409, no una segunda."""
    factura = await crud_facturas.emitir(sesion, venta)
    return SobreFactura(factura=FacturaSalida.desde_modelo(factura))


@router.get(
    "/{factura_id}",
    response_model=SobreFactura,
    summary="Consultar una factura",
    responses=respuestas(NO_ENCONTRADO),
)
async def obtener(factura: FacturaRuta, usuario: UsuarioActual) -> SobreFactura:
    _exigir_acceso(usuario, factura)
    return SobreFactura(factura=FacturaSalida.desde_modelo(factura))


@router.patch(
    "/{factura_id}/anular",
    response_model=SobreFactura,
    summary="Anular una factura",
    responses=respuestas(NO_ENCONTRADO),
)
async def anular(factura: FacturaRuta, sesion: SesionDep, _: Personal) -> SobreFactura:
    """Una factura se anula, no se borra.

    Borrarla dejaría un hueco en el consecutivo, y un consecutivo con huecos
    no sirve para lo único que hace falta: demostrar que no falta ninguna.
    Por eso no hay DELETE en este router.
    """
    return SobreFactura(
        factura=FacturaSalida.desde_modelo(
            await crud_facturas.anular(sesion, factura)
        )
    )


@router.get(
    "/{factura_id}/pdf",
    summary="Descargar la factura en PDF",
    response_class=Response,
    responses=respuestas(
        NO_ENCONTRADO,
        {
            200: {
                "content": {"application/pdf": {}},
                "description": "La factura lista para imprimir o archivar",
            }
        },
    ),
)
async def descargar(factura: FacturaRuta, usuario: UsuarioActual) -> Response:
    """El cliente descarga la suya; el personal, cualquiera.

    El PDF se arma en memoria y se devuelve en la misma respuesta: guardarlo
    en disco obligaria a decidir donde, a limpiarlo despues y a confiar en un
    disco que en Render es efimero y desaparece con cada despliegue.
    """
    _exigir_acceso(usuario, factura)
    return Response(
        content=factura_pdf(factura),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{factura.numero}.pdf"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
