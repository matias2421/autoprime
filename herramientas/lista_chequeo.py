# -*- coding: utf-8 -*-
"""Rellena la lista de chequeo del SENA en formato Excel, con las evidencias.

Reproduce el instrumento que entregó el instructor —mismas secciones, mismas
columnas, mismos colores, tomados del PDF original— y pega cada captura en su
casilla «Espacio para Evidencia».

El PDF que se recibió es un escaneo sin texto, así que no se puede rellenar
encima: hay que reconstruir la hoja. A cambio, al ser un .xlsx de verdad, el
instructor puede escribir en las casillas que le corresponden y el porcentaje
de avance se recalcula solo.

    python herramientas/lista_chequeo.py
"""

import os
import sys

import xlsxwriter
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURAS = os.path.join(RAIZ, "evidencias", "capturas")
LOGO = os.path.join(RAIZ, "evidencias", "plantilla", "logo-1.png")
DESTINO = os.path.join(RAIZ, "evidencias", "Lista_Chequeo_Cuarto_Avance_AutoPrime.xlsx")

# Colores muestreados del PDF original, no elegidos a ojo.
VERDE_OSCURO = "#1D5900"
VERDE = "#3AAA00"
VERDE_CLARO = "#E9F2E8"
AZUL_CLARO = "#DBE6F0"
GRIS = "#F2F2F2"
BLANCO = "#FFFFFF"
BORDE = "#808080"

# Anchos en caracteres de Excel, derivados de medir las columnas en el PDF.
# La de evidencia se ensancha un poco respecto al original: a su ancho exacto
# las capturas de consola quedaban ilegibles, y esa columna existe justamente
# para que se vean.
ANCHOS = {"A": 14.5, "B": 25.5, "C": 45.0, "D": 70.0, "E": 32.0}

ANCHO_IMAGEN = 480          # px a los que se escala cada captura
ALTO_MAXIMO_FILA = 409      # el máximo que admite Excel, en puntos


# --------------------------------------------------------------------------
# El instrumento, transcrito literalmente del PDF del instructor.
# --------------------------------------------------------------------------
REQUISITOS = [
    ("REQ-01", "Arquitectura Tecnológica",
     "Integración Full Stack: Frontend React + Vite consumiendo endpoints "
     "FastAPI en formato JSON mediante fetch, Axios u otra librería. Conexión "
     "Backend a Base de Datos relacional SQL.",
     "req-01-portada",
     "La portada servida por Vite. Las llamadas al puerto 8000 devuelven JSON."),

    ("REQ-02", "Carpeta Backend con FastAPI",
     "Organización clara del proyecto separando Frontend y Backend. Estructura "
     "sugerida para el backend con subcarpeta app/ y dependencias.",
     "req-02-estructura",
     "Árbol del proyecto y del paquete app/ (core, models, schemas, crud, "
     "routers). El backend en Express queda en backend-express/."),

    ("REQ-03", "Entorno FastAPI",
     "Configuración y activación de entorno virtual Python (venv) e "
     "instalación de dependencias principales registradas en requirements.txt "
     "(fastapi, uvicorn, sqlalchemy, etc.).",
     "req-03-entorno",
     "Salida real de pip list en el entorno del proyecto."),

    ("REQ-04", "Base de Datos SQL",
     "Estructura relacional SQL mantenida y completada con mínimo las "
     "entidades: Usuarios, Roles, Permisos, Productos y Servicios.",
     "req-04-tablas",
     "SHOW TABLES sobre la base autoprime: siete tablas, incluida rol_permiso "
     "que enlaza roles con permisos."),

    ("REQ-05", "Tabla de Usuarios",
     "Estructura con campos: Nombre, Apellido, Tipo/Número documento, "
     "Dirección, Teléfono, Correo, Contraseña, Rol, Estado. La contraseña debe "
     "almacenarse SOLO con hash seguro.",
     "req-05-tabla-usuarios",
     "DESCRIBE usuarios. La columna se llama password_hash: no existe ninguna "
     "que guarde la contraseña en claro."),

    ("REQ-06", "Modelos y Esquemas",
     "Separación en FastAPI de modelos SQLAlchemy (Base de Datos) y esquemas "
     "Pydantic (Validación). Esquemas deben validar tipos, campos "
     "obligatorios, longitudes y formatos.",
     "req-06-esquemas",
     "Los esquemas de Pydantic publicados en /docs. password_hash está en el "
     "modelo y en ninguno de los esquemas de salida."),

    ("REQ-07", "Conexión DB con FastAPI",
     "Establecer conexión funcional con SQL. Parámetros de configuración "
     "mediante variables de entorno en archivo .env sin exponer contraseñas en "
     "código fuente.",
     "req-07-salud",
     "GET /salud responde tras consultar la base de verdad, no con un valor "
     "fijo."),

    ("REQ-08", "Conexión FrontEnd, BackEnd y DB",
     "Comunicación interactiva. El formulario React envía peticiones a "
     "FastAPI, que realiza re-validación (independiente del FrontEnd y opera "
     "sobre la base de datos SQL.",
     "req-08-revalidacion",
     "Alta con un correo ya registrado, pedida sin pasar por el formulario. "
     "La API responde 409 por su cuenta."),

    ("REQ-09", "Registro de Clientes",
     "Formulario de registro conectado a POST /api/usuarios/registro. Flujo "
     "completo: validaciones, verificación de no duplicados (correo/doc), hash "
     "de contraseña, guardar y respuesta JSON.",
     "req-09-registro",
     "Formulario de alta. Responde en la ruta que pide el instrumento y "
     "también en /api/auth/registro: las dos ejecutan el mismo manejador."),

    ("REQ-10", "Inicio de Sesión",
     "Formulario de login conectado a POST /api/auth/login. Flujo de inicio de "
     "sesión: FastAPI verifica credenciales y genera un JSON Web Token (JWT) "
     "si son correctas.",
     "req-10-login",
     "Formulario de acceso. Cada rol aterriza en su propio panel."),

    ("REQ-11", "Autenticación JWT",
     "React envía el token en la cabecera (Authorization: Bearer TOKEN) en las "
     "peticiones que lo requieran. FastAPI verifica firma, validez, "
     "expiración, usuario y rol asociado.",
     "req-11-jwt",
     "El token descodificado: lleva usuario, rol y caducidad. La firma es lo "
     "que impide alterarlo."),

    ("REQ-12", "Control de Roles",
     "Roles mínimos: Administrador, Empleado, Cliente. Control implementado en "
     "Frontend y Backend (BE tiene la autorización definitiva). Roles definen "
     "accesos y funciones.",
     "req-12-roles",
     "Un cliente pidiendo la lista de usuarios. La interfaz ya lo oculta, pero "
     "la autorización de verdad ocurre aquí: 403."),

    ("REQ-13", "Uso de archivos y Hooks",
     "Creación e implementación de Hooks para gestionar diferentes estados en "
     "la aplicación React, utilizando los distintos Hooks disponibles, como "
     "useState, useEffect, useContext, entre otros.",
     "req-13-hooks",
     "Siete hooks propios y el recuento de archivos que usan cada hook de "
     "React."),

    ("REQ-14", "Endpoints de la API",
     "Creación de endpoints para la gestión de Usuarios, Productos y Servicios "
     "(operaciones REST con rutas estructuradas por entidad).",
     "req-14-catalogo",
     "Catálogo servido por GET /api/productos. En total son 32 endpoints en "
     "cinco grupos, visibles en /docs."),

    ("REQ-15", "Recuperación de Contraseña",
     "implementacion de la funcionalidad de recuperación de contraseña "
     "olvidada por el usuario (Cliente-Empleado)",
     "req-15-recuperar",
     "El enlace llega al correo de la cuenta y se abre en /restablecer. Caduca "
     "a los 30 minutos, sirve una sola vez y no vale como token de sesión."),

    ("REQ-16", "Operaciones CRUD Usuarios",
     "CRUD completo en usuarios para Consultar, Crear, Editar, Actualizar, "
     "Eliminar y Cambiar Estado (Activo/Inactivo para mantener consistencia "
     "histórica).",
     "req-16-crud-usuarios",
     "Alta desde el panel, con selección de rol. La tabla con consultar, "
     "editar, inactivar y eliminar está en la evidencia de REQ-17."),

    ("REQ-17", "Panel de Administración",
     "Panel protegido por autenticación y autorización desarrollado en React, "
     "Vite, Tailwind CSS y FastAPI. Solo administradores pueden gestionar "
     "usuarios y módulos del proyecto.",
     "req-17-panel-admin",
     "Panel de administración con la gestión de usuarios."),

    ("REQ-18", "Panel de Empleado",
     "Panel que restringe el acceso mostrando únicamente las funcionalidades "
     "correspondientes al rol de empleado. BE valida el rol antes de permitir "
     "operaciones restringidas.",
     "req-18-panel-empleado",
     "Panel de empleado. No aparece la gestión de usuarios, exclusiva del "
     "administrador."),

    ("REQ-19", "Panel de Cliente",
     "Panel para el rol de cliente donde accede a sus servicios y productos. "
     "El sistema identifica al usuario mediante la información contenida en el "
     "JWT.",
     "req-19-panel-cliente",
     "Panel de cliente: solo salen sus citas. El dueño se saca del token, no "
     "de lo que envíe el navegador."),

    ("REQ-20", "Usuario en el Navbar",
     "React muestra el nombre del usuario autenticado en el Navbar tras el "
     "login exitoso (ej. 'Bienvenido, Juan | Cerrar sesión'). Se actualiza "
     "automáticamente al cerrar sesión.",
     "req-20-navbar",
     "El nombre y el rol del usuario en la navegación, que desde este avance "
     "es un raíl lateral."),

    ("REQ-21", "Validaciones Tiempo Real",
     "Validación de campos obligatorios, longitudes mín/máx, tipos de datos, "
     "expresiones regulares, correos, teléfonos y contraseñas. Ejecución "
     "obligatoria tanto en React como en FastAPI.",
     "req-21-validacion",
     "Aviso mientras se escribe, sin llegar a enviar. Las mismas reglas se "
     "repiten en los esquemas de Pydantic."),

    ("REQ-22", "Seguridad de Contraseñas",
     "Prohibición de texto plano en DB. Uso obligatorio de algoritmos de "
     "hashing seguros (como bcrypt) en FastAPI para generación, almacenamiento "
     "y verificación en login.",
     "req-22-hash",
     "Hashes bcrypt en la base. Ninguna contraseña en claro."),

    ("REQ-23", "Variables de Entorno",
     "Uso de variables de entorno (ej. en archivo .env local) para resguardar "
     "información sensible (contraseñas de base de datos, claves secretas, "
     "tokens y credenciales).",
     "req-23-entorno",
     "La plantilla .env.example es lo que se publica; el .env real está "
     "ignorado por git, como demuestra git check-ignore."),

    ("REQ-24", "Componente Flotante WhatsApp",
     "Conservar el botón reutilizable 'WhatsAppButton.jsx' con posición fija, "
     "enlace configurado y diseño coherente. Sigue funcionando con "
     "independencia del backend.",
     "req-24-whatsapp",
     "El botón flotante, abajo a la derecha. Sigue ahí con la API apagada."),

    ("REQ-25", "Documentación FastAPI (Swagger)",
     "Habilitación y visualización de la documentación interactiva en "
     "http://127.0.0.1:8000/docs. Debe usarse Swagger UI como evidencia del "
     "funcionamiento de la API.",
     "req-25-swagger",
     "Swagger UI en /docs. El botón Authorize admite el token del login para "
     "probar allí mismo lo protegido."),

    ("REQ-26", "Pruebas con Postman Métodos HTTP",
     "Evidencias de pruebas de endpoints mediante Postman o similar. "
     "Implementación y demostración de los métodos estándar GET, POST, PUT, "
     "PATCH, DELETE.",
     "req-26-pruebas",
     "81 comprobaciones de extremo a extremo por HTTP con los cinco métodos. "
     "La colección de Postman, con 44 peticiones, está en "
     "backend/sql/AutoPrime.postman_collection.json."),
]


def ancho_px(caracteres: float) -> int:
    """Ancho de columna de Excel en píxeles."""
    return round(caracteres * 7) + 5


def main() -> int:
    libro = xlsxwriter.Workbook(DESTINO, {"nan_inf_to_errors": True})
    hoja = libro.add_worksheet("Lista de Chequeo")

    # --- Formatos -------------------------------------------------------
    def f(**extra):
        base = {"border": 1, "border_color": BORDE, "valign": "vcenter",
                "font_name": "Calibri"}
        base.update(extra)
        return libro.add_format(base)

    titulo = f(bg_color=VERDE_OSCURO, font_color=BLANCO, bold=True,
               font_size=18, align="center")
    subtitulo = f(bg_color=VERDE_OSCURO, font_color=BLANCO, italic=True,
                  font_size=11, align="center")
    banda_clara = f(bg_color=VERDE, font_color=BLANCO, bold=True,
                    font_size=12, align="center")
    banda_seccion = f(bg_color=VERDE_OSCURO, font_color=BLANCO, italic=True,
                      bold=True, font_size=11, align="center")
    banda_verde = f(bg_color=VERDE, font_color=BLANCO, bold=True,
                    font_size=11, align="left", indent=1)

    etiqueta = f(bold=True, align="right", font_size=11)
    valor_blanco = f(align="left", font_size=11, indent=1)
    valor_verde = f(bg_color=VERDE_CLARO, align="center", bold=True, font_size=11)
    valor_azul = f(bg_color=AZUL_CLARO, align="center", font_size=11)

    cabecera_tabla = f(bg_color=VERDE, font_color=BLANCO, bold=True,
                       align="center", font_size=11, text_wrap=True)

    def fila(par: bool):
        fondo = GRIS if par else BLANCO
        return {
            "num": f(bg_color=fondo, bold=True, align="center", font_size=11),
            "req": f(bg_color=fondo, bold=True, align="center",
                     text_wrap=True, font_size=11),
            "det": f(bg_color=fondo, italic=True, font_color="#595959",
                     align="center", text_wrap=True, font_size=10),
            "evi": f(bg_color=fondo, align="center"),
            "obs": f(bg_color=AZUL_CLARO, align="left", text_wrap=True,
                     font_size=10, indent=1),
        }

    pie_url = f(bold=True, align="center", font_size=11)
    pie_nota = libro.add_format({"italic": True, "font_size": 9,
                                 "font_color": "#595959", "font_name": "Calibri"})

    # --- Anchos y altos -------------------------------------------------
    for i, col in enumerate("ABCDE"):
        hoja.set_column(i, i, ANCHOS[col])

    r = 0

    # --- Cabecera institucional ----------------------------------------
    hoja.merge_range(r, 0, r + 1, 4, "SENA - REGIONAL ANTIOQUIA", titulo)
    hoja.set_row(r, 30)
    hoja.set_row(r + 1, 18)
    if os.path.isfile(LOGO):
        # El logo va superpuesto sobre la banda, como en el original.
        hoja.insert_image(r, 0, LOGO, {
            "x_scale": 0.20, "y_scale": 0.20,
            "x_offset": 12, "y_offset": 6,
            "object_position": 1,
        })
    r += 2

    hoja.merge_range(r, 0, r, 4, "Centro de Servicio y Gestión Empresarial",
                     subtitulo)
    hoja.set_row(r, 18)
    r += 1

    hoja.merge_range(r, 0, r, 4,
                     "Lista de Chequeo - Cuarto Avance REACT - FASTAPI",
                     banda_clara)
    hoja.set_row(r, 22)
    r += 1

    hoja.merge_range(r, 0, r, 4, "1. DATOS DEL APRENDIZ Y DEL PROGRAMA",
                     banda_seccion)
    hoja.set_row(r, 20)
    r += 1

    # --- Sección 1 ------------------------------------------------------
    datos = [
        ("Nombre del Aprendiz:", "Jose Matías Agudelo Bolívar", valor_verde,
         "Fecha de Presentación:", "2026-09-10", valor_azul),
        ("Documento de Identidad:", "", valor_azul,
         "Ficha de Caracterización:", "3406211", valor_blanco),
        ("Programa de Formación:", "ADSO (Análisis y Desarrollo de Software)",
         valor_blanco, "Trimestre / Ambiente:", "03 / 702", valor_blanco),
        ("Competencia:", "React", valor_blanco,
         "Instructor:", "Jhan Hader Muñoz", valor_blanco),
    ]
    for et_i, val_i, fmt_i, et_d, val_d, fmt_d in datos:
        hoja.merge_range(r, 0, r, 1, et_i, etiqueta)
        hoja.write(r, 2, val_i, fmt_i)
        hoja.write(r, 3, et_d, etiqueta)
        hoja.write(r, 4, val_d, fmt_d)
        hoja.set_row(r, 22)
        r += 1

    # --- Sección 2 ------------------------------------------------------
    hoja.merge_range(r, 0, r, 4, "2. INDICADORES DE AVANCE Y CALIFICACIÓN",
                     banda_verde)
    hoja.set_row(r, 20)
    r += 1

    fila_total = r + 1  # 1-indexada para las fórmulas
    hoja.write(r, 0, "Total Requerimientos:", f(bold=True, align="center",
                                                text_wrap=True, font_size=10))
    hoja.write(r, 1, len(REQUISITOS), valor_verde)
    hoja.write(r, 2, "Requerimientos Cumplidos:", etiqueta)
    hoja.write(r, 3, len(REQUISITOS), valor_verde)
    # El porcentaje se calcula, no se escribe: si el instructor corrige el
    # número de cumplidos, el avance se actualiza solo.
    hoja.write_formula(r, 4, f"=IF(B{fila_total}=0,0,D{fila_total}/B{fila_total})",
                       f(bg_color=VERDE_CLARO, align="center", bold=True,
                         font_size=11, num_format="0.0%"), 1.0)
    hoja.set_row(r, 26)
    r += 1

    hoja.merge_range(r, 0, r, 1, "Estado de Avance:", etiqueta)
    hoja.write(r, 2, "COMPLETO - PENDIENTE REVISIÓN", valor_verde)
    hoja.write(r, 3, "Valoración Final Instructor:", etiqueta)
    hoja.write(r, 4, "Aprobado / No Aprobado", valor_azul)
    hoja.set_row(r, 22)
    r += 1

    # --- Sección 3 ------------------------------------------------------
    hoja.merge_range(
        r, 0, r, 4,
        "3. LISTA DE CHEQUEO - REQUERIMIENTOS DETALLADOS DEL ENTREGABLE (01 AL 26)",
        banda_verde)
    hoja.set_row(r, 20)
    r += 1

    encabezados = ["No.", "Requerimiento", "Detalle / Criterio de Aceptación",
                   "Espacio para Evidencia / Captura de Pantalla",
                   "Observaciones del Aprendiz / Notas de Entrega"]
    for c, texto in enumerate(encabezados):
        hoja.write(r, c, texto, cabecera_tabla)
    hoja.set_row(r, 34)
    fila_encabezado = r
    r += 1

    # --- Los 26 requisitos ---------------------------------------------
    ancho_celda = ancho_px(ANCHOS["D"])
    faltan = []

    for i, (numero, nombre, detalle, archivo, nota) in enumerate(REQUISITOS):
        fmt = fila(i % 2 == 1)
        hoja.write(r, 0, numero, fmt["num"])
        hoja.write(r, 1, nombre, fmt["req"])
        hoja.write(r, 2, detalle, fmt["det"])
        hoja.write_blank(r, 3, None, fmt["evi"])
        hoja.write(r, 4, nota, fmt["obs"])

        ruta = os.path.join(CAPTURAS, f"{archivo}.png")
        if not os.path.isfile(ruta):
            faltan.append(numero)
            hoja.write(r, 3, "[Pegar Captura de Pantalla Aquí]", fmt["evi"])
            hoja.set_row(r, 90)
            r += 1
            continue

        with Image.open(ruta) as imagen:
            ancho_nativo, alto_nativo = imagen.size

        escala = ANCHO_IMAGEN / ancho_nativo
        alto_mostrado = alto_nativo * escala

        # Una fila no puede pasar de 409 puntos; si la captura es muy alta se
        # reduce entera en vez de recortarla.
        alto_puntos = alto_mostrado * 0.75 + 10
        if alto_puntos > ALTO_MAXIMO_FILA:
            escala *= (ALTO_MAXIMO_FILA - 10) / (alto_puntos - 10)
            alto_mostrado = alto_nativo * escala
            alto_puntos = ALTO_MAXIMO_FILA

        hoja.insert_image(r, 3, ruta, {
            "x_scale": escala, "y_scale": escala,
            "x_offset": max(2, (ancho_celda - ancho_nativo * escala) / 2),
            "y_offset": 5,
            "object_position": 1,   # se mueve y se ajusta con la celda
            "description": f"Evidencia del requisito {numero}: {nombre}",
        })
        hoja.set_row(r, alto_puntos)
        r += 1

    # --- Pie ------------------------------------------------------------
    hoja.merge_range(
        r, 0, r, 2,
        "Url del Drive o Git Hub, donde se encuentra alojado el cuarto entregable:",
        pie_url)
    hoja.merge_range(r, 3, r, 4, "https://github.com/matias2421/autoprime",
                     f(align="center", font_color="#0563C1", underline=True,
                       font_size=11))
    hoja.set_row(r, 24)
    r += 2

    hoja.write(r, 0, "Versión del Instrumento: 1.0 | Cuarto Entregable React + "
                     "FastAPI | Generado: 2026-08-31", pie_nota)
    r += 1
    hoja.write(r, 0, "Nota: Este archivo es una herramienta de autoevaluación "
                     "académica para el SENA ADSO.", pie_nota)

    # --- Presentación e impresión ---------------------------------------
    hoja.freeze_panes(fila_encabezado + 1, 0)
    hoja.set_landscape()
    hoja.set_paper(9)                    # A4
    hoja.fit_to_pages(1, 0)              # una página de ancho: el PDF del
                                         # instructor se partía en dos y por
                                         # eso no se leía la mitad derecha.
    hoja.repeat_rows(fila_encabezado)
    hoja.set_margins(0.3, 0.3, 0.4, 0.4)
    hoja.hide_gridlines(2)

    libro.close()

    peso = os.path.getsize(DESTINO) / 1024 / 1024
    print(f"  {DESTINO}")
    print(f"  {len(REQUISITOS)} requisitos, {len(REQUISITOS) - len(faltan)} con captura")
    if faltan:
        print(f"  sin captura: {', '.join(faltan)}")
    print(f"  {peso:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
