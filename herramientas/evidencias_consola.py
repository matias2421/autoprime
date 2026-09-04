# -*- coding: utf-8 -*-
"""Convierte en PNG las evidencias que no son pantallas de la aplicación.

Varios requisitos no se demuestran con una captura del sitio: la estructura de
carpetas, el entorno de Python, las tablas de MySQL o la respuesta cruda de la
API ante un intento sin permiso. Este script **ejecuta de verdad** cada
comprobación, recoge su salida tal cual y la dibuja como una ventana de
terminal para poder pegarla junto al resto.

Nada está escrito a mano: si una comprobación deja de pasar, la imagen lo
enseña. Esa es la diferencia entre una evidencia y una ilustración.

    backend/venv/Scripts/python herramientas/evidencias_consola.py
"""

import html
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capturas import SALIDA, Navegador  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "http://127.0.0.1:8000"
MYSQL = r"C:\xampp\mysql\bin\mysql.exe"
PY = os.path.join(RAIZ, "backend", "venv", "Scripts", "python.exe")


# ---------------------------------------------------------------------------
# Recolección
# ---------------------------------------------------------------------------
def correr(orden, cwd=RAIZ, limite=40) -> str:
    """Ejecuta y devuelve la salida recortada a un número de líneas."""
    r = subprocess.run(
        orden, cwd=cwd, capture_output=True, text=True, shell=isinstance(orden, str),
        encoding="utf-8", errors="replace",
    )
    salida = (r.stdout or "") + (r.stderr or "")
    lineas = salida.strip().splitlines()
    if len(lineas) > limite:
        lineas = lineas[:limite] + [f"... ({len(salida.splitlines()) - limite} líneas más)"]
    return "\n".join(lineas)


def sql(consulta: str) -> str:
    return correr([MYSQL, "-u", "root", "--table", "-e", consulta])


def http(metodo: str, ruta: str, cuerpo=None, token=None):
    """Devuelve la petición y la respuesta tal como viajan, para poder verlas."""
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    pet = urllib.request.Request(API + ruta, data=datos, method=metodo)
    if datos is not None:
        pet.add_header("Content-Type", "application/json")
    if token:
        pet.add_header("Authorization", f"Bearer {token}")

    lineas = [f"$ {metodo} {ruta}"]
    if token:
        lineas.append(f"  Authorization: Bearer {token[:28]}...")
    if cuerpo is not None:
        lineas.append("  " + json.dumps(cuerpo, ensure_ascii=False))
    lineas.append("")

    try:
        with urllib.request.urlopen(pet, timeout=15) as r:
            lineas.append(f"HTTP {r.status}")
            lineas.append(json.dumps(json.loads(r.read().decode()), indent=2,
                                     ensure_ascii=False)[:900])
    except urllib.error.HTTPError as e:
        lineas.append(f"HTTP {e.code}")
        lineas.append(json.dumps(json.loads(e.read().decode()), indent=2,
                                 ensure_ascii=False)[:900])
    return "\n".join(lineas)


def token_de(correo: str, password: str) -> str:
    pet = urllib.request.Request(
        API + "/api/auth/login",
        data=json.dumps({"correo": correo, "password": password}).encode(),
    )
    pet.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(pet, timeout=15) as r:
        return json.loads(r.read().decode())["token"]


def contar_hooks() -> str:
    """Cuenta en cuántos archivos aparece cada hook.

    Se recorre el árbol desde Python y no con una orden del sistema: el
    intérprete que ejecuta esto no es siempre el mismo, y una expansión de
    variables que funciona en una consola devuelve cualquier cosa en otra.
    La primera versión de esta ficha acabó listando el disco entero.
    """
    import re

    hooks = ["useState", "useEffect", "useContext", "useRef", "useMemo",
             "useCallback"]
    cuenta = {h: 0 for h in hooks}
    base = os.path.join(RAIZ, "frontend", "src")

    for carpeta, _, archivos in os.walk(base):
        for archivo in archivos:
            if not archivo.endswith((".js", ".jsx")):
                continue
            contenido = open(os.path.join(carpeta, archivo), encoding="utf-8",
                             errors="replace").read()
            for h in hooks:
                # Con limites de palabra, para que `useState` no cuente
                # por aparecer dentro de otro identificador.
                if re.search(r"\b" + h + r"\b", contenido):
                    cuenta[h] += 1

    ancho = max(len(h) for h in hooks)
    return "\n".join(
        f"  {h.ljust(ancho)}  {cuenta[h]:>2} archivos" for h in hooks
    )


def arbol(base: str, prefijo: str = "", profundidad: int = 2) -> list[str]:
    """Dibuja el árbol de una carpeta, sin ruido."""
    if profundidad == 0:
        return []
    ignorar = {"__pycache__", "venv", "node_modules", ".git", "dist"}
    entradas = sorted(
        e for e in os.listdir(base)
        if e not in ignorar and not e.startswith(".")
    )
    lineas = []
    for i, nombre in enumerate(entradas):
        ultimo = i == len(entradas) - 1
        rama = "└── " if ultimo else "├── "
        ruta = os.path.join(base, nombre)
        lineas.append(prefijo + rama + nombre + ("/" if os.path.isdir(ruta) else ""))
        if os.path.isdir(ruta):
            lineas += arbol(ruta, prefijo + ("    " if ultimo else "│   "),
                            profundidad - 1)
    return lineas


# ---------------------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------------------
PLANTILLA = """<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Inter:wght@500;600&display=swap">
<style>
  body {{ margin:0; padding:26px; background:#020204;
         font-family:"Inter",system-ui,sans-serif; }}
  .marco {{ border:1px solid #22222b; background:#0d0d13; overflow:hidden; }}
  .barra {{ display:flex; align-items:center; gap:10px;
            padding:11px 15px; background:#13131b;
            border-bottom:1px solid #22222b; }}
  .punto {{ width:9px; height:9px; background:#3c3c47; }}
  .titulo {{ margin-left:6px; font-size:12px; font-weight:600; color:#ffffff;
             letter-spacing:.04em; }}
  .req {{ margin-left:auto; font-family:"JetBrains Mono",monospace; font-size:11px;
          font-weight:500; color:#829fb0; letter-spacing:.1em; }}
  .nota {{ padding:11px 18px; font-size:12.5px; color:#8f8f93;
           border-bottom:1px solid #22222b; background:#07070b; }}
  pre {{ margin:0; padding:18px; font-family:"JetBrains Mono",monospace;
         font-size:12.5px; line-height:1.6; color:#b6b6b6;
         white-space:pre; overflow-x:auto; }}
  .cmd {{ color:#ffffff; }}
  .ok {{ color:#7fd1a3; }}
  .mal {{ color:#e8907f; }}
</style>
<div class="marco">
  <div class="barra">
    <span class="punto"></span><span class="punto"></span><span class="punto"></span>
    <span class="titulo">{titulo}</span>
    <span class="req">{req}</span>
  </div>
  <div class="nota">{nota}</div>
  <pre>{cuerpo}</pre>
</div>
"""


def resaltar(texto: str) -> str:
    """Marca las líneas de orden y los códigos de estado."""
    salida = []
    for linea in html.escape(texto).splitlines():
        if linea.startswith("$ ") or linea.startswith("&gt; "):
            salida.append(f'<span class="cmd">{linea}</span>')
        elif linea.startswith("HTTP 2") or " OK " in linea or "0 fallidas" in linea:
            salida.append(f'<span class="ok">{linea}</span>')
        elif linea.startswith("HTTP 4") or "FALLA" in linea:
            salida.append(f'<span class="mal">{linea}</span>')
        else:
            salida.append(linea)
    return "\n".join(salida)


def main() -> int:
    os.makedirs(SALIDA, exist_ok=True)
    tmp = os.path.join(SALIDA, "_render.html")

    t_admin = token_de("admin@autoprime.com.co", "Admin2026!")
    t_cliente = token_de("cliente@autoprime.com.co", "Cliente2026!")

    partes = t_admin.split(".")
    import base64
    def trozo(p):
        p += "=" * (-len(p) % 4)
        return json.dumps(json.loads(base64.urlsafe_b64decode(p)), indent=2)

    fichas = [
        ("req-02-estructura", "REQ-02", "Estructura del proyecto",
         "Frontend y backend separados; el backend con su subcarpeta app/.",
         "$ tree proyecto-final\n" + "\n".join(arbol(RAIZ, profundidad=1))
         + "\n\n$ tree backend/app\n"
         + "\n".join(arbol(os.path.join(RAIZ, "backend", "app"), profundidad=1))),

        ("req-03-entorno", "REQ-03", "Entorno virtual y dependencias",
         "Dependencias principales instaladas en el entorno del proyecto.",
         "$ venv\\Scripts\\python --version\n" + correr([PY, "--version"])
         + "\n\n$ venv\\Scripts\\python -m pip list\n"
         + correr(f'"{PY}" -m pip list | findstr /I "fastapi uvicorn SQLAlchemy PyMySQL '
                  'bcrypt pydantic jose"')),

        ("req-04-tablas", "REQ-04", "Tablas de la base de datos",
         "Las siete tablas del esquema relacional, incluidas roles y permisos.",
         "$ mysql -u root -e \"SHOW TABLES FROM autoprime;\"\n"
         + sql("SHOW TABLES FROM autoprime;")),

        ("req-05-tabla-usuarios", "REQ-05", "Estructura de la tabla usuarios",
         "Todos los campos que pide el entregable. La contraseña solo como hash.",
         "$ mysql -u root -e \"DESCRIBE autoprime.usuarios;\"\n"
         + sql("DESCRIBE autoprime.usuarios;")),

        ("req-22-hash", "REQ-22", "Contraseñas guardadas con bcrypt",
         "Ninguna contraseña en texto plano. Misma clave, hash distinto: cada "
         "cuenta lleva su propia sal.",
         "$ mysql -u root -e \"SELECT correo, LEFT(password_hash,38) ...\"\n"
         + sql("SELECT correo, rol_id, LEFT(password_hash,38) AS hash "
               "FROM autoprime.usuarios LIMIT 5;")),

        ("req-11-jwt", "REQ-11", "Contenido del JSON Web Token",
         "El token que emite FastAPI al iniciar sesión, descodificado. Lleva el "
         "usuario, su rol y la caducidad; la firma es lo que impide alterarlo.",
         "$ token emitido por POST /api/auth/login\n\n"
         + "cabecera:\n" + trozo(partes[0]) + "\n\ncarga:\n" + trozo(partes[1])
         + f"\n\nfirma: {partes[2][:40]}... (no descodificable: es la prueba)"),

        ("req-12-roles", "REQ-12", "El backend decide el permiso",
         "El mismo endpoint, con el token de un cliente. La interfaz ya lo "
         "oculta, pero la autorización de verdad ocurre aquí.",
         http("GET", "/api/usuarios", token=t_cliente)),

        ("req-08-revalidacion", "REQ-08", "La API revalida por su cuenta",
         "Petición hecha sin pasar por el formulario de React. La regla de "
         "correo único se aplica igual.",
         http("POST", "/api/auth/registro", {
             "nombre": "Prueba", "apellido": "Duplicada", "tipoDocumento": "CC",
             "numeroDocumento": "1088111222", "direccion": "Calle 1 # 2-3",
             "telefono": "3001112233", "correo": "admin@autoprime.com.co",
             "password": "Prueba2026!", "confirmarPassword": "Prueba2026!"})),

        ("req-13-hooks", "REQ-13", "Hooks de React",
         "Siete hooks propios más los de la biblioteca, repartidos por la "
         "aplicación.",
         "$ ls frontend/src/hooks\n"
         + "\n".join(sorted(os.listdir(os.path.join(RAIZ, "frontend", "src", "hooks"))))
         + "\n\n$ archivos que usan cada hook de React\n"
         + contar_hooks()),

        ("req-23-entorno", "REQ-23", "Variables de entorno",
         "La plantilla se publica; el .env real con las claves queda fuera del "
         "repositorio.",
         "$ type backend\\.env.example\n"
         + open(os.path.join(RAIZ, "backend", ".env.example"), encoding="utf-8").read()
         + "\n$ git check-ignore -v backend/.env\n"
         + correr("git check-ignore -v backend/.env")),

        ("req-26-pruebas", "REQ-26", "Pruebas de los endpoints",
         "81 comprobaciones de extremo a extremo por HTTP, con los cinco "
         "métodos: GET, POST, PUT, PATCH y DELETE.",
         "$ venv\\Scripts\\python pruebas_api.py\n"
         + correr(f'"{PY}" pruebas_api.py',
                  cwd=os.path.join(RAIZ, "backend"), limite=34)),
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
    print(f"  {len(fichas)} evidencias de consola en evidencias/capturas/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
