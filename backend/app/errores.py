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
    """Los datos son válidos, pero el estado del sistema impide la operación. → 409

    `campo` dice CUÁL de los datos enviados provoca el choque, cuando se puede
    señalar uno. No es un adorno: sin él, un formulario recibe «ya existe una
    cuenta con ese correo» y no tiene forma de saber qué casilla marcar, así
    que los deja todos en verde mientras enseña un error. Quien lo rellenó ve
    un aviso y ni un solo campo señalado.

    Va en el nombre que usa el cliente (`numeroDocumento`, no
    `numero_documento`), igual que los detalles de validación.
    """

    codigo = "conflicto_de_negocio"
    campo: str | None = None


class CorreoYaRegistrado(ConflictoDeNegocio):
    codigo = "correo_ya_registrado"
    campo = "correo"

    def __init__(self, correo: str):
        super().__init__(f"Ya existe una cuenta con el correo {correo}.")


class DocumentoYaRegistrado(ConflictoDeNegocio):
    codigo = "documento_ya_registrado"
    campo = "numeroDocumento"

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


class VehiculoNoDisponible(ConflictoDeNegocio):
    codigo = "vehiculo_no_disponible"

    def __init__(self, descripcion: str, estado: str):
        super().__init__(
            f"El vehículo {descripcion} ya no está disponible (estado '{estado}')."
        )


class PrecioBajoConsulta(ConflictoDeNegocio):
    """Pieza sin precio de lista: la cifra la pone un asesor, no el catálogo."""

    codigo = "precio_bajo_consulta"

    def __init__(self, descripcion: str):
        super().__init__(
            f"{descripcion} se vende bajo consulta: agenda una cotización con "
            "un asesor para recibir el precio."
        )


class VentaNoModificable(ConflictoDeNegocio):
    codigo = "venta_no_modificable"

    def __init__(self, estado: str):
        super().__init__(f"Una venta en estado '{estado}' ya no admite cambios.")


class VentaYaFacturada(ConflictoDeNegocio):
    codigo = "venta_ya_facturada"

    def __init__(self, numero: str):
        super().__init__(f"La venta {numero} ya tiene factura emitida.")


class VentaConFactura(ConflictoDeNegocio):
    """Se intentó borrar una venta que ya tiene factura."""

    codigo = "venta_con_factura"

    def __init__(self, numero: str, factura: str):
        super().__init__(
            f"La venta {numero} ya tiene la factura {factura} y no puede "
            "eliminarse. Anúlala en su lugar para conservar el histórico."
        )


class VentaNoFacturable(ConflictoDeNegocio):
    codigo = "venta_no_facturable"

    def __init__(self, estado: str):
        super().__init__(f"No se factura una venta en estado '{estado}'.")


class PqrNoModificable(ConflictoDeNegocio):
    codigo = "pqr_no_modificable"

    def __init__(self, estado: str):
        super().__init__(f"Una PQR en estado '{estado}' ya está cerrada.")


class DemasiadasPeticiones(ErrorDeDominio):
    """Se superó el cupo de peticiones por minuto. → 429

    No es un conflicto de datos ni un fallo del servidor: la petición está
    bien y volverá a funcionar sola. Por eso lleva su propio código y su
    propia espera, que viaja en la cabecera `Retry-After`.
    """

    codigo = "demasiadas_peticiones"

    def __init__(self, espera: int):
        self.espera = espera
        super().__init__(
            f"Vas muy rápido. Espera {espera} segundos y vuelve a escribir."
        )


class ServicioExternoCaido(ErrorDeDominio):
    """Un proveedor de fuera no respondió o respondió mal. → 503

    Se distingue de un fallo propio a conciencia: quien llama necesita saber
    que el problema está afuera y que reintentar puede servir.
    """

    codigo = "servicio_externo_caido"

    def __init__(self, servicio: str, motivo: str = ""):
        self.servicio = servicio
        detalle = f" ({motivo})" if motivo else ""
        super().__init__(
            f"El servicio de {servicio} no está respondiendo{detalle}. "
            "Inténtalo de nuevo en unos minutos."
        )

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
