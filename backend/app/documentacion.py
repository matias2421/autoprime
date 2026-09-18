"""Respuestas de error documentadas, para que `/docs` diga la verdad entera.

Por defecto, FastAPI documenta de cada endpoint el 200 y poco más. Quien abre
la documentación ve entonces la mitad del contrato: qué devuelve cuando todo
va bien, y ningún indicio de que además puede responder 401, 403, 404 o 409
—ni con qué forma—. Eso obliga a descubrir los errores probando, que es la
manera cara de descubrirlos.

Aquí se declaran una sola vez y cada router compone las que le tocan:

    responses=respuestas(NO_ENCONTRADO, CONFLICTO)

El ejemplo de cada una es un cuerpo real de la API, no una plantilla: es el
mismo `{codigo, mensaje, ruta, detalles}` que arma `main.py`.
"""

from app.schemas.comunes import RespuestaError


def _error(descripcion: str, codigo: str, mensaje: str, ruta: str = "/api/ventas"):
    return {
        "model": RespuestaError,
        "description": descripcion,
        "content": {
            "application/json": {
                "example": {
                    "codigo": codigo,
                    "mensaje": mensaje,
                    "ruta": ruta,
                    "detalles": None,
                }
            }
        },
    }


NO_AUTENTICADO = {
    401: _error(
        "Falta el token o ya expiró",
        "no_autenticado",
        "El token no es válido o ya expiró.",
    )
}

SIN_PERMISO = {
    403: _error(
        "La cuenta existe pero no tiene el rol necesario",
        "permiso_denegado",
        "Esta operación está reservada al rol administrador.",
    )
}

NO_ENCONTRADO = {
    404: _error(
        "No existe un recurso con ese identificador",
        "recurso_no_encontrado",
        "No existe una venta con identificador 4321.",
    )
}

CONFLICTO = {
    409: _error(
        "Los datos son válidos, pero el estado del sistema lo impide",
        "vehiculo_no_disponible",
        "El vehículo Rolls-Royce Phantom VIII ya no está disponible "
        "(estado 'vendido').",
    )
}

NO_VALIDO = {
    422: {
        "model": RespuestaError,
        "description": "El cuerpo no cumple el formato esperado",
        "content": {
            "application/json": {
                "example": {
                    "codigo": "datos_invalidos",
                    "mensaje": "Los datos enviados no cumplen el formato esperado.",
                    "ruta": "/api/ventas",
                    "detalles": [
                        {
                            "campo": "lineas",
                            "problema": "List should have at least 1 item after "
                            "validation, not 0",
                        }
                    ],
                }
            }
        },
    }
}

SERVICIO_CAIDO = {
    503: _error(
        "Un proveedor externo no respondió",
        "servicio_externo_caido",
        "El servicio de asistente no está respondiendo. Inténtalo de nuevo "
        "en unos minutos.",
        "/api/chat/mensajes",
    )
}

# Casi todo endpoint autenticado puede responder estas dos.
PROTEGIDO = {**NO_AUTENTICADO, **SIN_PERMISO}


def respuestas(*bloques: dict) -> dict:
    """Une varios bloques en el `responses` de un endpoint."""
    unidas: dict = {}
    for bloque in bloques:
        unidas.update(bloque)
    return unidas
