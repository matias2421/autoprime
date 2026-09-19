"""Autenticación: registro, login y perfil."""

from fastapi import APIRouter, BackgroundTasks, Request, status

from app.core import limitador
from app.core.configuracion import configuracion
from app.core.correo import enviar_enlace_recuperacion
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
from app.errores import DemasiadasPeticiones, NoAutenticado
from app.schemas.auth import (
    AvisoRecuperacion,
    Credenciales,
    RestablecerContrasena,
    Sesion,
    SolicitudRecuperacion,
)
from app.schemas.comunes import RespuestaSimple
from app.schemas.sobres import SobreUsuario
from app.schemas.usuario import UsuarioRegistro, UsuarioSalida

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

# Intentos de entrar por minuto antes de frenar.
#
# Ocho deja pasar a quien se equivoca un par de veces y no se acuerda de si
# la clave lleva mayuscula; corta en seco a quien prueba un diccionario. Sin
# freno, el login admite miles de intentos por minuto y una clave corta cae
# en una tarde, por muy bien cifrada que este en la base: bcrypt protege el
# hash si alguien roba la tabla, no protege de que le pregunten al servidor
# una y otra vez.
INTENTOS_POR_MINUTO = 8

# Mas margen aqui: es la unica manera de recuperar una cuenta y frenarla de
# mas convierte un olvido en un problema. Pero con freno igualmente, porque
# cada solicitud manda un correo de verdad.
RECUPERACIONES_POR_MINUTO = 4


def _origen(peticion: Request) -> str:
    """De donde viene, contando con el balanceador de Render."""
    reenviado = peticion.headers.get("x-forwarded-for")
    if reenviado:
        return reenviado.split(",")[0].strip()
    return peticion.client.host if peticion.client else "desconocido"


def _frenar(peticion: Request, llave: str, cupo: int) -> None:
    permitido, espera = limitador.permitido(llave, cupo)
    if not permitido:
        raise DemasiadasPeticiones(espera)


@router.post(
    "/registro",
    response_model=Sesion,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un cliente",
)
async def registrar(datos: UsuarioRegistro, sesion: SesionDep) -> Sesion:
    """Alta pública. Siempre con rol de cliente y contraseña hasheada.

    Devuelve ya la sesión iniciada: quien acaba de registrarse entra sin
    tener que escribir de nuevo sus credenciales, que es como se comportaba
    el formulario desde el segundo avance.
    """
    usuario = await crud_usuarios.crear(sesion, datos.model_dump(), rol_nombre="cliente")

    return Sesion(
        token=crear_token(usuario.id, usuario.correo, usuario.rol.nombre),
        expira_en_horas=configuracion.horas_expiracion_token,
        usuario=UsuarioSalida.desde_modelo(usuario),
    )


@router.post("/login", response_model=Sesion, summary="Iniciar sesión")
async def iniciar_sesion(
    credenciales: Credenciales, peticion: Request, sesion: SesionDep
) -> Sesion:
    """Verifica las credenciales y emite un JWT.

    Se cuenta por ORIGEN y ademas por CORREO, y hacen falta las dos.

    Solo por origen, quien reparte los intentos entre varias direcciones
    sigue probando contra la misma cuenta. Solo por correo, basta con ir
    cambiando el correo de la peticion para no gastar nunca el cupo, que es
    justo lo que hace quien prueba una clave comun contra muchas cuentas.
    """
    _frenar(peticion, f"login:{_origen(peticion)}", INTENTOS_POR_MINUTO)
    _frenar(peticion, f"login:correo:{credenciales.correo.lower()}",
            INTENTOS_POR_MINUTO)

    usuario = await crud_usuarios.obtener_por_correo(sesion, credenciales.correo)

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


@router.get("/perfil", response_model=SobreUsuario, summary="Perfil propio")
async def perfil(usuario: UsuarioActual) -> SobreUsuario:
    """Devuelve el usuario del token. Sirve para revalidar la sesión.

    Va dentro del sobre `{usuario: ...}` como el resto de la API, y no suelto:
    el frontend reconstruye la sesión al recargar leyendo `datos.usuario`, así
    que devolverlo pelado dejaba fuera a quien pulsara F5 estando dentro.
    """
    return SobreUsuario(usuario=UsuarioSalida.desde_modelo(usuario))


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
async def solicitar_recuperacion(
    datos: SolicitudRecuperacion,
    peticion: Request,
    sesion: SesionDep,
    tareas: BackgroundTasks,
) -> AvisoRecuperacion:
    """Primer paso: pedir por correo el enlace para volver a entrar.

    El token no vuelve en la respuesta: viaja por correo y solo por correo. Es
    la parte que hace que el flujo signifique algo, porque obliga a demostrar
    que se controla el buzón de la cuenta. Devolverlo aquí convertiría "olvidé
    mi contraseña" en "cámbiale la contraseña a quien yo diga".

    Responde exactamente lo mismo exista o no la cuenta. Si dijera "ese correo
    no está registrado", cualquiera podría ir probando direcciones hasta saber
    cuáles tienen cuenta en el atelier.

    El envío se encola como tarea de fondo: hablar con el servidor de correo
    puede tardar segundos y quien rellenó el formulario no tiene por qué
    esperarlos.
    """

    # Cada solicitud manda un correo de verdad. Sin freno, esto es un
    # generador de correo basura con el remitente del atelier: se pide mil
    # veces la recuperacion de una cuenta ajena y el buzon de esa persona
    # se llena de enlaces que no pidio.
    _frenar(peticion, f"recuperar:{_origen(peticion)}",
            RECUPERACIONES_POR_MINUTO)
    _frenar(peticion, f"recuperar:correo:{datos.correo.lower()}",
            RECUPERACIONES_POR_MINUTO)
    usuario = await crud_usuarios.obtener_por_correo(sesion, datos.correo)

    if usuario is not None and usuario.estado == "activo":
        tareas.add_task(
            enviar_enlace_recuperacion,
            usuario.correo,
            usuario.nombre,
            crear_token_recuperacion(usuario.id, usuario.password_hash),
        )

    return AvisoRecuperacion(
        mensaje=(
            "Si el correo corresponde a una cuenta activa, enviamos las "
            "instrucciones para restablecer la contraseña."
        ),
        expira_en_minutos=configuracion.minutos_expiracion_recuperacion,
    )


@router.post(
    "/restablecer",
    response_model=RespuestaSimple,
    summary="Restablecer la contraseña con el token recibido",
)
async def restablecer_contrasena(
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
        await crud_usuarios.obtener(sesion, int(identificador))
        if identificador is not None
        else None
    )
    if usuario is None or usuario.estado != "activo":
        raise NoAutenticado("La cuenta no existe o está inactiva.")

    # Uso único: la huella se calculó con el hash que había al pedir el enlace.
    # Si ya se restableció la contraseña, el hash cambió y esto no cuadra.
    if carga.get("huella") != huella_contrasena(usuario.password_hash):
        raise NoAutenticado("Este enlace ya se usó. Solicita uno nuevo.")

    await crud_usuarios.cambiar_contrasena(sesion, usuario, datos.password)

    return RespuestaSimple(
        mensaje="Contraseña actualizada. Ya puedes iniciar sesión con ella."
    )
