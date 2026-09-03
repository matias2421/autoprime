"""Autenticación: registro, login y perfil."""

from fastapi import APIRouter, status

from app.core.configuracion import configuracion
from app.core.seguridad import crear_token, verificar_contrasena
from app.crud import usuarios as crud_usuarios
from app.dependencias import SesionDep, UsuarioActual
from app.errores import NoAutenticado
from app.schemas.auth import Credenciales, Sesion
from app.schemas.usuario import UsuarioRegistro, UsuarioSalida

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post(
    "/registro",
    response_model=Sesion,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un cliente",
)
def registrar(datos: UsuarioRegistro, sesion: SesionDep) -> Sesion:
    """Alta pública. Siempre con rol de cliente y contraseña hasheada.

    Devuelve ya la sesión iniciada: quien acaba de registrarse entra sin
    tener que escribir de nuevo sus credenciales, que es como se comportaba
    el formulario desde el segundo avance.
    """
    usuario = crud_usuarios.crear(sesion, datos.model_dump(), rol_nombre="cliente")

    return Sesion(
        token=crear_token(usuario.id, usuario.correo, usuario.rol.nombre),
        expira_en_horas=configuracion.horas_expiracion_token,
        usuario=UsuarioSalida.desde_modelo(usuario),
    )


@router.post("/login", response_model=Sesion, summary="Iniciar sesión")
def iniciar_sesion(credenciales: Credenciales, sesion: SesionDep) -> Sesion:
    """Verifica las credenciales y emite un JWT."""
    usuario = crud_usuarios.obtener_por_correo(sesion, credenciales.correo)

    # Mismo mensaje si el correo no existe o si la contraseña falla: decir
    # cuál de las dos falló revelaría qué correos están registrados.
    if usuario is None or not verificar_contrasena(
        credenciales.password, usuario.password_hash
    ):
        raise NoAutenticado("Correo o contraseña incorrectos.")

    if usuario.estado != "activo":
        raise NoAutenticado("La cuenta está inactiva. Contacta con el atelier.")

    return Sesion(
        token=crear_token(usuario.id, usuario.correo, usuario.rol.nombre),
        expira_en_horas=configuracion.horas_expiracion_token,
        usuario=UsuarioSalida.desde_modelo(usuario),
    )


@router.get("/perfil", response_model=UsuarioSalida, summary="Perfil propio")
def perfil(usuario: UsuarioActual) -> UsuarioSalida:
    """Devuelve el usuario del token. Sirve para revalidar la sesión."""
    return UsuarioSalida.desde_modelo(usuario)
