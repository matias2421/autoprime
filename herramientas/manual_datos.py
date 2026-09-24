# -*- coding: utf-8 -*-
"""Lee del proyecto lo que el Manual Técnico tiene que contar.

Las tablas, los endpoints, las dependencias y las variables de entorno no se
transcriben: se leen de donde viven. Un diccionario de datos copiado a mano
empieza siendo correcto y deja de serlo en cuanto alguien añade una columna,
y el manual sigue diciendo lo de antes sin que nadie lo note.

Aquí, volver a lanzar el generador basta para ponerlo al día.
"""

import io
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(RAIZ, "backend")
sys.path.insert(0, BACKEND)


# ---------------------------------------------------------------------------
# Modelo de datos
# ---------------------------------------------------------------------------
# Para qué sirve cada tabla. Es lo único de esta sección que no se puede
# deducir del esquema: SQLAlchemy sabe que `pqr.numero` es un VARCHAR(20),
# pero no que es el radicado que se le da al cliente.
PROPOSITOS = {
    "roles": "Los tres perfiles del sistema: administrador, empleado y cliente.",
    "permisos": "Catálogo de acciones nombradas. Ver la nota del apartado 7.3.",
    "usuarios": "Toda persona que entra al sistema, sea del atelier o cliente.",
    "productos": "El catálogo de vehículos, con su ficha técnica y su estado.",
    "servicios": "Lo que se puede agendar: peritaje, prueba de manejo, taller.",
    "citas": "Una franja reservada por un cliente para un servicio.",
    "ventas": "La cabecera de una operación comercial y su estado de cobro.",
    "detalle_ventas": "Cada línea de una venta, con copia de precio y descripción.",
    "facturas": "El documento fiscal que se emite a partir de una venta.",
    "detalle_facturas": "Las líneas de la factura, congeladas al emitirla.",
    "pqr": "Peticiones, quejas y reclamos, con su radicado y su respuesta.",
    "conversaciones": "Un hilo de chat con el asistente.",
    "mensajes": "Cada turno dentro de una conversación.",
}


def entidades():
    """Devuelve el esquema tal como lo declara SQLAlchemy."""
    from app.core.base_datos import Base
    from app.models import autoprime  # noqa: F401 — registra las tablas

    salida = []
    for tabla in Base.metadata.sorted_tables:
        columnas = []
        for c in tabla.columns:
            ajena = list(c.foreign_keys)
            columnas.append({
                "nombre": c.name,
                "tipo": str(c.type),
                "nulo": bool(c.nullable),
                "pk": bool(c.primary_key),
                "unica": bool(c.unique),
                "fk": ajena[0].target_fullname if ajena else None,
            })
        salida.append({
            "tabla": tabla.name,
            "proposito": PROPOSITOS.get(tabla.name, ""),
            "columnas": columnas,
        })
    return salida


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def endpoints():
    """Los endpoints, agrupados por etiqueta, leídos del propio OpenAPI.

    Es la misma fuente de la que se genera la colección de Postman: si se
    añade una ruta, aparece en los dos sitios sin tocar nada.
    """
    from app.main import app

    api = app.openapi()
    grupos = {}
    for ruta, metodos in api["paths"].items():
        for metodo, operacion in metodos.items():
            if metodo not in ("get", "post", "put", "patch", "delete"):
                continue
            etiqueta = (operacion.get("tags") or ["Sistema"])[0]
            grupos.setdefault(etiqueta, []).append({
                "metodo": metodo.upper(),
                "ruta": ruta,
                "resumen": operacion.get("summary", ""),
                "protegido": bool(operacion.get("security")),
            })
    for lista in grupos.values():
        lista.sort(key=lambda o: (o["ruta"], o["metodo"]))
    return dict(sorted(grupos.items())), api["info"]["version"]


# ---------------------------------------------------------------------------
# Dependencias y configuración
# ---------------------------------------------------------------------------
def dependencias_backend():
    """Paquete y versión de requirements.txt, sin los comentarios."""
    ruta = os.path.join(BACKEND, "requirements.txt")
    salida = []
    for linea in io.open(ruta, encoding="utf-8"):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        partida = re.split(r"==", linea, maxsplit=1)
        salida.append((partida[0], partida[1] if len(partida) > 1 else "—"))
    return salida


def dependencias_frontend():
    ruta = os.path.join(RAIZ, "frontend", "package.json")
    paquete = json.load(io.open(ruta, encoding="utf-8"))
    normales = sorted(paquete.get("dependencies", {}).items())
    desarrollo = sorted(paquete.get("devDependencies", {}).items())
    return normales, desarrollo


# Qué hace cada variable. El .env.example trae los nombres; el para qué es lo
# que hace falta para poder poner el proyecto en marcha sin adivinar.
SENTIDO_VARIABLES = {
    "ENTORNO": ("desarrollo | produccion. Decide si se envían las cabeceras "
                "HSTS y si la documentación queda publicada.", "desarrollo"),
    "ORIGENES_PERMITIDOS": ("Dominios del frontend a los que la API responde. "
                            "Sin esto el navegador bloquea cada petición.",
                            "http://localhost:5173"),
    "DB_HOST": ("Servidor de MySQL.", "localhost"),
    "DB_PORT": ("Puerto de MySQL.", "3306"),
    "DB_USER": ("Usuario de la base.", "root"),
    "DB_PASSWORD": ("Su contraseña. Nunca se escribe en el código.", "(vacío en XAMPP)"),
    "DB_NAME": ("Nombre del esquema.", "autoprime"),
    "DB_SSL_CA": ("Ruta al certificado de la autoridad, para cifrar el enlace "
                  "con una base remota.", "(vacío en local)"),
    "DB_SSL_CA_CONTENIDO": ("El mismo certificado pegado como texto, para "
                            "proveedores donde no se pueden subir archivos.", "(vacío)"),
    "SECRET_KEY": ("Clave con la que se firman los JWT. Cambiarla invalida "
                   "todas las sesiones.", "(obligatoria)"),
    "ALGORITMO_JWT": ("Algoritmo de firma.", "HS256"),
    "HORAS_EXPIRACION_TOKEN": ("Duración de la sesión.", "8"),
    "MINUTOS_EXPIRACION_RECUPERACION": ("Validez del enlace de recuperación.", "30"),
    "BCRYPT_ROUNDS": ("Coste del hash de contraseña.", "12"),
    "URL_FRONTEND": ("Base de los enlaces que se envían por correo.",
                     "http://localhost:5173"),
    "SMTP_HOST": ("Servidor de correo saliente.", "smtp.gmail.com"),
    "SMTP_PUERTO": ("Su puerto.", "587"),
    "SMTP_USUARIO": ("Cuenta remitente.", "(opcional)"),
    "SMTP_PASSWORD": ("Su contraseña de aplicación.", "(opcional)"),
    "SMTP_REMITENTE": ("Nombre y dirección que ve quien recibe.", "(opcional)"),
    "GROQ_API_KEY": ("Clave del modelo que responde en el asistente. Sin "
                     "ella el chat avisa y ofrece los canales de contacto.", "(opcional)"),
    "GROQ_MODELO": ("Modelo a usar.", "(por defecto el del código)"),
    "URL_FESTIVOS": ("Calendario de festivos colombianos, para la agenda.",
                     "(por defecto el del código)"),
}


def variables_entorno():
    ruta = os.path.join(BACKEND, ".env.example")
    vistas, salida = set(), []
    for linea in io.open(ruta, encoding="utf-8"):
        nombre = re.match(r"^([A-Z_]+)\s*=", linea.strip())
        if not nombre or nombre.group(1) in vistas:
            continue
        clave = nombre.group(1)
        vistas.add(clave)
        sentido, ejemplo = SENTIDO_VARIABLES.get(clave, ("", ""))
        salida.append((clave, sentido, ejemplo))
    return salida


# ---------------------------------------------------------------------------
def tamano():
    """Cuántos archivos y líneas tiene cada parte. Da escala al lector."""
    def contar(carpeta, extensiones):
        archivos = lineas = 0
        for base, _, nombres in os.walk(carpeta):
            if any(p in base for p in ("__pycache__", "node_modules", "venv")):
                continue
            for nombre in nombres:
                if not nombre.endswith(extensiones):
                    continue
                archivos += 1
                with io.open(os.path.join(base, nombre), encoding="utf-8",
                             errors="replace") as f:
                    lineas += sum(1 for _ in f)
        return archivos, lineas

    backend = contar(os.path.join(BACKEND, "app"), (".py",))
    frontend = contar(os.path.join(RAIZ, "frontend", "src"), (".jsx", ".js"))
    pruebas = contar(os.path.join(BACKEND, "tests"), (".py",))
    return {"backend": backend, "frontend": frontend, "pruebas": pruebas}


# Se calcula al importar: el generador solo tiene que leerlo.
ENTIDADES = entidades()
ENDPOINTS, VERSION_API = endpoints()
DEPENDENCIAS_BACKEND = dependencias_backend()
DEPENDENCIAS_FRONTEND = dependencias_frontend()
VARIABLES_ENTORNO = variables_entorno()
TAMANO = tamano()
