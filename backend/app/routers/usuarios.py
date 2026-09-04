"""Gestión de usuarios (panel de administración)."""

from fastapi import APIRouter, Query, status

from app.crud import usuarios as crud_usuarios
from app.dependencias import SesionDep, SoloAdmin, UsuarioRuta
from app.routers.auth import registrar
from app.schemas.auth import Sesion
from app.schemas.comunes import EstadoCuenta, NombreRol, RespuestaSimple
from app.schemas.sobres import SobreUsuario, SobreUsuarios
from app.schemas.usuario import (
    CambioEstado,
    UsuarioActualizar,
    UsuarioCrear,
    UsuarioRegistro,
    UsuarioSalida,
)

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])


@router.post(
    "/registro",
    response_model=Sesion,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un cliente (misma alta que POST /api/auth/registro)",
)
def registro_publico(datos: UsuarioRegistro, sesion: SesionDep) -> Sesion:
    """Alta pública de clientes, sin token.

    Es la misma función que atiende `POST /api/auth/registro`, expuesta
    también aquí porque es la ruta que nombra la lista de chequeo del
    entregable. Se reutiliza el manejador en lugar de copiarlo para que no
    puedan acabar comportándose distinto.

    Va declarada antes que `/{usuario_id}` para que "registro" no se intente
    interpretar como un identificador.
    """
    return registrar(datos, sesion)


@router.get("", response_model=SobreUsuarios, summary="Listar usuarios")
def listar(
    sesion: SesionDep,
    _: SoloAdmin,
    rol: NombreRol | None = None,
    estado: EstadoCuenta | None = None,
    buscar: str | None = Query(default=None, min_length=2, max_length=60),
) -> SobreUsuarios:
    usuarios = crud_usuarios.listar(sesion, rol=rol, estado=estado, buscar=buscar)
    salida = [UsuarioSalida.desde_modelo(u) for u in usuarios]
    return SobreUsuarios(usuarios=salida, total=len(salida))


@router.post(
    "",
    response_model=SobreUsuario,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
)
def crear(datos: UsuarioCrear, sesion: SesionDep, _: SoloAdmin) -> SobreUsuario:
    """Alta desde el panel: aquí sí se puede elegir el rol."""
    cuerpo = datos.model_dump()
    rol = cuerpo.pop("rol")
    usuario = crud_usuarios.crear(sesion, cuerpo, rol_nombre=rol)
    return SobreUsuario(usuario=UsuarioSalida.desde_modelo(usuario))


@router.get("/{usuario_id}", response_model=SobreUsuario, summary="Consultar uno")
def obtener(usuario: UsuarioRuta, _: SoloAdmin) -> SobreUsuario:
    return SobreUsuario(usuario=UsuarioSalida.desde_modelo(usuario))


@router.put("/{usuario_id}", response_model=SobreUsuario, summary="Actualizar")
def actualizar(
    datos: UsuarioActualizar,
    usuario: UsuarioRuta,
    sesion: SesionDep,
    _: SoloAdmin,
) -> SobreUsuario:
    cambios = datos.model_dump(exclude_unset=True)
    actualizado = crud_usuarios.actualizar(sesion, usuario, cambios)
    return SobreUsuario(usuario=UsuarioSalida.desde_modelo(actualizado))


@router.patch(
    "/{usuario_id}/estado", response_model=SobreUsuario, summary="Activar o inactivar"
)
def cambiar_estado(
    datos: CambioEstado,
    usuario: UsuarioRuta,
    sesion: SesionDep,
    _: SoloAdmin,
) -> SobreUsuario:
    """Se prefiere inactivar a borrar: conserva el histórico de citas."""
    actualizado = crud_usuarios.cambiar_estado(sesion, usuario, datos.estado)
    return SobreUsuario(usuario=UsuarioSalida.desde_modelo(actualizado))


@router.delete("/{usuario_id}", response_model=RespuestaSimple, summary="Eliminar")
def eliminar(
    usuario: UsuarioRuta, sesion: SesionDep, _: SoloAdmin
) -> RespuestaSimple:
    crud_usuarios.eliminar(sesion, usuario)
    return RespuestaSimple(mensaje="Usuario eliminado.")
