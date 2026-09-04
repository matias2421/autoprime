"""Autenticación: registro, login y perfil."""

from fastapi import APIRouter, status

from app.core.configuracion import configuracion
from app.core.seguridad import (
    TIPO_RECUPERACION,
    JWTError,
    crear_token,
    crear_token_recuperacion,
    decodificar_token,
    huella_contrasena,
    verificar_contrasena,
)
from app.crud import usuarios as crud_usuarios
from app.dependencias import SesionDep, UsuarioActual
from app.errores import NoAutenticado
from app.schemas.auth import (
    AvisoRecuperacion,
    Credenciales,
    RestablecerContrasena,
    Sesion,
    SolicitudRecuperacion,
)
from app.schemas.comunes import RespuestaSimple
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


# --------------------------------------------------------------------------
# Recuperación de contraseña olvidada
#
# Son dos pasos y dos endpoints. El primero comprueba quién pide el cambio y
# emite un permiso temporal; el segundo lo canjea por la contraseña nueva.
# Separarlos es lo que permite que quien haya perdido el acceso demuestre que
# controla el correo de la cuenta antes de tocar nada.
# --------------------------------------------------------------------------


@router.post(
    "/recuperar",
    response_model=AvisoRecuperacion,
    summary="Solicitar la recuperación de la contraseña",
)
def solicitar_recuperacion(
    datos: SolicitudRecuperacion, sesion: SesionDep
) -> AvisoRecuperacion:
    """Primer paso: pedir el enlace para volver a entrar.

    Responde exactamente lo mismo exista o no la cuenta. Si dijera "ese correo
    no está registrado", cualquiera podría ir probando direcciones hasta saber
    cuáles tienen cuenta en el atelier.
    """
    usuario = crud_usuarios.obtener_por_correo(sesion, datos.correo)

    token = None
    if usuario is not None and usuario.estado == "activo":
        token = crear_token_recuperacion(usuario.id, usuario.password_hash)

    aviso = AvisoRecuperacion(
        mensaje=(
            "Si el correo corresponde a una cuenta activa, enviamos las "
            "instrucciones para restablecer la contraseña."
        ),
        expira_en_minutos=configuracion.minutos_expiracion_recuperacion,
    )

    # Fuera de desarrollo el token no sale por la respuesta: iría por correo.
    if configuracion.entorno == "desarrollo":
        aviso.token = token

    return aviso


@router.post(
    "/restablecer",
    response_model=RespuestaSimple,
    summary="Restablecer la contraseña con el token recibido",
)
def restablecer_contrasena(
    datos: RestablecerContrasena, sesion: SesionDep
) -> RespuestaSimple:
    """Segundo paso: canjear el token por una contraseña nueva."""
    try:
        carga = decodificar_token(datos.token)
    except JWTError:
        raise NoAutenticado("El enlace no es válido o ya expiró.")

    if carga.get("tipo") != TIPO_RECUPERACION:
        raise NoAutenticado("Este token no sirve para restablecer la contraseña.")

    identificador = carga.get("sub")
    usuario = (
        crud_usuarios.obtener(sesion, int(identificador))
        if identificador is not None
        else None
    )
    if usuario is None or usuario.estado != "activo":
        raise NoAutenticado("La cuenta no existe o está inactiva.")

    # Uso único: la huella se calculó con el hash que había al pedir el enlace.
    # Si ya se restableció la contraseña, el hash cambió y esto no cuadra.
    if carga.get("huella") != huella_contrasena(usuario.password_hash):
        raise NoAutenticado("Este enlace ya se usó. Solicita uno nuevo.")

    crud_usuarios.cambiar_contrasena(sesion, usuario, datos.password)

    return RespuestaSimple(
        mensaje="Contraseña actualizada. Ya puedes iniciar sesión con ella."
    )
