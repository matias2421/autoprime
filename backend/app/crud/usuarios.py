"""Acceso a datos de usuarios y roles."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.seguridad import hashear_contrasena
from app.errores import (
    CorreoYaRegistrado,
    DocumentoYaRegistrado,
    RecursoNoEncontrado,
)
from app.models.autoprime import Rol, Usuario


def obtener_rol_por_nombre(sesion: Session, nombre: str) -> Rol:
    rol = sesion.scalar(select(Rol).where(Rol.nombre == nombre))
    if rol is None:
        raise RecursoNoEncontrado("un rol", nombre)
    return rol


def obtener_por_correo(sesion: Session, correo: str) -> Usuario | None:
    """Busca sin distinguir mayúsculas: los correos se guardan en minúscula."""
    return sesion.scalar(
        select(Usuario).where(func.lower(Usuario.correo) == correo.lower())
    )


def obtener(sesion: Session, usuario_id: int) -> Usuario | None:
    return sesion.get(Usuario, usuario_id)


def obtener_o_fallar(sesion: Session, usuario_id: int) -> Usuario:
    usuario = obtener(sesion, usuario_id)
    if usuario is None:
        raise RecursoNoEncontrado("un usuario", usuario_id)
    return usuario


def listar(
    sesion: Session,
    rol: str | None = None,
    estado: str | None = None,
    buscar: str | None = None,
) -> list[Usuario]:
    consulta = select(Usuario).join(Rol)

    if rol:
        consulta = consulta.where(Rol.nombre == rol)
    if estado:
        consulta = consulta.where(Usuario.estado == estado)
    if buscar:
        patron = f"%{buscar}%"
        consulta = consulta.where(
            Usuario.nombre.like(patron)
            | Usuario.apellido.like(patron)
            | Usuario.correo.like(patron)
            | Usuario.numero_documento.like(patron)
        )

    return list(sesion.scalars(consulta.order_by(Usuario.id)).unique())


def _comprobar_duplicados(
    sesion: Session,
    correo: str,
    tipo_documento: str,
    numero_documento: str,
    excluir_id: int | None = None,
) -> None:
    """Evita correos y documentos repetidos antes de tocar la base.

    La base ya tiene índices únicos, pero al comprobarlo aquí el cliente
    recibe un 409 con un mensaje útil en lugar de un error de integridad.
    """
    consulta = select(Usuario).where(func.lower(Usuario.correo) == correo.lower())
    if excluir_id:
        consulta = consulta.where(Usuario.id != excluir_id)
    if sesion.scalar(consulta):
        raise CorreoYaRegistrado(correo)

    consulta = select(Usuario).where(
        Usuario.tipo_documento == tipo_documento,
        Usuario.numero_documento == numero_documento,
    )
    if excluir_id:
        consulta = consulta.where(Usuario.id != excluir_id)
    if sesion.scalar(consulta):
        raise DocumentoYaRegistrado(tipo_documento, numero_documento)


def crear(sesion: Session, datos: dict, rol_nombre: str = "cliente") -> Usuario:
    """Da de alta un usuario. La contraseña se hashea aquí, nunca antes."""
    _comprobar_duplicados(
        sesion, datos["correo"], datos["tipo_documento"], datos["numero_documento"]
    )

    rol = obtener_rol_por_nombre(sesion, rol_nombre)
    contrasena = datos.pop("password")
    limpios = {k: v for k, v in datos.items() if k != "confirmar_password"}

    usuario = Usuario(
        **limpios,
        password_hash=hashear_contrasena(contrasena),
        rol_id=rol.id,
    )
    usuario.correo = usuario.correo.lower()

    sesion.add(usuario)
    sesion.commit()
    sesion.refresh(usuario)
    return usuario


def actualizar(sesion: Session, usuario: Usuario, cambios: dict) -> Usuario:
    rol_nombre = cambios.pop("rol", None)

    correo = cambios.get("correo", usuario.correo)
    tipo = cambios.get("tipo_documento", usuario.tipo_documento)
    numero = cambios.get("numero_documento", usuario.numero_documento)
    _comprobar_duplicados(sesion, correo, tipo, numero, excluir_id=usuario.id)

    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)
    if "correo" in cambios:
        usuario.correo = usuario.correo.lower()

    if rol_nombre:
        usuario.rol_id = obtener_rol_por_nombre(sesion, rol_nombre).id

    sesion.commit()
    sesion.refresh(usuario)
    return usuario


def cambiar_contrasena(sesion: Session, usuario: Usuario, nueva: str) -> Usuario:
    """Reemplaza el hash por el de la contraseña nueva.

    Al cambiar el hash quedan invalidados de paso todos los enlaces de
    recuperación emitidos antes, porque su huella se calculó con el hash
    anterior y ya no coincidirá.
    """
    usuario.password_hash = hashear_contrasena(nueva)
    sesion.commit()
    sesion.refresh(usuario)
    return usuario


def cambiar_estado(sesion: Session, usuario: Usuario, estado: str) -> Usuario:
    usuario.estado = estado
    sesion.commit()
    sesion.refresh(usuario)
    return usuario


def eliminar(sesion: Session, usuario: Usuario) -> None:
    sesion.delete(usuario)
    sesion.commit()
