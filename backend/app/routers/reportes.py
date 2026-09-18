"""Reportes y tableros.

El mismo periodo se sirve de tres maneras —JSON para las gráficas, PDF para
imprimir, Excel para analizar— y las tres salen de la misma consulta. Que
compartan el armado no es ahorro de líneas: es lo que garantiza que el PDF
diga el mismo número que la pantalla de la que se descargó.

Los tres respetan el rol de quien pide: un cliente que descargue el reporte
obtiene el suyo, no el del negocio.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import reportes as crud_reportes
from app.crud import ventas as crud_ventas
from app.dependencias import Personal, SesionDep, UsuarioActual, usuario_actual
from app.documentacion import NO_VALIDO, PROTEGIDO, respuestas
from app.errores import DatosInvalidos
from app.reportes.excel import reporte_ventas_excel
from app.reportes.pdf import reporte_ventas_pdf
from app.schemas.reporte import (
    CorteConcepto,
    CorteEstado,
    PanelAdministrativo,
    PuntoDiario,
    Rango,
    ReporteVentas,
    SobrePanel,
    SobreReporteVentas,
)
from app.schemas.venta import ResumenVentas

router = APIRouter(
    prefix="/api/reportes",
    tags=["Reportes"],
    dependencies=[Depends(usuario_actual)],
    responses=respuestas(PROTEGIDO),
)

PERSONAL = ("administrador", "empleado")

# Un reporte de más de un año en un solo documento no se lee: se descarga,
# se abre y se cierra. El tope está para que una petición no intente armar
# un PDF de diez mil filas y agotar la memoria del contenedor.
DIAS_MAXIMOS = 366

TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _es_personal(usuario) -> bool:
    return usuario.rol.nombre in PERSONAL


def _rango(desde: date | None, hasta: date | None) -> tuple[date, date]:
    desde, hasta = crud_reportes.rango_por_defecto(desde, hasta)
    if hasta < desde:
        raise DatosInvalidos("La fecha final no puede ser anterior a la inicial.")
    if (hasta - desde).days + 1 > DIAS_MAXIMOS:
        raise DatosInvalidos(
            f"El reporte abarca como máximo {DIAS_MAXIMOS} días. "
            "Divide el periodo en tramos."
        )
    return desde, hasta


async def _armar(
    sesion: AsyncSession, usuario, desde: date, hasta: date
) -> dict:
    """Junta todas las piezas del reporte. Lo comparten JSON, PDF y Excel."""
    solo_mias = None if _es_personal(usuario) else usuario.id

    return {
        "desde": desde,
        "hasta": hasta,
        "alcance": (
            "Todas las ventas del negocio"
            if solo_mias is None
            else f"Compras de {usuario.nombre} {usuario.apellido}"
        ),
        "resumen": await crud_ventas.resumen(sesion, solo_mias, desde, hasta),
        "por_dia": await crud_reportes.serie_diaria(sesion, desde, hasta, solo_mias),
        "por_estado": await crud_reportes.por_estado(sesion, desde, hasta, solo_mias),
        "top_vehiculos": await crud_reportes.top_vehiculos(sesion, desde, hasta),
        "top_servicios": await crud_reportes.top_servicios(sesion, desde, hasta),
        "ventas": await crud_reportes.detalle_ventas(sesion, desde, hasta, solo_mias),
    }


def _descarga(contenido: bytes, tipo: str, nombre: str) -> Response:
    """Devuelve el archivo con las cabeceras que hacen que el navegador lo baje.

    `Content-Disposition: attachment` es lo que convierte la respuesta en una
    descarga con nombre en vez de un intento del navegador de mostrarla.
    """
    return Response(
        content=contenido,
        media_type=tipo,
        headers={
            "Content-Disposition": f'attachment; filename="{nombre}"',
            # El frontend lee el nombre del archivo de esta cabecera, y sin
            # exponerla el navegador no se la deja ver a JavaScript por ser
            # una petición de otro origen.
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


def _nombre(prefijo: str, desde: date, hasta: date, extension: str) -> str:
    periodo = f"{desde:%Y-%m-%d}" if desde == hasta else f"{desde:%Y-%m-%d}_{hasta:%Y-%m-%d}"
    return f"{prefijo}_{periodo}.{extension}"


@router.get(
    "/panel",
    response_model=SobrePanel,
    summary="Cifras del tablero administrativo",
)
async def panel(sesion: SesionDep, _: Personal) -> SobrePanel:
    """Reservado al personal: son cifras de todo el negocio, no de una cuenta."""
    datos = await crud_reportes.panel_administrativo(sesion)
    return SobrePanel(panel=PanelAdministrativo(**datos))


@router.get(
    "/ventas",
    response_model=SobreReporteVentas,
    summary="Reporte de ventas del periodo",
    responses=respuestas(NO_VALIDO),
)
async def ventas(
    sesion: SesionDep,
    usuario: UsuarioActual,
    desde: date | None = Query(default=None, description="Por omisión, hoy"),
    hasta: date | None = Query(default=None, description="Por omisión, hoy"),
) -> SobreReporteVentas:
    """Sin fechas devuelve el reporte diario, que es el que se pide a diario."""
    desde, hasta = _rango(desde, hasta)
    datos = await _armar(sesion, usuario, desde, hasta)

    return SobreReporteVentas(
        reporte=ReporteVentas(
            rango=Rango(desde=desde, hasta=hasta, dias=(hasta - desde).days + 1),
            alcance=datos["alcance"],
            resumen=ResumenVentas(**datos["resumen"]),
            por_dia=[PuntoDiario(**p) for p in datos["por_dia"]],
            por_estado=[CorteEstado(**c) for c in datos["por_estado"]],
            top_vehiculos=[CorteConcepto(**c) for c in datos["top_vehiculos"]],
            top_servicios=[CorteConcepto(**c) for c in datos["top_servicios"]],
        )
    )


@router.get(
    "/ventas/pdf",
    summary="Descargar el reporte en PDF",
    response_class=Response,
    responses=respuestas(
        NO_VALIDO,
        {
            200: {
                "content": {"application/pdf": {}},
                "description": "El reporte del periodo, listo para imprimir",
            }
        },
    ),
)
async def ventas_pdf(
    sesion: SesionDep,
    usuario: UsuarioActual,
    desde: date | None = None,
    hasta: date | None = None,
) -> Response:
    desde, hasta = _rango(desde, hasta)
    datos = await _armar(sesion, usuario, desde, hasta)
    return _descarga(
        reporte_ventas_pdf(datos),
        "application/pdf",
        _nombre("reporte_ventas", desde, hasta, "pdf"),
    )


@router.get(
    "/ventas/excel",
    summary="Descargar el reporte en Excel",
    response_class=Response,
    responses=respuestas(
        NO_VALIDO,
        {
            200: {
                "content": {TIPO_EXCEL: {}},
                "description": "Libro con resumen, detalle, líneas y una gráfica",
            }
        },
    ),
)
async def ventas_excel(
    sesion: SesionDep,
    usuario: UsuarioActual,
    desde: date | None = None,
    hasta: date | None = None,
) -> Response:
    desde, hasta = _rango(desde, hasta)
    datos = await _armar(sesion, usuario, desde, hasta)
    return _descarga(
        reporte_ventas_excel(datos),
        TIPO_EXCEL,
        _nombre("reporte_ventas", desde, hasta, "xlsx"),
    )
