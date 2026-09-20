# -*- coding: utf-8 -*-
"""Monta el documento de evidencias del quinto avance, y lo imprime a PDF.

    backend/venv/Scripts/python herramientas/documento_quinta.py

No hace falta que la aplicación esté en marcha: las capturas ya existen.

POR QUÉ ESTE NO USA UNA PLANTILLA A MANO
----------------------------------------
El del cuarto avance eran dos piezas: un `verificacion.html` escrito a mano y
un guion que le metía las capturas dentro. Funcionó, pero obligaba a tocar dos
archivos para cambiar una frase y dejaba que el documento y las imágenes se
desincronizaran sin que nada avisara.

Aquí el documento se genera entero desde esta lista. Si una captura falta, el
documento lo dice en su sitio en vez de enseñar un hueco: una evidencia que no
está es información, y esconderla sería justo lo contrario de para lo que
existe esto.

CÓMO SE NUMERA
--------------
Las secciones van por lo que demuestran, no por el número del requisito del
instrumento del instructor. Es a propósito: el instrumento del quinto avance
no está en el repositorio, y poner números inventados al lado de cada
evidencia sería peor que no poner ninguno. Cuando llegue el documento, cada
bloque ya lleva su título y basta con anteponerle el número que le toque.
"""

import base64
import datetime
import html
import io as _io
import os
import sys
import time

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capturas import Navegador  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURAS = os.path.join(RAIZ, "evidencias", "capturas-quinta")
DESTINO_HTML = os.path.join(RAIZ, "evidencias", "verificacion-quinta.html")
DESTINO_PDF = os.path.join(
    RAIZ, "evidencias", "Evidencias_Quinto_Avance_AutoPrime.pdf")

ANCHO_MAXIMO = 1120        # px a los que se reduce cada captura
ANCHO_A4, ALTO_A4 = 8.27, 11.69

AUTOR = "José Matías Agudelo Bolívar"
FICHA = "Ficha 3406211 · Análisis y Desarrollo de Software"


# ---------------------------------------------------------------------------
# El documento, sección a sección.
#
# Cada entrada: (archivo, título, qué demuestra, pie de la captura)
# ---------------------------------------------------------------------------
SECCIONES = [
    ("Gestión comercial", """
     El registro de una venta y su recorrido: se crea con sus líneas, se le
     calcula el IVA en el servidor —nunca en el navegador— y va cambiando de
     estado hasta que se cobra o se anula.""", [

        ("q04-ventas-listado", "El listado de ventas",
         "Tabla con filtros por estado y fecha, buscador y paginación. Cada "
         "fila lleva su número, el comprador, el total y en qué estado está.",
         "35 ventas en la base: 24 pagadas, 7 pendientes y 4 anuladas. La "
         "paginación pide solo la página que se está viendo."),

        ("q05-ventas-nueva", "Registrar una venta",
         "El alta, con el buscador de cliente y las líneas. Los importes los "
         "calcula la API: el navegador los enseña, no los decide.",
         "Se añaden líneas del catálogo y el subtotal, el IVA y el total "
         "salen del servidor."),
    ]),

    ("Facturación", """
     De una venta sale una factura, y de la factura sale un PDF que se puede
     imprimir y entregar. Con numeración propia, desglose de IVA y el importe
     en letras, que es lo que pide una factura de verdad.""", [

        ("q06-facturas-listado", "Facturas emitidas",
         "El listado, con su número, la venta de la que salen y su estado.",
         "19 facturas emitidas. Una factura anulada no desaparece: se marca, "
         "porque un documento fiscal no se borra."),

        ("q07-factura-pdf", "La factura en PDF",
         "Generada por la API con reportlab. Lleva la banda de estado, el "
         "bloque fiscal con NIT y régimen, el desglose del IVA, el importe en "
         "letras y un código de verificación.",
         "«SON: CINCO MIL SETECIENTOS DOCE MILLONES DE PESOS M/CTE» lo "
         "escribe un conversor propio, con sus propias pruebas: los números "
         "en letras tienen más casos raros de los que parece."),
    ]),

    ("Informes en PDF y en Excel", """
     El mismo informe, en los dos formatos que hacen falta: uno para imprimir
     y otro para seguir trabajando encima.""", [

        ("q08-reporte-pdf", "Reporte de ventas en PDF",
         "Cinco páginas: cifras del periodo, gráfica de ingresos por día, lo "
         "que más se vendió y el detalle venta a venta. Con «Página X de Y» "
         "en el pie, que obliga a componer el documento dos veces porque la "
         "primera aún no se sabe cuántas páginas va a haber.",
         "35 ventas y $67.831.249.500 en el trimestre."),

        ("q21-excel-seguro", "Qué lleva dentro el Excel",
         "Cuatro hojas, dos gráficas incrustadas y fórmulas SUBTOTAL que "
         "respetan el filtro. Y, sobre todo, ni una celda donde el texto de "
         "un cliente se haya convertido en fórmula.",
         "Comprobado abriendo el .xlsx y mirando sus fórmulas una por una."),
    ]),

    ("El tablero, con gráficas", """
     El resumen que abre el administrador. No son cifras sueltas: cada una se
     compara con el periodo anterior, que es lo que convierte un número en
     una noticia.""", [

        ("q01-tablero-ingresos", "Cifras del periodo e ingresos por día",
         "Ventas, ingresos, ticket promedio y lo que queda por cobrar, cada "
         "uno con su variación. Debajo, la serie diaria y el desglose por "
         "estado.",
         "7 ventas (+16,7 %) e ingresos de $11,9 mil M (+212,5 %) en siete "
         "días. La gráfica solo cuenta lo cobrado: una venta anulada no "
         "ingresó nada."),

        ("q02-tablero-ranking", "Lo que más se vende",
         "Vehículos y servicios ordenados por lo que han dejado.",
         "Sale del mismo cálculo que alimenta el informe: una sola fuente "
         "para los dos sitios."),

        ("q03-tablero-90-dias", "El mismo tablero, a noventa días",
         "El periodo se cambia y todo se recalcula: las cifras, las "
         "variaciones y las dos gráficas.",
         "Cambiar el periodo pide de nuevo los datos; no se filtran en el "
         "navegador sobre lo que ya había."),
    ]),

    ("PQR", """
     Peticiones, quejas y reclamos: el canal por el que un cliente reclama y
     alguien del atelier responde, con el estado a la vista de los dos.""", [

        ("q10-pqr-listado", "Las solicitudes radicadas",
         "Con su número de radicado, tipo, estado y fecha.",
         "10 solicitudes, 5 abiertas. Cada una nace pendiente y con un "
         "radicado con formato propio."),

        ("q11-pqr-responder", "Responder una PQR",
         "La respuesta y el estado en que queda se eligen a la vez: "
         "responder sin decir si el asunto se cierra deja el caso a medias.",
         "El cliente ve su solicitud y la respuesta desde su panel."),
    ]),

    ("El asistente con IA", """
     Un chat que contesta sobre el catálogo, los servicios y cómo agendar. No
     inventa: cuando no tiene el dato, dice dónde conseguirlo.""", [

        ("q12-chat-asistente", "El asistente respondiendo",
         "Pregunta real y respuesta real, contra el modelo. La conversación "
         "se guarda, así que se puede retomar.",
         "A «¿Qué vehículos tienen disponibles?» responde con los ocho "
         "modelos del catálogo y sus años: los ha leído de la base, no se los "
         "ha inventado."),
    ]),

    ("Lo que ve cada rol", """
     Tres roles y tres vistas distintas. Y la parte que importa: lo que
     decide no es la interfaz, es el servidor.""", [

        ("q13-panel-empleado", "El panel del empleado",
         "Ve las ventas y puede registrarlas, pero no toca usuarios ni "
         "informes del negocio.",
         "El menú lateral enseña solo lo que su rol permite."),

        ("q14-panel-cliente", "El panel del cliente",
         "Sus compras, sus citas y sus PQR. Nada de otros clientes.",
         "El filtro por dueño lo aplica la API: aunque alguien pidiera la "
         "lista entera a mano, recibiría solo lo suyo."),

        ("q15-cliente-sus-compras", "Un cliente en la pantalla de ventas",
         "La misma ruta que usa el administrador, con un cliente dentro.",
         "No se le enseña «Gestión comercial» sino «Mis compras», y la "
         "consulta sale acotada a su identificador."),
    ]),

    ("La API y sus pruebas", """
     Lo que sostiene todo lo anterior, y cómo se comprueba que sigue en pie.""", [

        ("q16-swagger-quinta", "La documentación de la API",
         "Publicada por la propia aplicación en /docs. Las rutas del quinto "
         "avance —ventas, facturas, informes, PQR y chat— con sus esquemas.",
         "De aquí se genera la colección de Postman, así que la batería no "
         "puede quedarse atrás cuando se añade una ruta."),

        ("q17-pruebas-pytest", "Las pruebas automáticas",
         "172 pruebas sobre la lógica: ventas, facturas, informes, PQR, chat, "
         "números en letras, documentos seguros y endurecimiento.",
         "Se ejecutan de verdad para hacer esta imagen. Si una fallara, la "
         "evidencia lo enseñaría."),

        ("q18-postman-newman", "La colección de Postman, ejecutada",
         "La misma que se entrega, corrida desde la línea de órdenes.",
         "69 peticiones y 62 comprobaciones, 0 fallidas."),
    ]),

    ("Seguridad", """
     Lo que cierra las puertas de fuera. Tres cosas distintas y las tres
     comprobables, que es lo que las separa de una promesa.""", [

        ("q19-inyeccion-sql", "Inyección SQL: el texto es texto",
         "Cinco cargas clásicas contra el buscador. Ninguna llega a la "
         "sentencia: el texto viaja siempre como parámetro enlazado.",
         "Un 200 con cero resultados es la respuesta correcta. Después de "
         "mandarlas todas, la tabla sigue con sus 11 usuarios."),

        ("q20-fuerza-bruta", "Probar contraseñas, frenado",
         "bcrypt protege el hash si alguien roba la tabla; no protege de que "
         "le pregunten al servidor mil veces por segundo.",
         "Ocho intentos por minuto, contados por origen Y por correo: así no "
         "se esquiva cambiando de dirección en cada intento."),

        ("q22-cabeceras", "Las cabeceras, en el servidor de verdad",
         "Leídas del despliegue, que es donde importan: nosniff, DENY, "
         "no-referrer, no-store, una política de contenido que no deja cargar "
         "nada, y HSTS.",
         "El enlace con la base va cifrado y con el certificado verificado."),
    ]),

    ("Desplegado y funcionando", """
     El proyecto no vive solo en un portátil.""", [

        ("q23-despliegue", "El servicio en producción",
         "Dos rutas de estado porque son dos preguntas distintas: /vivo dice "
         "si el proceso responde y es lo que consulta el proveedor; /salud "
         "diagnostica todo, base incluida, y lo lee una persona.",
         "Separarlas no es un adorno: con la comprobación atada a la base, "
         "una caída de la base tumba también los despliegues. Pasó, y costó "
         "uno."),
    ]),
]


# ---------------------------------------------------------------------------
def incrustar(nombre: str):
    """Devuelve la captura reducida y en base64, o None si no está."""
    ruta = os.path.join(CAPTURAS, nombre + ".png")
    if not os.path.isfile(ruta):
        return None
    with Image.open(ruta) as imagen:
        imagen = imagen.convert("RGB")
        if imagen.width > ANCHO_MAXIMO:
            alto = round(imagen.height * ANCHO_MAXIMO / imagen.width)
            imagen = imagen.resize((ANCHO_MAXIMO, alto), Image.LANCZOS)
        buzon = _io.BytesIO()
        imagen.save(buzon, format="JPEG", quality=86, optimize=True)
    return base64.b64encode(buzon.getvalue()).decode()


ESTILOS = """
  :root {
    --negro: #020204; --carbon: #07070b; --grafito: #0d0d13;
    --pizarra: #13131b; --linea: #22222b; --trazo: #3c3c47;
    --hueso: #ffffff; --ceniza: #b6b6b6; --plomo: #8f8f93;
    --accion: #829fb0;
    --display: "Cormorant Garamond", "Times New Roman", serif;
    --sans: "Inter", ui-sans-serif, system-ui, sans-serif;
    --mono: "JetBrains Mono", ui-monospace, Consolas, monospace;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 0 28px 40px;
    background: var(--negro); color: var(--ceniza);
    font-family: var(--sans); font-size: 14px; line-height: 1.62;
  }
  .portada {
    padding: 72px 0 40px; border-bottom: 1px solid var(--linea);
    margin-bottom: 34px;
  }
  .sello {
    font-family: var(--mono); font-size: 11px; letter-spacing: .22em;
    color: var(--accion); text-transform: uppercase;
  }
  .portada h1 {
    font-family: var(--display); font-weight: 400; color: var(--hueso);
    font-size: 3.4rem; line-height: 1.04; margin: 14px 0 6px;
  }
  .portada h2 {
    font-family: var(--display); font-weight: 400; color: var(--plomo);
    font-size: 1.6rem; margin: 0 0 22px;
  }
  .portada dl {
    display: grid; grid-template-columns: max-content 1fr;
    gap: 5px 20px; margin: 0; font-size: .87rem;
  }
  .portada dt { font-family: var(--mono); color: var(--plomo);
                font-size: .76rem; letter-spacing: .08em;
                text-transform: uppercase; }
  .portada dd { margin: 0; color: var(--ceniza); }

  .aviso {
    border: 1px solid var(--linea); border-left: 2px solid var(--accion);
    background: var(--grafito); padding: 16px 20px; margin: 28px 0 0;
    font-size: .89rem;
  }
  .aviso b { color: var(--hueso); font-weight: 600; }

  section { margin: 0 0 12px; page-break-inside: auto; }
  .seccion-cabeza {
    border-top: 1px solid var(--linea); padding-top: 26px;
    margin-top: 34px; page-break-after: avoid;
  }
  .seccion-cabeza h3 {
    font-family: var(--display); font-weight: 400; color: var(--hueso);
    font-size: 2rem; margin: 6px 0 8px;
  }
  .seccion-cabeza p { margin: 0; color: var(--plomo); max-width: 62ch; }
  .numero {
    font-family: var(--mono); font-size: 11px; letter-spacing: .18em;
    color: var(--accion);
  }

  .bloque { margin: 26px 0 0; page-break-inside: avoid; }
  .bloque h4 {
    font-family: var(--sans); font-weight: 600; color: var(--hueso);
    font-size: 1rem; margin: 0 0 5px;
  }
  .bloque .demuestra { margin: 0 0 12px; color: var(--ceniza);
                       max-width: 74ch; font-size: .9rem; }
  .bloque img {
    display: block; width: 100%; height: auto;
    border: 1px solid var(--linea); background: var(--negro);
  }
  .bloque figure { margin: 0; }
  .bloque figcaption {
    margin-top: 9px; font-size: .82rem; color: var(--plomo);
    display: flex; gap: .7rem; align-items: baseline;
  }
  .bloque figcaption .archivo {
    font-family: var(--mono); font-size: .72rem; color: var(--trazo);
    white-space: nowrap;
  }
  .falta {
    border: 1px dashed var(--trazo); padding: 20px; color: var(--plomo);
    font-family: var(--mono); font-size: .8rem; background: var(--carbon);
  }
  footer {
    margin-top: 44px; padding-top: 18px; border-top: 1px solid var(--linea);
    font-family: var(--mono); font-size: .72rem; color: var(--trazo);
  }
"""


def main() -> int:
    hoy = datetime.date.today()
    partes = ["""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Evidencias · Quinto avance · AutoPrime</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>%s</style></head><body>""" % ESTILOS]

    partes.append("""
  <div class="portada">
    <div class="sello">Quinto avance · Evidencias</div>
    <h1>AutoPrime</h1>
    <h2>Gestión comercial, informes, PQR y asistente</h2>
    <dl>
      <dt>Aprendiz</dt><dd>%s</dd>
      <dt>Ficha</dt><dd>%s</dd>
      <dt>Fecha</dt><dd>%s</dd>
      <dt>Pila</dt><dd>React 19 + Vite · FastAPI · MySQL</dd>
      <dt>Desplegado</dt><dd>autoprime-api-z9b6.onrender.com</dd>
    </dl>
    <div class="aviso">
      <b>Todas las capturas se generan ejecutando el sistema.</b> Las de
      consola no están escritas a mano: cada una corre su comando y recoge la
      salida tal cual, así que si una prueba dejara de pasar, la imagen lo
      enseñaría. Esa es la diferencia entre una evidencia y una ilustración.
    </div>
  </div>
""" % (html.escape(AUTOR), html.escape(FICHA), hoy.strftime("%d/%m/%Y")))

    faltan = []
    for indice, (titulo, intro, bloques) in enumerate(SECCIONES, 1):
        partes.append('<section><div class="seccion-cabeza">')
        partes.append('<div class="numero">%02d</div>' % indice)
        partes.append("<h3>%s</h3>" % html.escape(titulo))
        partes.append("<p>%s</p></div>" % html.escape(" ".join(intro.split())))

        for archivo, subtitulo, demuestra, pie in bloques:
            partes.append('<div class="bloque">')
            partes.append("<h4>%s</h4>" % html.escape(subtitulo))
            partes.append('<p class="demuestra">%s</p>' % html.escape(demuestra))
            datos = incrustar(archivo)
            if datos is None:
                faltan.append(archivo)
                partes.append(
                    '<div class="falta">Falta la captura %s.png &mdash; '
                    'se genera con herramientas/capturas_quinta.py</div>'
                    % html.escape(archivo))
            else:
                partes.append(
                    '<figure><img src="data:image/jpeg;base64,%s" alt="%s">'
                    '<figcaption><span>%s</span>'
                    '<span class="archivo">%s.png</span>'
                    "</figcaption></figure>"
                    % (datos, html.escape(subtitulo), html.escape(pie),
                       html.escape(archivo)))
            partes.append("</div>")
        partes.append("</section>")

    partes.append(
        "<footer>AutoPrime · %s · %s · generado el %s por "
        "herramientas/documento_quinta.py</footer>"
        % (html.escape(AUTOR), html.escape(FICHA), hoy.isoformat()))
    partes.append("</body></html>")

    with open(DESTINO_HTML, "w", encoding="utf-8") as f:
        f.write("\n".join(partes))

    peso = os.path.getsize(DESTINO_HTML) / 1024 / 1024
    total = sum(len(b) for _, _, b in SECCIONES)
    print("  %s" % DESTINO_HTML)
    print("  %d secciones, %d evidencias, %.1f MB"
          % (len(SECCIONES), total, peso))
    if faltan:
        print()
        print("  %d capturas que faltan (el documento lo dice en su sitio):"
              % len(faltan))
        for nombre in faltan:
            print("    %s" % nombre)

    # ------------------------------------------------------------------
    print()
    print("  Imprimiendo a PDF...")
    nav = Navegador()
    try:
        nav.ir("file:///" + DESTINO_HTML.replace("\\", "/"), espera=3.5)
        nav.js("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3.0)
        nav.js("window.scrollTo(0, 0)")
        time.sleep(0.8)

        pendientes = nav.js(
            "[...document.querySelectorAll('img')]"
            ".filter(i => !i.complete || i.naturalWidth === 0).length")
        if pendientes:
            print("  Aviso: %s imagenes sin cargar" % pendientes)

        # `printBackground` es imprescindible: el documento es oscuro, y sin
        # los fondos saldria texto gris claro sobre blanco.
        resultado = nav._enviar(
            "Page.printToPDF",
            printBackground=True,
            paperWidth=ANCHO_A4, paperHeight=ALTO_A4,
            marginTop=0.35, marginBottom=0.35,
            marginLeft=0.3, marginRight=0.3,
            scale=0.8, preferCSSPageSize=False,
        )
        with open(DESTINO_PDF, "wb") as f:
            f.write(base64.b64decode(resultado["data"]))
    finally:
        nav.cerrar()

    print("  %s" % DESTINO_PDF)
    print("  %.1f MB" % (os.path.getsize(DESTINO_PDF) / 1024 / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
