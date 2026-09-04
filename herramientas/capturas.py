# -*- coding: utf-8 -*-
"""Captura las evidencias del entregable en PNG, sin intervención manual.

Maneja un Chrome sin ventana por el protocolo de DevTools: navega, espera a que
la página termine de montarse y guarda la imagen. Frente a ir apretando la
tecla de impresión de pantalla, esto da capturas del mismo tamaño, sin barras
del navegador ni escritorio de fondo, y repetibles: si mañana cambia una
pantalla, se vuelve a lanzar y quedan todas al día.

    backend/venv/Scripts/python herramientas/capturas.py

Necesita las tres piezas en marcha: MySQL, la API en el 8000 y Vite en el 5173.
"""

import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

from websockets.sync.client import connect

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "evidencias", "capturas")

WEB = "http://localhost:5173"
API = "http://127.0.0.1:8000"

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

ANCHO, ALTO = 1440, 900

# La cortina de entrada se reproduce en cada recarga, así que hay que dejarla
# terminar antes de disparar o todas las capturas saldrían en negro.
ESPERA_CORTINA = 3.2


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def peticion_json(url: str, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    pet = urllib.request.Request(url, data=datos)
    if datos is not None:
        pet.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(pet, timeout=15) as r:
        return json.loads(r.read().decode())


class Navegador:
    """Cliente mínimo del protocolo de DevTools: lo justo para capturar."""

    def __init__(self):
        self.puerto = puerto_libre()
        self.perfil = tempfile.mkdtemp(prefix="autoprime-capturas-")
        self.proceso = subprocess.Popen(
            [
                CHROME,
                "--headless=new",
                f"--remote-debugging-port={self.puerto}",
                f"--user-data-dir={self.perfil}",
                f"--window-size={ANCHO},{ALTO}",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-extensions",
                # Sin esto, un Chrome sin ventana desactiva la aceleración y el
                # vídeo de portada y el visor 3D no llegan a pintarse.
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--autoplay-policy=no-user-gesture-required",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.ws = self._conectar()
        self.siguiente_id = 0
        self._enviar("Page.enable")
        self._enviar("Runtime.enable")

    def _conectar(self):
        """Espera a que Chrome abra su puerto y devuelve el socket de la pestaña."""
        for _ in range(60):
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{self.puerto}/json/list", timeout=1
                ) as r:
                    objetivos = json.loads(r.read().decode())
                paginas = [o for o in objetivos if o.get("type") == "page"]
                if paginas:
                    return connect(
                        paginas[0]["webSocketDebuggerUrl"], max_size=64 * 1024 * 1024
                    )
            except (urllib.error.URLError, OSError, json.JSONDecodeError):
                pass
            time.sleep(0.5)
        raise RuntimeError("Chrome no abrió su puerto de depuración")

    def _enviar(self, metodo: str, **parametros):
        self.siguiente_id += 1
        ident = self.siguiente_id
        self.ws.send(json.dumps({"id": ident, "method": metodo, "params": parametros}))

        # Por el mismo canal llegan los avisos de la página; se descartan hasta
        # dar con la respuesta que corresponde a esta petición.
        while True:
            mensaje = json.loads(self.ws.recv(timeout=60))
            if mensaje.get("id") == ident:
                if "error" in mensaje:
                    raise RuntimeError(f"{metodo}: {mensaje['error']}")
                return mensaje.get("result", {})

    def ir(self, url: str, espera: float = ESPERA_CORTINA):
        self._enviar("Page.navigate", url=url)
        time.sleep(espera)

    def js(self, expresion: str):
        r = self._enviar(
            "Runtime.evaluate",
            expression=expresion,
            awaitPromise=True,
            returnByValue=True,
        )
        return r.get("result", {}).get("value")

    def capturar(self, nombre: str, pagina_entera: bool = False) -> str:
        r = self._enviar(
            "Page.captureScreenshot",
            format="png",
            captureBeyondViewport=pagina_entera,
        )
        destino = os.path.join(SALIDA, f"{nombre}.png")
        with open(destino, "wb") as f:
            f.write(base64.b64decode(r["data"]))
        peso = os.path.getsize(destino) / 1024
        print(f"    {nombre}.png  ({peso:.0f} KB)")
        return destino

    def cerrar(self):
        try:
            self.ws.close()
        except Exception:
            pass
        self.proceso.terminate()
        try:
            self.proceso.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proceso.kill()
        shutil.rmtree(self.perfil, ignore_errors=True)


# ---------------------------------------------------------------------------
def entrar_como(nav: Navegador, correo: str, password: str):
    """Deja la sesión iniciada sin pasar por el formulario.

    El formulario se captura aparte, como evidencia propia. Para el resto de
    pantallas interesa llegar ya dentro: repetir el login en cada captura
    multiplicaría el tiempo y las ocasiones de que algo falle a media carga.
    """
    sesion = peticion_json(f"{API}/api/auth/login", {"correo": correo, "password": password})

    # Hay que estar en el origen de la aplicación para poder escribir en su
    # almacenamiento; desde `about:blank` no se puede. Y hay que esperar a que
    # el documento nuevo exista: si se evalúa demasiado pronto, la instrucción
    # corre todavía en el documento anterior y el token acaba en otro origen.
    # Esa es la razón por la que la primera tanda de capturas de los paneles
    # salió mostrando el formulario de acceso.
    nav.ir(WEB, espera=2.0)
    for _ in range(20):
        if nav.js("location.origin") == WEB:
            break
        time.sleep(0.5)
    else:
        raise RuntimeError(f"no se llegó a {WEB} para iniciar la sesión")

    nav.js(f"localStorage.setItem('autoprime:token', {json.dumps(sesion['token'])})")

    guardado = nav.js("localStorage.getItem('autoprime:token')")
    if guardado != sesion["token"]:
        raise RuntimeError("el token no quedó guardado en el navegador")

    return sesion["usuario"]


def comprobar_dentro(nav: Navegador, ruta_esperada: str):
    """Aborta si la ruta protegida rebotó al acceso.

    Sin esto, una sesión que no cuaja produce capturas del formulario de
    acceso con el nombre del panel: evidencia equivocada y difícil de notar
    revisando miniaturas.
    """
    actual = nav.js("location.pathname")
    if actual != ruta_esperada:
        raise RuntimeError(
            f"se esperaba {ruta_esperada} y se acabó en {actual}: la sesión no cuajó"
        )


def main() -> int:
    os.makedirs(SALIDA, exist_ok=True)
    print(f"  Guardando en {SALIDA}")
    print()

    nav = Navegador()
    try:
        # ---------------- Pantallas públicas ----------------
        print("  Públicas")
        nav.ir(f"{WEB}/")
        nav.capturar("req-01-portada")

        nav.ir(f"{WEB}/modelos")
        nav.capturar("req-14-catalogo")

        nav.ir(f"{WEB}/login")
        nav.capturar("req-10-login")

        # Validación en vivo: se escribe algo inválido y se deja el foco.
        nav.ir(f"{WEB}/login", espera=ESPERA_CORTINA)
        nav.js(
            """
            (() => {
              const set = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
              const c = document.querySelector('input[type=email]');
              set.call(c, 'esto-no-es-un-correo');
              c.dispatchEvent(new Event('input', { bubbles: true }));
              c.dispatchEvent(new Event('blur', { bubbles: true }));
              return true;
            })()
            """
        )
        time.sleep(0.8)
        nav.capturar("req-21-validacion")

        # Recuperación de contraseña
        nav.ir(f"{WEB}/login", espera=ESPERA_CORTINA)
        nav.js(
            "[...document.querySelectorAll('button')]"
            ".find(b => b.textContent.includes('Olvidaste')).click()"
        )
        time.sleep(1.0)
        nav.capturar("req-15-recuperar")

        # Alta de cliente: el formulario se abre en una ventana sobre el acceso.
        nav.ir(f"{WEB}/login", espera=ESPERA_CORTINA)
        nav.js(
            "[...document.querySelectorAll('a, button')]"
            ".find(e => /crear una cuenta/i.test(e.textContent)).click()"
        )
        time.sleep(1.2)
        nav.capturar("req-09-registro")

        # El botón flotante vive en todas las páginas; se enseña sobre el
        # catálogo, donde se distingue del fondo mejor que sobre el vídeo.
        nav.ir(f"{WEB}/modelos")
        nav.capturar("req-24-whatsapp")

        # ---------------- Documentación de la API ----------------
        print("  API")
        nav.ir(f"{API}/docs", espera=3.5)
        nav.capturar("req-25-swagger")

        # Los esquemas de Pydantic están al final de la documentación: es la
        # cara visible de la separación entre modelos y esquemas.
        nav.js("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.2)
        nav.capturar("req-06-esquemas")

        nav.ir(f"{API}/salud", espera=1.5)
        nav.capturar("req-07-salud")

        # ---------------- Paneles ----------------
        print("  Paneles")
        entrar_como(nav, "admin@autoprime.com.co", "Admin2026!")
        nav.ir(f"{WEB}/panel/admin")
        comprobar_dentro(nav, "/panel/admin")
        nav.capturar("req-17-panel-admin")

        # El alta desde el panel, que es donde sí se elige el rol. Junto con la
        # tabla de la captura anterior completa el CRUD.
        nav.js(
            "[...document.querySelectorAll('button')]"
            ".find(b => /agregar usuario/i.test(b.textContent)).click()"
        )
        time.sleep(1.2)
        nav.capturar("req-16-crud-usuarios")

        entrar_como(nav, "empleado@autoprime.com.co", "Empleado2026!")
        nav.ir(f"{WEB}/panel/empleado")
        comprobar_dentro(nav, "/panel/empleado")
        nav.capturar("req-18-panel-empleado")

        entrar_como(nav, "cliente@autoprime.com.co", "Cliente2026!")
        nav.ir(f"{WEB}/panel/cliente")
        comprobar_dentro(nav, "/panel/cliente")
        nav.capturar("req-19-panel-cliente")

        # El nombre en la barra se ve mejor con el raíl desplegado.
        nav.ir(f"{WEB}/modelos")
        nav.js(
            "document.querySelector('aside[aria-label]')"
            ".style.width = '264px'"
        )
        time.sleep(0.6)
        nav.capturar("req-20-navbar")

        print()
        print(f"  Listo. {len(os.listdir(SALIDA))} archivos en evidencias/capturas/")
        return 0
    finally:
        nav.cerrar()


if __name__ == "__main__":
    sys.exit(main())
