"""Cabeceras de seguridad: lo que se le dice al navegador que NO haga.

Una API puede estar bien escrita y aun así dejar que el navegador haga cosas
que nadie quiere. Estas cabeceras no arreglan un fallo del código: cierran
comportamientos que los navegadores traen encendidos por compatibilidad con
la web de hace veinte años.

Qué cierra cada una, y por qué esta API concreta la necesita:

**X-Content-Type-Options: nosniff** — sin ella, el navegador ignora el
`Content-Type` que manda el servidor y adivina el tipo mirando el contenido.
Esta API devuelve PDF y XLSX generados con texto que escribió gente; si un
navegador decide que uno de esos archivos «parece HTML», lo ejecuta como
HTML en el dominio de la API. Es la cabecera que más falta hace aquí.

**X-Frame-Options: DENY** — impide que otro sitio meta el panel dentro de un
iframe invisible y capture las pulsaciones de quien cree estar usando otra
página (clickjacking). El panel tiene botones que anulan ventas y borran
usuarios: no hay ningún motivo para que se vea desde fuera.

**Referrer-Policy** — sin ella, al seguir un enlace desde `/api/facturas/38`
el navegador manda esa URL entera al sitio de destino. El identificador de
una factura ajena no tiene por qué salir del sistema.

**Strict-Transport-Security** — obliga a usar HTTPS durante un año, incluso
si alguien teclea `http://`. Solo se manda en producción: en desarrollo se
trabaja por HTTP, y una vez que el navegador guarda esta cabecera para
`localhost` la recuerda para TODOS los proyectos que usen localhost, lo que
convierte un descuido de hoy en un problema de dentro de seis meses en otro
proyecto distinto.

**Content-Security-Policy** — va restrictiva porque esta aplicación no sirve
HTML: sirve JSON y archivos. La excepción son `/docs` y `/redoc`, que son
las páginas de documentación de FastAPI y cargan su JavaScript y su CSS
desde un CDN; con la política estricta se quedan en blanco, así que se les
da una propia en lugar de aflojar la de todo lo demás.
"""

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.configuracion import configuracion

# Nada de nada: ni scripts, ni marcos, ni formularios que envíen a otro
# sitio. Es lo que corresponde a un servidor que solo devuelve datos.
CSP_API = (
    "default-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'none'"
)

# Swagger y ReDoc cargan su JavaScript, su CSS y sus fuentes de jsdelivr, y
# pintan los iconos con imágenes embebidas en data:.
CSP_DOCUMENTACION = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "font-src 'self' https://cdn.jsdelivr.net; "
    "frame-ancestors 'none'; "
    "base-uri 'self'"
)

RUTAS_DOCUMENTACION = ("/docs", "/redoc", "/docs/oauth2-redirect")


class CabecerasDeSeguridad:
    """Middleware ASGI puro, sin `BaseHTTPMiddleware`.

    Se escribe a este nivel a propósito. `BaseHTTPMiddleware` envuelve la
    respuesta en un flujo intermedio, y con respuestas de archivo —un PDF de
    varios megas— eso significa pasar el contenido entero por otra capa.
    Aquí basta con tocar la lista de cabeceras cuando pasa el mensaje de
    inicio, y el cuerpo sigue de largo sin que nadie lo mire.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        ruta = scope.get("path", "")
        cabeceras = self._cabeceras(ruta)

        async def enviar(mensaje: Message) -> None:
            if mensaje["type"] == "http.response.start":
                existentes = mensaje.setdefault("headers", [])
                puestas = {nombre.lower() for nombre, _ in existentes}
                for nombre, valor in cabeceras:
                    # Si algo ya la puso, manda quien la puso: puede tener
                    # un motivo que aquí no se conoce.
                    if nombre.lower().encode() not in puestas:
                        existentes.append((nombre.encode(), valor.encode()))
            await send(mensaje)

        await self.app(scope, receive, enviar)

    def _cabeceras(self, ruta: str) -> list[tuple[str, str]]:
        politica = (
            CSP_DOCUMENTACION if ruta in RUTAS_DOCUMENTACION else CSP_API
        )

        cabeceras = [
            ("X-Content-Type-Options", "nosniff"),
            ("X-Frame-Options", "DENY"),
            ("Referrer-Policy", "no-referrer"),
            ("Content-Security-Policy", politica),
            # Apaga las capacidades del navegador que esta API no usa. Si un
            # día una de ellas hiciera falta, sale de aquí.
            ("Permissions-Policy",
             "camera=(), microphone=(), geolocation=(), payment=()"),
            # Sin esto, el navegador guarda en caché una respuesta con datos
            # de una cuenta y la reutiliza para la siguiente sesión abierta
            # en el mismo equipo.
            ("Cache-Control", "no-store"),
        ]

        if configuracion.entorno == "produccion":
            cabeceras.append((
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            ))

        return cabeceras
