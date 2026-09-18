"""Servicios del taller."""

from fastapi import APIRouter, status

from app.crud import servicios as crud_servicios
from app.dependencias import Personal, SesionDep, ServicioRuta, SoloAdmin
from app.schemas.comunes import EstadoCuenta, RespuestaSimple
from app.schemas.servicio import ServicioActualizar, ServicioCrear, ServicioSalida
from app.schemas.sobres import SobreServicio, SobreServicios

router = APIRouter(prefix="/api/servicios", tags=["Servicios"])


@router.get("", response_model=SobreServicios, summary="Listar servicios")
async def listar(sesion: SesionDep, estado: EstadoCuenta | None = None) -> SobreServicios:
    """Consulta pública: hace falta para el formulario de agendar cita."""
    salida = [
        ServicioSalida.model_validate(s)
        for s in await crud_servicios.listar(sesion, estado=estado)
    ]
    return SobreServicios(servicios=salida, total=len(salida))


@router.post(
    "",
    response_model=SobreServicio,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un servicio",
)
async def crear(datos: ServicioCrear, sesion: SesionDep, _: Personal) -> SobreServicio:
    servicio = await crud_servicios.crear(sesion, datos.model_dump())
    return SobreServicio(servicio=ServicioSalida.model_validate(servicio))


@router.get("/{servicio_id}", response_model=SobreServicio, summary="Consultar uno")
async def obtener(servicio: ServicioRuta) -> SobreServicio:
    return SobreServicio(servicio=ServicioSalida.model_validate(servicio))


@router.put("/{servicio_id}", response_model=SobreServicio, summary="Actualizar")
async def actualizar(
    datos: ServicioActualizar,
    servicio: ServicioRuta,
    sesion: SesionDep,
    _: Personal,
) -> SobreServicio:
    cambios = datos.model_dump(exclude_unset=True)
    actualizado = await crud_servicios.actualizar(sesion, servicio, cambios)
    return SobreServicio(servicio=ServicioSalida.model_validate(actualizado))


@router.delete("/{servicio_id}", response_model=RespuestaSimple, summary="Eliminar")
async def eliminar(
    servicio: ServicioRuta, sesion: SesionDep, _: SoloAdmin
) -> RespuestaSimple:
    await crud_servicios.eliminar(sesion, servicio)
    return RespuestaSimple(mensaje="Servicio eliminado.")
