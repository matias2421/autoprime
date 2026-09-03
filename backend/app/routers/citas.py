"""Agenda de citas del taller."""

from datetime import date

from fastapi import APIRouter, Query, status

from app.crud import citas as crud_citas
from app.dependencias import CitaRuta, Personal, SesionDep, UsuarioActual
from app.errores import PermisoDenegado
from app.schemas.cita import (
    CambioEstadoCita,
    CitaActualizar,
    CitaCrear,
    CitaSalida,
    FranjaDisponible,
    ResumenCitas,
)
from app.schemas.comunes import EstadoCita, RespuestaSimple
from app.schemas.sobres import (
    SobreCita,
    SobreCitas,
    SobreDisponibilidad,
    SobreResumen,
)

router = APIRouter(prefix="/api/citas", tags=["Citas"])

PERSONAL = ("administrador", "empleado")


def _es_personal(usuario) -> bool:
    return usuario.rol.nombre in PERSONAL


def _puede_ver(usuario, cita) -> bool:
    """El personal ve todas las citas; un cliente, solo las suyas."""
    return _es_personal(usuario) or cita.usuario_id == usuario.id


@router.get(
    "/disponibilidad",
    response_model=SobreDisponibilidad,
    summary="Franjas libres de un día",
)
def disponibilidad(
    sesion: SesionDep,
    fecha: date,
    # El frontend envía `productoId`: los parámetros de consulta no pasan por
    # el generador de alias de los esquemas, así que se declara aquí a mano.
    producto_id: int | None = Query(default=None, ge=1, alias="productoId"),
) -> SobreDisponibilidad:
    """Consulta pública: el formulario la usa antes de pedir iniciar sesión."""
    horas = [
        FranjaDisponible(**f) for f in crud_citas.franjas_de(sesion, fecha, producto_id)
    ]
    return SobreDisponibilidad(fecha=fecha.isoformat(), horas=horas)


@router.get("/resumen", response_model=SobreResumen, summary="Contadores por estado")
def resumen(sesion: SesionDep, usuario: UsuarioActual) -> SobreResumen:
    """Un cliente ve el resumen de sus citas; el personal, el de todas."""
    solo_mias = None if _es_personal(usuario) else usuario.id
    datos = crud_citas.resumen(sesion, usuario_id=solo_mias)
    return SobreResumen(resumen=ResumenCitas(**datos))


@router.get("", response_model=SobreCitas, summary="Listar citas")
def listar(
    sesion: SesionDep,
    usuario: UsuarioActual,
    estado: EstadoCita | None = None,
) -> SobreCitas:
    solo_mias = None if _es_personal(usuario) else usuario.id
    citas = crud_citas.listar(sesion, usuario_id=solo_mias, estado=estado)
    salida = [CitaSalida.desde_modelo(c) for c in citas]
    return SobreCitas(citas=salida, total=len(salida))


@router.post(
    "",
    response_model=SobreCita,
    status_code=status.HTTP_201_CREATED,
    summary="Agendar una cita",
)
def crear(datos: CitaCrear, sesion: SesionDep, usuario: UsuarioActual) -> SobreCita:
    """El dueño de la cita sale del token, nunca del cuerpo de la petición."""
    cita = crud_citas.crear(sesion, usuario.id, datos.model_dump())
    return SobreCita(cita=CitaSalida.desde_modelo(cita))


@router.get("/{cita_id}", response_model=SobreCita, summary="Consultar una cita")
def obtener(cita: CitaRuta, usuario: UsuarioActual) -> SobreCita:
    if not _puede_ver(usuario, cita):
        raise PermisoDenegado("Esa cita no te pertenece.")
    return SobreCita(cita=CitaSalida.desde_modelo(cita))


@router.put("/{cita_id}", response_model=SobreCita, summary="Reprogramar")
def actualizar(
    datos: CitaActualizar,
    cita: CitaRuta,
    sesion: SesionDep,
    usuario: UsuarioActual,
) -> SobreCita:
    if not _puede_ver(usuario, cita):
        raise PermisoDenegado("Esa cita no te pertenece.")
    cambios = datos.model_dump(exclude_unset=True)
    return SobreCita(cita=CitaSalida.desde_modelo(crud_citas.actualizar(sesion, cita, cambios)))


@router.patch("/{cita_id}/estado", response_model=SobreCita, summary="Cambiar estado")
def cambiar_estado(
    datos: CambioEstadoCita,
    cita: CitaRuta,
    sesion: SesionDep,
    usuario: UsuarioActual,
) -> SobreCita:
    """Confirmar y completar son del personal; un cliente solo puede cancelar
    la suya."""
    if not _es_personal(usuario):
        if cita.usuario_id != usuario.id:
            raise PermisoDenegado("Esa cita no te pertenece.")
        if datos.estado != "cancelada":
            raise PermisoDenegado("Solo puedes cancelar tu cita.")

    actualizada = crud_citas.cambiar_estado(sesion, cita, datos.estado)
    return SobreCita(cita=CitaSalida.desde_modelo(actualizada))


@router.delete("/{cita_id}", response_model=RespuestaSimple, summary="Eliminar")
def eliminar(cita: CitaRuta, sesion: SesionDep, _: Personal) -> RespuestaSimple:
    crud_citas.eliminar(sesion, cita)
    return RespuestaSimple(mensaje="Cita eliminada.")
