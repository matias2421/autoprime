"""Cómo meter texto de otros dentro de un documento sin que muerda.

Los reportes y las facturas llevan texto que escribió gente: el nombre con
el que alguien se registró, la descripción de un vehículo, el asunto de una
PQR. Un ORM protege la base de datos de ese texto, pero no protege al
documento: un PDF y una hoja de cálculo son dos lenguajes más, cada uno con
su forma de confundir datos con instrucciones.

Las dos que afectan a este proyecto, comprobadas contra los generadores
reales antes de escribir esto:

**Excel ejecuta lo que empieza por `=`, `+`, `-` o `@`.** No es una
exageración: `=cmd|' /c calc'!A1` en una celda es la carga clásica de DDE, y
al abrir el archivo Excel ofrece ejecutarla. Peor aún, xlsxwriter no la
guardaba como texto sino que la convertía en una fórmula viva —`<f>cmd|'
/c calc'!A1</f>` dentro del XML—, así que el reporte salía del servidor ya
armado. Y el nombre del cliente aparece en ese reporte, y el nombre lo elige
el cliente al registrarse: bastaba con llamarse así para atacar a quien
abriera el reporte de ventas.

**reportlab interpreta un dialecto de marcado dentro de `Paragraph`.** Un
`<b>` sin cerrar en una descripción no se pinta como texto: levanta un
`ValueError` y tumba la generación entera. Una descripción de vehículo con
una etiqueta abierta dejaba esa factura sin poder descargarse nunca, y el
reporte de ventas —que lista nombres de cliente— sin poder generarse para
todo el negocio.

Ninguna de las dos se arregla validando la entrada: el texto es legítimo,
la gente puede llamarse `O'Brien` y una descripción puede decir `< 500 hp`.
Lo que hay que hacer es escaparlo al SALIR, en el idioma de cada formato,
que es justo lo que hay aquí.
"""

from xml.sax.saxutils import escape

# Los cuatro caracteres con los que Excel empieza a interpretar, más el
# tabulador y el retorno de carro, que sirven para colarse en la celda de al
# lado cuando el archivo se pega en una hoja.
ARRANQUES_PELIGROSOS = ("=", "+", "-", "@", "\t", "\r")


def texto_para_excel(valor) -> str:
    """Neutraliza una celda para que Excel la lea como texto y no como orden.

    El apóstrofo delante es la marca que Excel entiende como «esto es texto
    literal»: no se ve en la celda, no se copia al pegar el valor, y desarma
    la fórmula. Es la contramedida estándar y la única que cubre también
    `+`, `-` y `@`, que no se arreglan guardando el valor como cadena
    porque Excel los reinterpreta igualmente al abrir el archivo.

    Un número negativo escrito como número no pasa por aquí y sigue siendo
    negativo: esto es solo para el texto.
    """
    texto = "" if valor is None else str(valor)
    if texto.startswith(ARRANQUES_PELIGROSOS):
        return "'" + texto
    return texto


def texto_para_pdf(valor) -> str:
    """Escapa el texto para que reportlab lo pinte en vez de interpretarlo.

    Se escapan `&`, `<` y `>`. El orden importa y lo garantiza `escape`, que
    hace primero el `&`: al revés, un `<` convertido en `&lt;` volvería a
    escaparse y saldría `&amp;lt;` en el documento.

    Lo que este módulo escapa es el texto AJENO. El marcado propio —el
    `<b>` de un rótulo, el `<br/>` que separa las líneas de una dirección—
    se compone después, alrededor de lo ya escapado; por eso la función
    devuelve texto listo para insertar y no toca nada más.
    """
    return escape("" if valor is None else str(valor))


def recortar(valor, maximo: int) -> str:
    """Corta lo que no cabe, avisando con puntos suspensivos.

    Una descripción de mil caracteres en una celda de tabla no se lee: rompe
    la maqueta del PDF y empuja el resto de la fila fuera de la página. Vale
    más decir menos que romper la página entera.
    """
    texto = "" if valor is None else str(valor)
    if len(texto) <= maximo:
        return texto
    return texto[: maximo - 1].rstrip() + "…"
