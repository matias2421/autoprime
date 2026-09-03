"""Excepciones del dominio.

No conocen HTTP: solo describen qué salió mal. La traducción a códigos de
estado ocurre en los manejadores registrados en `main.py`, de modo que la
lógica de negocio no tiene que importar nada de FastAPI.
"""


class ErrorDeDominio(Exception):
    """Raíz de todas las excepciones de negocio de AutoPrime."""

    codigo = "error_de_dominio"

    def __init__(self, mensaje: str):
        self.mensaje = mensaje
        super().__init__(mensaje)


class RecursoNoEncontrado(ErrorDeDominio):
    """El identificador solicitado no corresponde a ningún recurso. → 404"""

    codigo = "recurso_no_encontrado"

    def __init__(self, recurso: str, identificador: int | str):
        self.recurso = recurso
        self.identificador = identificador
        super().__init__(f"No existe {recurso} con identificador {identificador}.")


class ConflictoDeNegocio(ErrorDeDominio):
    """Los datos son válidos, pero el estado del sistema impide la operación. → 409"""

    codigo = "conflicto_de_negocio"


class CorreoYaRegistrado(ConflictoDeNegocio):
    codigo = "correo_ya_registrado"

    def __init__(self, correo: str):
        super().__init__(f"Ya existe una cuenta con el correo {correo}.")


class DocumentoYaRegistrado(ConflictoDeNegocio):
    codigo = "documento_ya_registrado"

    def __init__(self, tipo: str, numero: str):
        super().__init__(f"Ya existe una cuenta con el documento {tipo} {numero}.")


class SlugYaRegistrado(ConflictoDeNegocio):
    codigo = "slug_ya_registrado"

    def __init__(self, slug: str):
        super().__init__(f"Ya existe un vehículo con el identificador '{slug}'.")


class FranjaOcupada(ConflictoDeNegocio):
    codigo = "franja_ocupada"

    def __init__(self, fecha: str, hora: str):
        super().__init__(
            f"La franja del {fecha} a las {hora} ya está tomada para ese vehículo."
        )


class CitaNoModificable(ConflictoDeNegocio):
    codigo = "cita_no_modificable"

    def __init__(self, estado: str):
        super().__init__(f"Una cita en estado '{estado}' ya no admite cambios.")


# --- Autenticación y autorización ---
class NoAutenticado(ErrorDeDominio):
    """No se pudo establecer la identidad del solicitante. → 401"""

    codigo = "no_autenticado"

    def __init__(self, mensaje: str = "Credenciales ausentes o inválidas."):
        super().__init__(mensaje)


class PermisoDenegado(ErrorDeDominio):
    """La identidad es conocida, pero no tiene permiso. → 403"""

    codigo = "permiso_denegado"

    def __init__(self, mensaje: str = "No tiene permiso para esta operación."):
        super().__init__(mensaje)


class DatosInvalidos(ErrorDeDominio):
    """Regla de negocio que Pydantic no puede cubrir por sí solo. → 422"""

    codigo = "datos_invalidos"
