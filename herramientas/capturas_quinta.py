# -*- coding: utf-8 -*-
"""Captura las evidencias del quinto avance: lo comercial, los informes y el chat.

Reutiliza el navegador sin ventana de `capturas.py` —el del cuarto avance— y
cambia lo que cambia: las pantallas.

    backend/venv/Scripts/python herramientas/capturas_quinta.py

Necesita la API en el 8000 y Vite en el 5173.

POR QUÉ NO USA ESPERAS FIJAS
----------------------------
El cuarto avance capturaba pantallas que se pintaban solas. Estas no: el
tablero pide sus cifras, la tabla de ventas pide su página, y con un `sleep`
de tres segundos unas veces sale la pantalla y otras sale «Cargando el
tablero…». Una evidencia que sale bien siete de cada diez veces no es una
evidencia. Por eso aquí se espera a que aparezca algo concreto de la pantalla
y se aborta si no aparece, en vez de contar hasta tres y disparar.

LOS PDF SE DESCARGAN Y SE ABREN COMO ARCHIVO
--------------------------------------------
Las rutas de descarga piden la cabecera `Authorization`, y una barra de
direcciones no puede mandarla. Así que el PDF se baja con el token desde
Python, se guarda, y se abre el archivo en el visor del propio Chrome: lo que
se ve en la captura es el PDF que genera la API, no una imitación.
"""

import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capturas  # noqa: E402
from capturas import Navegador, entrar_como  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "evidencias", "capturas-quinta")

# `capturar()` guarda en el `SALIDA` del módulo que lo define, así que hay que
# cambiárselo ahí. Si no, estas capturas se mezclarían con las del cuarto.
capturas.SALIDA = SALIDA

WEB = capturas.WEB
API = capturas.API

# El reporte se pide por fechas, no por «últimos N días»: `desde` y `hasta`.
# Pedirlo con `?dias=90` devuelve el reporte de HOY, porque FastAPI descarta
# sin avisar los parámetros que no conoce y el rango se queda en su valor por
# defecto. Salió un reporte impecable y con todo a cero.
def rango(dias: int):
    hasta = datetime.date.today()
    return (hasta - datetime.timedelta(days=dias)).isoformat(), hasta.isoformat()


ADMIN = ("admin@autoprime.com.co", "Admin2026!")
EMPLEADO = ("empleado@autoprime.com.co", "Empleado2026!")
CLIENTE = ("cliente@autoprime.com.co", "Cliente2026!")


# ---------------------------------------------------------------------------
# Esperas con criterio
# ---------------------------------------------------------------------------
def esperar(nav, condicion_js: str, que_espera: str, limite: float = 25.0):
    """Espera a que una condición se cumpla en la página, o aborta diciendo cuál.

    El mensaje importa: cuando esto falla a las dos de la mañana, la diferencia
    entre «timeout» y «nunca apareció la tabla de ventas» son veinte minutos.
    """
    plazo = time.time() + limite
    while time.time() < plazo:
        try:
            if nav.js("!!(" + condicion_js + ")"):
                return
        except RuntimeError:
            pass          # la página aún se está reemplazando
        time.sleep(0.4)
    raise RuntimeError("no apareció " + que_espera + " en %.0fs" % limite)


def esperar_texto(nav, texto: str, limite: float = 25.0):
    esperar(nav,
            "document.body.innerText.includes(" + json.dumps(texto) + ")",
            "el texto «" + texto + "»", limite)


def esperar_sin_cargando(nav, limite: float = 25.0):
    esperar(nav, "!/Cargando/i.test(document.body.innerText)",
            "el final de la carga", limite)


def esperar_filas(nav, minimo: int = 1, limite: float = 25.0):
    """Espera a que la tabla traiga filas.

    Mejor criterio que buscar un rótulo: el rótulo lo pinta React de inmediato
    y no dice nada de si los datos llegaron. Esperando filas, una captura que
    sale es además una captura que enseña datos, que es lo que se quiere
    enseñar. Una tabla vacía deja de ser una evidencia válida y pasa a ser un
    fallo, que es exactamente lo que debe ser.
    """
    esperar(nav,
            "document.querySelectorAll('tbody tr').length >= %d" % minimo,
            "al menos %d fila en la tabla" % minimo, limite)


# Sube desde el enlace SOLO mientras el padre siga siendo un flotante pequeño.
#
# La primera versión usaba `closest('div,aside')`, que sube hasta el primer div
# que encuentre —y el primero que encuentra es el contenedor de la página—.
# Resultado: `display:none` a la página entera y dieciséis capturas en negro.
# El tope de tamaño es lo que impide que vuelva a pasar: un contenedor de
# página nunca mide menos de 400 px de ancho.
FLOTANTES = """
  (function () {
    var enlaces = document.querySelectorAll(
      'a[href*="wa.me"], a[href*="whatsapp"], a[href^="mailto:"]');
    for (var i = 0; i < enlaces.length; i++) {
      var e = enlaces[i];
      while (e.parentElement) {
        var p = e.parentElement;
        var s = getComputedStyle(p);
        var r = p.getBoundingClientRect();
        var flota = (s.position === 'fixed' || s.position === 'absolute');
        if (!flota || r.width > 400 || r.height > 400) break;
        e = p;
      }
      e.style.display = 'none';
    }
    return enlaces.length;
  })()
"""


def sin_distracciones(nav):
    """Aparta el botón flotante de WhatsApp, y nada más.

    Vive fijo en la esquina y se monta encima de la esquina inferior derecha de
    cada captura. Aquí estorba; tiene su propia evidencia en el cuarto avance,
    donde es el tema.

    De la cortina de entrada no hace falta ocuparse: se retira sola a los 2,7 s
    y todas las esperas de aquí son más largas que eso.
    """
    nav.js(FLOTANTES)
    time.sleep(0.3)


# ---------------------------------------------------------------------------
# Descargas
# ---------------------------------------------------------------------------
def token_de(correo: str, password: str) -> str:
    pet = urllib.request.Request(
        API + "/api/auth/login",
        data=json.dumps({"correo": correo, "password": password}).encode(),
    )
    pet.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(pet, timeout=20) as r:
        return json.loads(r.read())["token"]


def bajar(ruta: str, token: str, destino: str) -> str:
    """Trae un archivo de la API con el token puesto y lo guarda."""
    pet = urllib.request.Request(API + ruta)
    pet.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(pet, timeout=120) as r:
        datos = r.read()
        tipo = r.headers.get("content-type", "")
    with open(destino, "wb") as f:
        f.write(datos)
    print("      bajado %s  (%.0f KB, %s)"
          % (os.path.basename(destino), len(datos) / 1024, tipo.split(";")[0]))
    return destino


def pedir_json(ruta: str, token: str):
    pet = urllib.request.Request(API + ruta)
    pet.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(pet, timeout=60) as r:
        return json.loads(r.read())


def lista_del_sobre(sobre: dict) -> list:
    """Saca la lista de un sobre paginado sin saber cómo se llama.

    Cada sobre nombra su lista como lo que lleva —`ventas`, `facturas`, `pqr`—
    en vez de un `datos` genérico, que se lee mejor en la documentación. Aquí
    da igual cuál sea: se coge la única lista que hay, y así esto no se rompe
    cuando se añada el sobre siguiente.
    """
    for clave, valor in sobre.items():
        if isinstance(valor, list):
            return valor
    raise RuntimeError("el sobre no trae ninguna lista: " + str(list(sobre)))


# ---------------------------------------------------------------------------
# La tanda
# ---------------------------------------------------------------------------
fallos = []


def paso(nombre, funcion):
    """Corre una captura y, si revienta, lo anota y sigue.

    Con dieciséis capturas encadenadas, que la número tres falle y deje sin
    hacer las trece siguientes es perder el viaje entero. Se anota, se sigue, y
    al final se dice qué faltó: así una pasada da la lista completa de lo que
    hay que arreglar, en vez de darla de una en una.
    """
    try:
        funcion()
    except Exception as error:
        fallos.append((nombre, "%s: %s" % (type(error).__name__, error)))
        print("    -- %s: %s: %s" % (nombre, type(error).__name__, str(error)[:80]))


def main() -> int:
    os.makedirs(SALIDA, exist_ok=True)
    print("  Guardando en " + SALIDA)
    print()

    t_admin = token_de(*ADMIN)

    # Los identificadores no se fijan a mano: se preguntan. Escribir «factura 7»
    # aquí funciona hasta que alguien vuelve a sembrar la base.
    facturas = lista_del_sobre(pedir_json("/api/facturas?tamano=1", t_admin))
    if not facturas:
        print("  No hay facturas en la base. Siembra antes de capturar.")
        return 1
    id_factura = facturas[0]["id"]
    print("  Factura de muestra: #%s" % facturas[0].get("numero", id_factura))

    temporal = os.path.join(SALIDA, "_descargas")
    os.makedirs(temporal, exist_ok=True)

    nav = Navegador()
    try:
        # ---------------- Tablero ----------------
        print("  Tablero")
        entrar_como(nav, *ADMIN)

        def tablero():
            nav.ir(WEB + "/panel/tablero")
            esperar_texto(nav, "Ingresos por día")
            esperar_sin_cargando(nav)
            sin_distracciones(nav)
            nav.capturar("q01-tablero-ingresos")
        paso("q01-tablero-ingresos", tablero)

        def ranking():
            nav.js("window.scrollTo(0, document.body.scrollHeight * 0.45)")
            time.sleep(1.2)
            nav.capturar("q02-tablero-ranking")
        paso("q02-tablero-ranking", ranking)

        def noventa():
            nav.js("window.scrollTo(0, 0)")
            nav.js("[...document.querySelectorAll('button')]"
                   ".find(b => /90/.test(b.textContent))?.click()")
            time.sleep(2.5)
            esperar_sin_cargando(nav)
            sin_distracciones(nav)
            nav.capturar("q03-tablero-90-dias")
        paso("q03-tablero-90-dias", noventa)

        # ---------------- Ventas ----------------
        print("  Ventas")

        def ventas():
            nav.ir(WEB + "/panel/ventas")
            esperar_sin_cargando(nav)
            esperar_filas(nav)
            sin_distracciones(nav)
            nav.capturar("q04-ventas-listado")
        paso("q04-ventas-listado", ventas)

        def nueva():
            nav.js("[...document.querySelectorAll('button')]"
                   ".find(b => /nueva venta|registrar venta|agregar/i"
                   ".test(b.textContent))?.click()")
            time.sleep(1.4)
            nav.capturar("q05-ventas-nueva")
        paso("q05-ventas-nueva", nueva)

        # ---------------- Facturas ----------------
        print("  Facturas")

        def facturas_pantalla():
            nav.ir(WEB + "/panel/facturas")
            esperar_sin_cargando(nav)
            esperar_filas(nav)
            sin_distracciones(nav)
            nav.capturar("q06-facturas-listado")
        paso("q06-facturas-listado", facturas_pantalla)

        # ---------------- Los documentos que genera la API ----------------
        print("  Documentos")

        def factura_pdf():
            archivo = bajar("/api/facturas/%d/pdf" % id_factura, t_admin,
                            os.path.join(temporal, "factura.pdf"))
            nav.ir("file:///" + archivo.replace("\\", "/"), espera=3.5)
            nav.capturar("q07-factura-pdf")
        paso("q07-factura-pdf", factura_pdf)

        def reporte_pdf():
            desde, hasta = rango(90)
            archivo = bajar("/api/reportes/ventas/pdf?desde=%s&hasta=%s"
                            % (desde, hasta), t_admin,
                            os.path.join(temporal, "reporte.pdf"))
            nav.ir("file:///" + archivo.replace("\\", "/"), espera=3.5)
            nav.capturar("q08-reporte-pdf")
        paso("q08-reporte-pdf", reporte_pdf)

        def reporte_excel():
            # El Excel no se puede enseñar en un navegador. Se baja igualmente
            # para comprobar que sale y con qué peso; su contenido se enseña en
            # la evidencia de consola, hoja por hoja.
            desde, hasta = rango(90)
            bajar("/api/reportes/ventas/excel?desde=%s&hasta=%s"
                  % (desde, hasta), t_admin,
                  os.path.join(temporal, "reporte.xlsx"))
        paso("q09-reporte-excel", reporte_excel)

        # ---------------- PQR ----------------
        print("  PQR")

        def pqr():
            nav.ir(WEB + "/panel/pqr")
            esperar_sin_cargando(nav)
            esperar_filas(nav)
            sin_distracciones(nav)
            nav.capturar("q10-pqr-listado")
        paso("q10-pqr-listado", pqr)

        def responder():
            nav.js("[...document.querySelectorAll('button')]"
                   ".find(b => /responder/i.test(b.textContent))?.click()")
            time.sleep(1.4)
            nav.capturar("q11-pqr-responder")
        paso("q11-pqr-responder", responder)

        # ---------------- Asistente ----------------
        print("  Asistente")

        def chat():
            """El asistente contestando de verdad, no el saludo.

            Abierto y sin usar solo demuestra que hay un panel. Lo que hay que
            enseñar es la vuelta completa: pregunta -> modelo -> respuesta. Por
            eso se pulsa una de las preguntas sugeridas y se espera a que el
            registro tenga las dos burbujas.
            """
            nav.ir(WEB + "/modelos")
            time.sleep(2.0)
            nav.js("""
              (function () {
                var b = [].slice.call(document.querySelectorAll('button'))
                  .filter(function (x) {
                    return /asistente|chat/i.test(
                      (x.getAttribute('aria-label') || '') + x.textContent);
                  })[0];
                if (b) b.click();
                return !!b;
              })()
            """)
            time.sleep(1.5)

            nav.js("""
              (function () {
                var b = [].slice.call(document.querySelectorAll('button'))
                  .filter(function (x) { return /vehículos tienen disponibles/i
                    .test(x.textContent); })[0];
                if (b) b.click();
                return !!b;
              })()
            """)
            # El modelo tarda lo suyo, y más la primera vez.
            # Dos burbujas NO bastan: la segunda es el «Escribiendo…», y
            # esperando solo por el número salía la captura con el aviso
            # puesto y sin respuesta. Hay que esperar a que se vaya.
            # (`[role=log]` va sin comillas: es CSS válido y ahorra el
            # baile de escapes entre Python y JavaScript.)
            esperar(nav,
                    "document.querySelectorAll('[role=log] > *').length >= 2"
                    " && !/Escribiendo/i.test("
                    "document.querySelector('[role=log]').innerText)",
                    "la respuesta del asistente", limite=45.0)
            time.sleep(1.2)
            nav.capturar("q12-chat-asistente")
        paso("q12-chat-asistente", chat)

        # ---------------- Lo que ve cada rol ----------------
        print("  Roles")

        def empleado():
            entrar_como(nav, *EMPLEADO)
            nav.ir(WEB + "/panel/ventas")
            esperar_sin_cargando(nav)
            sin_distracciones(nav)
            nav.capturar("q13-panel-empleado")
        paso("q13-panel-empleado", empleado)

        def cliente():
            entrar_como(nav, *CLIENTE)
            nav.ir(WEB + "/panel/cliente")
            esperar_sin_cargando(nav)
            sin_distracciones(nav)
            nav.capturar("q14-panel-cliente")
        paso("q14-panel-cliente", cliente)

        def compras():
            nav.ir(WEB + "/panel/ventas")
            esperar_sin_cargando(nav)
            sin_distracciones(nav)
            nav.capturar("q15-cliente-sus-compras")
        paso("q15-cliente-sus-compras", compras)

        # ---------------- La API ----------------
        print("  API")

        def swagger():
            nav.ir(API + "/docs", espera=4.0)
            nav.js("""
              (() => {
                const t = [...document.querySelectorAll('.opblock-tag')]
                  .find(e => /venta/i.test(e.textContent));
                if (t) t.scrollIntoView({block: 'start'});
                return !!t;
              })()
            """)
            time.sleep(1.2)
            nav.capturar("q16-swagger-quinta")
        paso("q16-swagger-quinta", swagger)

        print()
        hechas = len([f for f in os.listdir(SALIDA) if f.endswith(".png")])
        print("  %d capturas en evidencias/capturas-quinta/" % hechas)
        if fallos:
            print()
            print("  %d sin salir:" % len(fallos))
            for nombre, motivo in fallos:
                print("    %s: %s" % (nombre, motivo[:100]))
            return 1
        return 0
    finally:
        nav.cerrar()


if __name__ == "__main__":
    sys.exit(main())
