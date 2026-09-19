"""Convierte un importe en su lectura en letras.

Una factura colombiana lleva el total escrito también con palabras. No es
formalismo: es una comprobación cruzada. Un cero de más en «$32.000.000» no
salta a la vista; en «TREINTA Y DOS MILLONES DE PESOS» sí, porque las dos
cifras tienen que decir lo mismo y quien lee compara sin darse cuenta.

Las reglas del español que hay que respetar y son fáciles de romper:

  - «uno» se apocopa a «un» delante de un sustantivo: un peso, veintiún mil,
    doscientos un millones. Nunca «uno peso».
  - de dieciséis a veintinueve se escribe junto; de treinta y uno en
    adelante, separado con «y».
  - «ciento» pierde la sílaba cuando va solo: cien, no ciento.
  - el millón se pluraliza y pide «de» cuando la cifra es redonda: dos
    millones DE pesos, pero dos millones quinientos mil pesos.

La primera versión de este archivo se rompía con 1.200.000.000 —los
millones también tienen miles, y el catálogo de AutoPrime está justo en esa
escala— y escribía «UNO PESOS». Las dos cosas las encontró la tabla de
casos de `tests/test_letras.py`, que por eso existe.
"""

from decimal import Decimal

UNIDADES = (
    "", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
    "nueve", "diez", "once", "doce", "trece", "catorce", "quince",
    "dieciséis", "diecisiete", "dieciocho", "diecinueve", "veinte",
    "veintiuno", "veintidós", "veintitrés", "veinticuatro", "veinticinco",
    "veintiséis", "veintisiete", "veintiocho", "veintinueve",
)

DECENAS = (
    "", "", "", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta",
    "ochenta", "noventa",
)

CENTENAS = (
    "", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos",
    "seiscientos", "setecientos", "ochocientos", "novecientos",
)


def _apocopar(texto: str) -> str:
    """«uno» → «un» cuando le sigue un sustantivo.

    Solo al final: «veintiuno mil» es incorrecto y «veintiún mil» es lo
    correcto, pero dentro de «uno» no hay nada que tocar si el número
    termina ahí. Por eso se mira el final de la cadena y no se reemplaza en
    cualquier posición, que era el error de la primera versión.
    """
    if texto.endswith("veintiuno"):
        return texto[: -len("veintiuno")] + "veintiún"
    if texto.endswith("uno"):
        return texto[:-3] + "un"
    return texto


def _hasta_999(numero: int) -> str:
    if numero == 0:
        return ""
    if numero == 100:
        return "cien"

    centena, resto = divmod(numero, 100)
    texto = CENTENAS[centena]

    if resto:
        if resto < 30:
            parte = UNIDADES[resto]
        else:
            decena, unidad = divmod(resto, 10)
            parte = DECENAS[decena]
            if unidad:
                parte += f" y {UNIDADES[unidad]}"
        texto = f"{texto} {parte}".strip()

    return texto


def _hasta_999_999(numero: int) -> str:
    """Un bloque completo de seis cifras: sus miles y sus unidades.

    Se usa dos veces —para el bloque de los millones y para el de las
    unidades—, que es lo que permite decir «mil doscientos millones». La
    primera versión spelleaba los millones con `_hasta_999` y por eso se
    rompía en cuanto la cifra pasaba de mil millones.
    """
    if numero == 0:
        return ""

    miles, unidades = divmod(numero, 1_000)
    partes = []

    if miles == 1:
        partes.append("mil")
    elif miles:
        partes.append(f"{_apocopar(_hasta_999(miles))} mil")

    if unidades:
        partes.append(_hasta_999(unidades))

    return " ".join(partes)


def en_letras(valor) -> str:
    """El importe en palabras, en mayúsculas y listo para la factura.

    Se ignoran los centavos a propósito: el peso colombiano no los usa en la
    práctica y «CON CERO CENTAVOS» en cada factura es ruido. Si algún día
    hicieran falta, esta es la función que habría que ampliar, y queda dicho
    aquí para que se encuentre.
    """
    entero = int(Decimal(str(valor or 0)))
    signo = "MENOS " if entero < 0 else ""
    entero = abs(entero)

    if entero == 0:
        return "CERO PESOS M/CTE"

    millones, resto = divmod(entero, 1_000_000)

    partes = []
    if millones == 1:
        partes.append("un millón")
    elif millones:
        partes.append(f"{_apocopar(_hasta_999_999(millones))} millones")

    if resto:
        partes.append(_hasta_999_999(resto))

    texto = " ".join(p for p in partes if p)

    # Singular y plural del sustantivo, y el «de» que pide un millón redondo.
    if entero == 1:
        moneda = "peso"
    elif millones and not resto:
        moneda = "de pesos"
    else:
        moneda = "pesos"

    # M/CTE: moneda corriente. Es lo que se escribe en las facturas del país.
    return f"{signo}{_apocopar(texto)} {moneda} M/CTE".upper()
