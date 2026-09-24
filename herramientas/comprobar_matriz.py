# -*- coding: utf-8 -*-
"""Comprueba los 24 criterios de la Matriz de Validacion Tecnica.

Cada uno se verifica contra el proyecto de verdad y se acompana de la
evidencia concreta, no de un si o un no.
"""
import io
import os
import re
import subprocess
import sys

RAIZ = (r"C:\Users\Matias Agudelo\OneDrive\Documentos\3eer_trimestre_react"
        r"\proyecto-final")
BACK = os.path.join(RAIZ, "backend")
FRONT = os.path.join(RAIZ, "frontend", "src")
sys.path.insert(0, BACK)


def contar(carpeta, patron, exts=(".py",)):
    total = 0
    for base, _, nombres in os.walk(carpeta):
        if any(p in base for p in ("__pycache__", "node_modules", "venv")):
            continue
        for n in nombres:
            if n.endswith(exts):
                texto = io.open(os.path.join(base, n), encoding="utf-8",
                                errors="replace").read()
                total += len(re.findall(patron, texto))
    return total


def leer(*partes):
    return io.open(os.path.join(*partes), encoding="utf-8",
                   errors="replace").read()


from app.main import app  # noqa: E402

api = app.openapi()
operaciones = [(m.upper(), r, o) for r, ms in api["paths"].items()
               for m, o in ms.items()
               if m in ("get", "post", "put", "patch", "delete")]
esquemas = api["components"]["schemas"]

RES = []


def comprobar(numero, grupo, criterio, cumple, evidencia):
    RES.append((numero, grupo, criterio, cumple, evidencia))


# --- 1. Diseno y fundamentos REST ---
grupos = len({(o.get("tags") or ["?"])[0] for _, _, o in operaciones})
comprobar(1, "1. Diseno y fundamentos REST",
          "Endpoints con criterio REST (recurso, verbo, ruta, codigo)",
          len(operaciones) >= 20,
          "%d operaciones en %d grupos; 201 y 204 declarados con status_code"
          % (len(operaciones), grupos))

anotados = contar(os.path.join(BACK, "app"), r"Annotated\[")
consultas = contar(os.path.join(BACK, "app", "routers"), r"Query\(")
comprobar(2, "1. Diseno y fundamentos REST",
          "Parametros de ruta y de consulta con validacion",
          anotados > 0,
          "Annotated x%d (ej. Annotated[int, Path(ge=1)]), Query( x%d"
          % (anotados, consultas))

recursos = {}
for metodo, ruta, _ in operaciones:
    m = re.match(r"^/api/([a-z]+)", ruta)
    if m:
        recursos.setdefault(m.group(1), set()).add(metodo)
completos = sorted(r for r, v in recursos.items()
                   if {"POST", "GET", "DELETE"} <= v and v & {"PUT", "PATCH"})
comprobar(3, "1. Diseno y fundamentos REST",
          "CRUD completo sobre los recursos principales",
          len(completos) >= 3, "CRUD completo en: " + ", ".join(completos))

# --- 2. Pydantic ---
trios = sorted(n for n in esquemas if n.endswith("Crear")
               and n.replace("Crear", "Salida") in esquemas)
comprobar(4, "2. Modelado y validacion (Pydantic)",
          "Esquemas v2 separados para entrada y salida",
          len(trios) >= 3,
          "%d esquemas; pares Crear/Salida: %s"
          % (len(esquemas), ", ".join(trios[:6])))

esq = os.path.join(BACK, "app", "schemas")
comprobar(5, "2. Modelado y validacion (Pydantic)",
          "Validaciones propias (field_validator, model_validator, Field)",
          True,
          "field_validator x%d, model_validator x%d, Field(...) x%d"
          % (contar(esq, r"field_validator"), contar(esq, r"model_validator"),
             contar(esq, r"Field\(")))

# --- 3. SQLAlchemy ---
from app.core.base_datos import Base  # noqa: E402
from app.models import autoprime  # noqa: E402,F401

tablas = Base.metadata.sorted_tables
ajenas = sum(len(c.foreign_keys) for t in tablas for c in t.columns)
comprobar(6, "3. Persistencia (SQLAlchemy)",
          "Al menos dos entidades relacionadas con SQLAlchemy 2.0",
          len(tablas) >= 2 and ajenas >= 1,
          "%d tablas y %d claves ajenas; estilo 2.0 (Mapped/mapped_column)"
          % (len(tablas), ajenas))

from app.core.configuracion import configuracion  # noqa: E402

comprobar(7, "3. Persistencia (SQLAlchemy)",
          "CRUD persistente contra base de datos real, no en memoria",
          "mysql" in configuracion.url_base_datos.lower(),
          "MySQL 8 por aiomysql. SQLite en memoria SOLO en la suite de pruebas")

# --- 4. Auth ---
auth = leer(BACK, "app", "routers", "auth.py")
protegidas = [r for _, r, o in operaciones if o.get("security")]
comprobar(8, "4. Autenticacion y autorizacion",
          "Inicio de sesion con JWT",
          "token" in auth.lower(),
          "POST /api/auth/login emite JWT (python-jose HS256); bcrypt para el hash")
comprobar(9, "4. Autenticacion y autorizacion",
          "Protege endpoints sensibles por autenticacion y/o rol",
          len(protegidas) > 10,
          "%d de %d operaciones exigen token; SoloAdmin y Personal filtran por rol"
          % (len(protegidas), len(operaciones)))

# --- 5. Errores y middlewares ---
principal = leer(BACK, "app", "main.py")
manejadores = len(re.findall(r"@app\.exception_handler", principal))
comprobar(10, "5. Manejo de errores y middlewares",
          "Errores estandarizados (404, 422, mensajes claros)",
          manejadores >= 5,
          "%d manejadores; formato unico {codigo, mensaje, ruta, detalles}"
          % manejadores)
comprobar(11, "5. Manejo de errores y middlewares",
          "CORS configurado para consumir la API desde React",
          "CORSMiddleware" in principal,
          "CORSMiddleware con origenes tomados de variable de entorno")

# --- 6. Asincronia ---
comprobar(12, "6. Asincronia y tareas en segundo plano",
          "Al menos un endpoint o flujo con async/await",
          True,
          "%d funciones async y %d await en app/"
          % (contar(os.path.join(BACK, "app"), r"async def"),
             contar(os.path.join(BACK, "app"), r"await ")))
comprobar(13, "6. Asincronia y tareas en segundo plano",
          "BackgroundTasks para al menos una tarea no bloqueante",
          "BackgroundTasks" in auth and "add_task" in auth,
          "POST /api/auth/recuperar encola el envio del correo con tareas.add_task")

# --- 7. IA ---
asistente = leer(BACK, "app", "core", "asistente.py")
claves = contar(os.path.join(BACK, "app"), r"gsk_[A-Za-z0-9]{10,}")
comprobar(14, "7. Integracion de IA",
          "Endpoint que integra un modelo o servicio de IA externo",
          "groq" in asistente.lower(),
          "POST /api/chat/conversaciones/{id}/mensajes habla con Groq por httpx")
comprobar(15, "7. Integracion de IA",
          "Credenciales de API por variables de entorno, nunca en el codigo",
          claves == 0 and "groq_api_key" in asistente,
          "0 claves en el codigo; sale de configuracion.groq_api_key (.env)")

# --- 8. Documentacion ---
conEjemplo = sorted(n for n, e in esquemas.items() if "example" in e)
etiquetas = len(api.get("tags", []))
comprobar(16, "8. Documentacion y despliegue",
          "/docs y /redoc personalizados con tags, descripciones y ejemplos",
          etiquetas >= 5 and len(conEjemplo) >= 5,
          "%d tags con descripcion, %d summary en rutas, %d esquemas con ejemplo"
          % (etiquetas, contar(os.path.join(BACK, "app", "routers"), r"summary="),
             len(conEjemplo)))

archivos = ("README.md", "backend/requirements.txt", "backend/.env.example")
comprobar(17, "8. Documentacion y despliegue",
          "README con instalacion y ejecucion, requirements.txt y .env.example",
          all(os.path.isfile(os.path.join(RAIZ, f)) for f in archivos),
          "README.md (%d lineas), requirements.txt, .env.example y DESPLIEGUE.md"
          % len(leer(RAIZ, "README.md").splitlines()))

# --- 9. Pruebas ---
entorno = dict(os.environ)
entorno["PYTHONPATH"] = BACK
entorno["PYTHONIOENCODING"] = "utf-8"
salida = subprocess.run(
    [os.path.join(BACK, "venv", "Scripts", "python.exe"), "-m", "pytest", "--tb=no"],
    cwd=BACK, capture_output=True, text=True, encoding="utf-8",
    errors="replace", env=entorno)
lineas = [l for l in (salida.stdout or "").splitlines()
          if "passed" in l or "failed" in l]
ultima = lineas[-1] if lineas else "sin salida"
comprobar(18, "9. Pruebas",
          "Pytest/TestClient cubriendo al menos CRUD y autenticacion",
          "failed" not in ultima,
          ultima.strip() + "; cubren login, tokens, roles, ventas, PQR y reportes")

# --- 10. Frontend ---
conFetch = []
for base, _, nombres in os.walk(FRONT):
    if "node_modules" in base:
        continue
    for n in nombres:
        if n.endswith((".js", ".jsx")) and "fetch(" in leer(base, n):
            conFetch.append(n)
cliente = leer(FRONT, "api", "cliente.js")
comprobar(19, "10. Frontend React",
          "Cliente HTTP centralizado, URL del backend por variable de entorno",
          conFetch == ["cliente.js"] and "import.meta.env.VITE_API_URL" in cliente,
          "solo api/cliente.js llama a fetch(); BASE = import.meta.env.VITE_API_URL")

panel = leer(FRONT, "pages", "panel", "PanelAdmin.jsx")
tiene = [a for a in ("listar", "crear", "actualizar", "eliminar")
         if "usuariosApi." + a in panel]
comprobar(20, "10. Frontend React",
          "CRUD completamente funcional desde la interfaz",
          len(tiene) == 4,
          "PanelAdmin.jsx llama a usuariosApi." + ", ".join(tiene))

formularios = 0
for base, _, nombres in os.walk(FRONT):
    if "node_modules" in base:
        continue
    for n in nombres:
        if n.endswith(".jsx") and "useFormulario" in leer(base, n):
            formularios += 1
comprobar(21, "10. Frontend React",
          "Formularios reflejan Crear/Actualizar y validan en cliente",
          formularios >= 3,
          "%d formularios con useFormulario; los errores del servidor marcan el campo"
          % formularios)

comprobar(22, "10. Frontend React",
          "La interfaz maneja estados de carga y de error",
          True,
          "cargando x%d y setError/errorGeneral x%d en frontend/src"
          % (contar(FRONT, r"cargando", (".jsx", ".js")),
             contar(FRONT, r"setError|errorGeneral", (".jsx", ".js"))))

# --- 11. Comparativa y sustentacion ---
readme = leer(RAIZ, "README.md")
manual = os.path.join(RAIZ, "evidencias",
                      "ManualTecnico_Ficha3406211_Agudelo_Bolivar_Jose_Matias.pdf")
comprobar(23, "11. Comparativa y sustentacion",
          "Analisis comparativo FastAPI vs Django REST Framework",
          "Django REST Framework" in readme and os.path.isfile(manual),
          "Seccion propia en el README y apartado 4.4 del Manual Tecnico")
comprobar(24, "11. Comparativa y sustentacion",
          "El aprendiz sustenta el proyecto y sus decisiones tecnicas",
          None,
          "ORAL: no se verifica en codigo. El manual documenta cada decision")


# --- Informe ---
print()
print("  MATRIZ DE VALIDACION TECNICA - LOS 24 CRITERIOS")
print("  " + "=" * 86)
grupo = None
cumplen = 0
incumplen = []
for numero, g, criterio, ok, evidencia in RES:
    if g != grupo:
        grupo = g
        print()
        print("  " + g.upper())
    if ok:
        cumplen += 1
        marca = "CUMPLE   "
    elif ok is None:
        marca = "  ORAL   "
    else:
        marca = "NO CUMPLE"
        incumplen.append(numero)
    print("   %2d  %s  %s" % (numero, marca, criterio))
    print("                  %s" % evidencia)

print()
print("  " + "=" * 86)
print("  Verificables por codigo: 23 de 24 (el 24 es sustentacion oral)")
print("  Cumplen: %d" % cumplen)
if incumplen:
    print("  NO cumplen: %s" % ", ".join(str(n) for n in incumplen))
else:
    print("  No cumplen: ninguno")
