"""Dependencias inyectables.

Una dependencia no es solo código compartido: es el punto donde se resuelve
la sesión de base de datos, la identidad de quien pide y su permiso. Al
declararlas aquí, cada endpoint recibe todo eso ya comprobado.
"""

from typing import Annotated

from fastapi import Depends, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.base_datos import obtener_sesion
from app.core.seguridad import JWTError, decodificar_token
from app.crud import citas as crud_citas
from app.crud import productos as crud_productos
from app.crud import servicios as crud_servicios
from app.crud import usuarios as crud_usuarios
from app.errores import NoAutenticado, PermisoDenegado
from app.models.autoprime import Cita, Producto, Servicio, Usuario

# --- Sesión de base de datos ---
SesionDep = Annotated[Session, Depends(obtener_sesion)]

# `auto_error=False` para poder lanzar nuestro propio 401 con el formato de
# error de la API, en vez del que trae FastAPI por defecto.
esquema_bearer = HTTPBearer(auto_error=False, description="Token JWT del login")


# --- Autenticación ---
def usuario_actual(
    sesion: SesionDep,
    credenciales: Annotated[
        HTTPAuthorizationCredentials | None, Depends(esquema_bearer)
    ],
) -> Usuario:
    """Valida el token y devuelve el usuario. Falla con 401."""
    if credenciales is None:
        raise NoAutenticado("Falta la cabecera Authorization con el token.")

    try:
        carga = decodificar_token(credenciales.credentials)
    except JWTError:
        # python-jose usa una sola excepción para firma inválida y expiración.
        raise NoAutenticado("El token no es válido o ya expiró.")

    identificador = carga.get("sub")
    if identificador is None:
        raise NoAutenticado("El token no identifica a ningún usuario.")

    usuario = crud_usuarios.obtener(sesion, int(identificador))

    # Que el token sea válido no significa que la cuenta siga vigente: se
    # relee el usuario para que inactivarlo surta efecto de inmediato, sin
    # esperar a que caduque el token que ya tiene en el navegador.
    if usuario is None or usuario.estado != "activo":
        raise NoAutenticado("La cuenta no existe o está inactiva.")

    return usuario


UsuarioActual = Annotated[Usuario, Depends(usuario_actual)]


# --- Autorización por rol ---
def permitir_roles(*roles: str):
    """Fabrica una dependencia que exige uno de los roles indicados.

    La identidad ya está establecida cuando esto corre; aquí solo se decide
    el permiso, que es un 403 y no un 401.
    """

    def comprobar(usuario: UsuarioActual) -> Usuario:
        if usuario.rol.nombre not in roles:
            legibles = " o ".join(roles)
            raise PermisoDenegado(
                f"Esta operación está reservada al rol {legibles}."
            )
        return usuario

    return comprobar


SoloAdmin = Annotated[Usuario, Depends(permitir_roles("administrador"))]
Personal = Annotated[Usuario, Depends(permitir_roles("administrador", "empleado"))]


# --- Recursos de la ruta, ya resueltos ---
def obtener_usuario_ruta(
    sesion: SesionDep, usuario_id: Annotated[int, Path(ge=1)]
) -> Usuario:
    return crud_usuarios.obtener_o_fallar(sesion, usuario_id)


def obtener_producto_ruta(
    sesion: SesionDep, producto_id: Annotated[int, Path(ge=1)]
) -> Producto:
    return crud_productos.obtener_o_fallar(sesion, producto_id)


def obtener_servicio_ruta(
    sesion: SesionDep, servicio_id: Annotated[int, Path(ge=1)]
) -> Servicio:
    return crud_servicios.obtener_o_fallar(sesion, servicio_id)


def obtener_cita_ruta(
    sesion: SesionDep, cita_id: Annotated[int, Path(ge=1)]
) -> Cita:
    return crud_citas.obtener_o_fallar(sesion, cita_id)


UsuarioRuta = Annotated[Usuario, Depends(obtener_usuario_ruta)]
ProductoRuta = Annotated[Producto, Depends(obtener_producto_ruta)]
ServicioRuta = Annotated[Servicio, Depends(obtener_servicio_ruta)]
CitaRuta = Annotated[Cita, Depends(obtener_cita_ruta)]
