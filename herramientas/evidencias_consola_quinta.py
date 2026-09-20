# -*- coding: utf-8 -*-
"""Las evidencias del quinto avance que no son pantallas de la aplicación.

Las pruebas, la batería de Postman, lo que pasa cuando alguien intenta colar
SQL, el contenido del Excel y el estado del despliegue: nada de eso se ve en
una captura del sitio, y todo se demuestra mejor con la salida real del
comando que con una explicación.

    backend/venv/Scripts/python herramientas/evidencias_consola_quinta.py

Como en el cuarto avance: **todo se ejecuta de verdad**. Si una prueba deja
de pasar, la imagen lo enseña. Esa es la diferencia entre una evidencia y una
ilustración.

NO USA EL CLIENTE `mysql`
-------------------------
El del cuarto avance llamaba a `C:\\xampp\\mysql\\bin\\mysql.exe`, porque
entonces la base estaba en XAMPP. Ahora está en Aiven, con TLS, y ese cliente
no llega. Lo que hace falta preguntarle a la base se pregunta por SQLAlchemy,
con la misma configuración que usa la aplicación.
"""

import html
import io
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capturas  # noqa: E402
from capturas import Navegador  # noqa: E402
from evidencias_consola import PLANTILLA, correr, resaltar  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "evidencias", "capturas-quinta")
capturas.SALIDA = SALIDA

BACKEND = os.path.join(RAIZ, "backend")
PY = os.path.join(BACKEND, "venv", "Scripts", "python.exe")
API = "http://127.0.0.1:8000"
PRODUCCION = "https://autoprime-api-z9b6.onrender.com"

ADMIN = {"correo": "admin@autoprime.com.co", "password": "Admin2026!"}


# ---------------------------------------------------------------------------
# Recolección
# ---------------------------------------------------------------------------
def token_admin() -> str:
    pet = urllib.request.Request(
        API + "/api/auth/login", data=json.dumps(ADMIN).encode())
    pet.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(pet, timeout=20) as r:
        return json.loads(r.read())["token"]


def pedir(url: str, token=None, cuerpo=None, metodo=None):
    """Devuelve (código, cabeceras en minúscula, cuerpo en bytes)."""
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    pet = urllib.request.Request(url, data=datos, method=metodo)
    if datos is not None:
        pet.add_header("Content-Type", "application/json")
    if token:
        pet.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(pet, timeout=90) as r:
            return r.status, {c.lower(): v for c, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as e:
        return e.code, {c.lower(): v for c, v in e.headers.items()}, e.read()


def cabeza_y_cola(texto: str, cabeza: int = 12, cola: int = 22) -> str:
    """Deja el principio y el final, y dice cuanto se salto por el medio.

    Para newman el principio prueba que corrio y el final es lo unico que de
    verdad se lee: cuantas peticiones, cuantas comprobaciones, cuantas
    fallaron. Recortar solo por arriba —que es lo que hace `correr`— deja
    fuera justo el resumen.
    """
    lineas = texto.splitlines()
    if len(lineas) <= cabeza + cola:
        return texto
    saltadas = len(lineas) - cabeza - cola
    return chr(10).join(
        lineas[:cabeza]
        + ["", "    ... (%d lineas mas) ..." % saltadas, ""]
        + lineas[-cola:])


def inyecciones(token: str) -> str:
    """Manda las cargas clásicas y enseña qué contesta la API a cada una.

    El punto no es que las rechace: es que las TRATA COMO TEXTO. Un 200 con
    cero resultados significa que buscó la cadena tal cual y no encontró a
    nadie que se llame así, que es exactamente lo correcto. Lo que no puede
    salir por ningún lado es un 500.
    """
    cargas = [
        "' OR '1'='1",
        "'; DROP TABLE usuarios; --",
        "' UNION SELECT id, correo, password_hash FROM usuarios --",
        "admin'--",
        "1; DELETE FROM ventas",
    ]
    lineas = ["$ cinco cargas clasicas contra GET /api/usuarios?buscar=...", ""]
    for carga in cargas:
        consulta = urllib.parse.quote(carga)
        codigo, _, cuerpo = pedir(
            API + "/api/usuarios?buscar=" + consulta, token=token)
        try:
            total = json.loads(cuerpo).get("total", "?")
        except Exception:
            total = "?"
        marca = "OK " if codigo in (200, 422) else "FALLA"
        lineas.append("%s HTTP %s  total=%-3s  <- %s"
                      % (marca, codigo, total, carga))

    # Y, lo que de verdad cierra el argumento: las tablas siguen ahi.
    codigo, _, cuerpo = pedir(API + "/api/usuarios", token=token)
    total = json.loads(cuerpo).get("total", "?")
    lineas += [
        "",
        "$ y despues de mandarlas todas, la tabla sigue entera",
        "HTTP %s  usuarios = %s" % (codigo, total),
        "",
        "No hay ni un SQL escrito a mano en toda app/: el texto viaja",
        "SIEMPRE como parametro enlazado, nunca pegado a la sentencia.",
    ]
    return "\n".join(lineas)


def fuerza_bruta() -> str:
    """Prueba contraseñas a discreción contra el login, hasta que frene."""
    lineas = ["$ POST /api/auth/login con la clave equivocada, en bucle", ""]
    for intento in range(1, 14):
        codigo, cabeceras, cuerpo = pedir(
            API + "/api/auth/login",
            cuerpo={"correo": ADMIN["correo"], "password": "incorrecta"})
        if codigo == 429:
            espera = cabeceras.get("retry-after", "?")
            try:
                codigo_error = json.loads(cuerpo).get("codigo", "")
            except Exception:
                codigo_error = ""
            lineas.append("intento %-2d  HTTP 429  FRENADO  "
                          "retry-after=%ss  codigo=%s"
                          % (intento, espera, codigo_error))
            lineas += [
                "",
                "bcrypt protege el hash si alguien roba la tabla; no protege",
                "de que le pregunten al servidor mil veces por segundo. Eso",
                "lo hace este freno, que cuenta por origen Y por correo: asi",
                "no se esquiva cambiando de direccion en cada intento.",
            ]
            return "\n".join(lineas)
        lineas.append("intento %-2d  HTTP %s" % (intento, codigo))
    lineas.append("")
    lineas.append("FALLA: nunca freno")
    return "\n".join(lineas)


def cabeceras_produccion() -> str:
    """Lee las cabeceras del despliegue real, no de local."""
    esperadas = [
        ("x-content-type-options", "nosniff",
         "el navegador no adivina el tipo de un PDF generado"),
        ("x-frame-options", "DENY", "nadie mete el sitio en un iframe"),
        ("referrer-policy", "no-referrer", "no se filtra de donde viene nadie"),
        ("cache-control", "no-store", "ningun intermediario guarda respuestas"),
        ("content-security-policy", "default-src 'none'", "la API no carga nada"),
        ("strict-transport-security", "max-age", "solo por HTTPS, de aqui en adelante"),
    ]
    codigo, cabeceras, cuerpo = pedir(PRODUCCION + "/salud")
    lineas = ["$ curl -I %s/salud" % PRODUCCION, "", "HTTP %s" % codigo, ""]
    for nombre, trozo, porque in esperadas:
        valor = cabeceras.get(nombre, "")
        marca = "OK " if trozo in valor else "FALLA"
        lineas.append("%s %-28s %s" % (marca, nombre, valor[:52] or "(ausente)"))
        lineas.append("    %s" % porque)
    try:
        datos = json.loads(cuerpo)
        lineas += ["", "$ y el cuerpo de /salud:",
                   "    base_datos : %s" % datos.get("base_datos"),
                   "    cifrado    : %s" % datos.get("cifrado"),
                   "    entorno    : %s" % datos.get("entorno")]
    except Exception:
        pass
    return "\n".join(lineas)


def despliegue() -> str:
    """Las dos rutas de estado, en el despliegue de verdad."""
    lineas = []
    for ruta, para_que in (
        ("/vivo", "lo que consulta Render para decidir si el servicio vive"),
        ("/salud", "el diagnostico completo, que SI consulta la base"),
    ):
        codigo, _, cuerpo = pedir(PRODUCCION + ruta)
        lineas.append("$ GET %s%s" % (PRODUCCION, ruta))
        lineas.append("  # %s" % para_que)
        lineas.append("HTTP %s" % codigo)
        try:
            lineas.append("  " + json.dumps(json.loads(cuerpo), ensure_ascii=False))
        except Exception:
            lineas.append("  " + cuerpo[:120].decode("utf-8", "replace"))
        lineas.append("")
    lineas += [
        "Son dos preguntas distintas y tienen dos respuestas. Atar la",
        "comprobacion de salud a la base significa que una caida de la base",
        "tumba tambien los despliegues; paso, y costo uno.",
    ]
    return "\n".join(lineas)


def contenido_excel(token: str) -> str:
    """Abre el .xlsx que genera la API y enseña lo que lleva dentro.

    Un Excel no se puede fotografiar en un navegador, pero sí se puede abrir
    y contar: es un zip con XML. Así la evidencia dice qué hojas trae y
    cuántas filas, sin depender de que haya Excel instalado.
    """
    import datetime
    hasta = datetime.date.today()
    desde = hasta - datetime.timedelta(days=90)
    codigo, cabeceras, cuerpo = pedir(
        API + "/api/reportes/ventas/excel?desde=%s&hasta=%s"
        % (desde.isoformat(), hasta.isoformat()), token=token)

    lineas = [
        "$ GET /api/reportes/ventas/excel?desde=%s&hasta=%s"
        % (desde.isoformat(), hasta.isoformat()),
        "",
        "HTTP %s  %s" % (codigo, cabeceras.get("content-type", "")[:60]),
        "%.1f KB" % (len(cuerpo) / 1024),
        "",
    ]

    with zipfile.ZipFile(io.BytesIO(cuerpo)) as z:
        libro = z.read("xl/workbook.xml").decode("utf-8", "replace")
        hojas = re.findall(r'<sheet[^>]*name="([^"]+)"', libro)
        lineas.append("$ hojas del libro")
        for i, nombre in enumerate(hojas, 1):
            try:
                hoja = z.read("xl/worksheets/sheet%d.xml" % i).decode(
                    "utf-8", "replace")
                filas = hoja.count("<row ")
            except KeyError:
                filas = "?"
            lineas.append("    %-14s %s filas" % (nombre, filas))

        graficas = [n for n in z.namelist() if "charts/chart" in n]
        lineas.append("")
        lineas.append("$ graficas incrustadas: %d" % len(graficas))

        # La prueba que de verdad importa: no basta con CONTAR las formulas,
        # hay que mirar QUE son. Se sacan todas y se comprueba que cada una
        # es un SUBTOTAL puesto por el generador. Si alguna fuera otra cosa,
        # seria texto de alguien que acabo ejecutandose, y aqui se veria.
        todas = []
        for nombre in sorted(z.namelist()):
            if nombre.startswith("xl/worksheets/sheet"):
                todas += re.findall(
                    r"<f>(.*?)</f>",
                    z.read(nombre).decode("utf-8", "replace"))
        # Lo que hace peligrosa a una formula no es como se llame la funcion:
        # es que lleve texto de alguien dentro. `SUM(B18:B108)` opera sobre
        # un rango de celdas y no puede contener nada que haya escrito un
        # cliente; `=cmd|' /c calc'!A1` si. El criterio, entonces, es que la
        # formula sea puramente estructural: funcion, celdas, numeros y
        # separadores, y NI UNA comilla.
        #
        # La primera version exigia que todas fueran SUBTOTAL y marcaba como
        # fallo los dos SUM del resumen, que son igual de inofensivos.
        ESTRUCTURAL = re.compile(r"^[A-Z]+\([A-Z0-9:,.$ ]*\)$")
        ajenas = [f for f in todas
                  if not ESTRUCTURAL.match(f.upper()) or '"' in f or "'" in f]

        lineas += ["", "$ las %d formulas del libro, una por una" % len(todas)]
        for formula in todas[:6]:
            lineas.append("    %s" % formula[:64])
        if len(todas) > 6:
            lineas.append("    ... y %d mas del mismo tipo" % (len(todas) - 6))
        lineas += [
            "",
            "$ formulas con texto dentro (las peligrosas): %d" % len(ajenas),
        ]
        if ajenas:
            for formula in ajenas[:4]:
                lineas.append("    FALLA  %s" % formula[:64])
        else:
            lineas.append("    ninguna: todas operan sobre rangos de celdas")
        lineas += [
            "",
            "Eso es lo que hay que mirar. Un cliente que se llame",
            "=cmd|' /c calc'!A1 ejecuta un programa en el ordenador de quien",
            "abra el informe: se llama inyeccion de formulas y es la",
            "vulnerabilidad clasica del .xlsx. El texto de la gente se",
            "escribe SIEMPRE como texto, nunca como formula.",
        ]
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
def main() -> int:
    os.makedirs(SALIDA, exist_ok=True)
    tmp = os.path.join(SALIDA, "_render.html")

    print("  Recogiendo (esto tarda: se ejecuta todo de verdad)")
    token = token_admin()

    print("    pruebas con pytest...")
    # OJO con el `-q`: `pytest.ini` ya lo trae en `addopts`, asi que pasarlo
    # otra vez da `-qq`, y ese nivel suprime la linea del resumen. Es decir,
    # la evidencia salia con los puntos pero SIN el «172 passed», que es lo
    # unico que a nadie le interesa leer de aqui.
    salida_pytest = correr(
        '"%s" -m pytest --tb=no' % PY, cwd=BACKEND, limite=30)

    # Y el desglose por archivo. Aqui el `-qq` SI interesa: a ese nivel
    # `--collect-only` deja de listar las 172 pruebas una por una y saca
    # justo el recuento por archivo, que es lo que se quiere ensenar.
    desglose = correr('"%s" -m pytest --collect-only -q' % PY,
                      cwd=BACKEND, limite=20)

    print("    bateria de Postman con newman...")
    coleccion = os.path.join(BACKEND, "postman", "AutoPrime.postman_collection.json")
    entorno = os.path.join(BACKEND, "postman", "AutoPrime.postman_environment.json")
    salida_newman = cabeza_y_cola(correr(
        'npx --no-install newman run "%s" -e "%s" --reporters cli '
        '--reporter-cli-no-banner --color off' % (coleccion, entorno),
        cwd=RAIZ, limite=100000))

    print("    inyeccion SQL...")
    salida_sql = inyecciones(token)

    print("    fuerza bruta...")
    salida_bruta = fuerza_bruta()

    print("    contenido del Excel...")
    salida_excel = contenido_excel(token)

    print("    despliegue en produccion...")
    salida_cabeceras = cabeceras_produccion()
    salida_despliegue = despliegue()

    fichas = [
        ("q17-pruebas-pytest", "PRUEBAS", "Pruebas automáticas del backend",
         "Toda la lógica nueva con sus pruebas: ventas, facturas, informes, "
         "PQR, chat, números en letras y el endurecimiento.",
         "$ venv\\Scripts\\python -m pytest\n" + salida_pytest
         + "\n\n$ y que cubren, por archivo\n" + desglose),

        ("q18-postman-newman", "POSTMAN", "La batería de Postman, ejecutada",
         "La misma colección que se entrega, corrida desde la línea de "
         "órdenes con newman. Se genera del OpenAPI de la propia API, así "
         "que la lista de rutas no puede quedarse atrás.",
         "$ newman run AutoPrime.postman_collection.json\n" + salida_newman),

        ("q19-inyeccion-sql", "SEGURIDAD", "Inyección SQL: el texto es texto",
         "Cinco cargas clásicas contra el buscador, que es el sitio donde "
         "se intentaría. Ninguna llega a la sentencia.",
         salida_sql),

        ("q20-fuerza-bruta", "SEGURIDAD", "Probar contraseñas, frenado",
         "El login corta a los ocho intentos por minuto, contados por origen "
         "y por correo.",
         salida_bruta),

        ("q21-excel-seguro", "INFORMES", "Qué lleva dentro el Excel",
         "Cuatro hojas, gráficas incrustadas, y ni una sola celda con texto "
         "de la gente convertida en fórmula.",
         salida_excel),

        ("q22-cabeceras", "SEGURIDAD", "Cabeceras del despliegue real",
         "Leídas del servidor en producción, no de local: es donde importan.",
         salida_cabeceras),

        ("q23-despliegue", "DESPLIEGUE", "El servicio, en producción",
         "Las dos rutas de estado: la que decide si el servicio vive y la "
         "que diagnostica.",
         salida_despliegue),
    ]

    nav = Navegador()
    try:
        for nombre, req, titulo, nota, cuerpo in fichas:
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(PLANTILLA.format(
                    titulo=html.escape(titulo), req=req,
                    nota=html.escape(nota), cuerpo=resaltar(cuerpo)))
            nav.ir("file:///" + tmp.replace("\\", "/"), espera=1.6)
            nav.capturar(nombre, pagina_entera=True)
    finally:
        nav.cerrar()
        if os.path.exists(tmp):
            os.remove(tmp)

    print()
    print("  %d evidencias de consola en evidencias/capturas-quinta/" % len(fichas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
