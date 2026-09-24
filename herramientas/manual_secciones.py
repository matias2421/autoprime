# -*- coding: utf-8 -*-
"""El contenido del Manual Técnico, sección a sección.

Las catorce que pide la solicitud, en su orden. Lo que puede leerse del
proyecto se lee (tablas, endpoints, dependencias, capturas); lo que no
—el problema, los objetivos, el alcance, las conclusiones— está escrito
aquí, que es donde debe estar.
"""

import os
import sys
from datetime import date

from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manual_datos import (  # noqa: E402
    DEPENDENCIAS_BACKEND,
    DEPENDENCIAS_FRONTEND,
    ENDPOINTS,
    ENTIDADES,
    TAMANO,
    VARIABLES_ENTORNO,
    VERSION_API,
)
from manual_diagramas import (  # noqa: E402
    diagrama_arquitectura,
    diagrama_entidad_relacion,
)
from manual_estilo import (  # noqa: E402
    ANCHO_UTIL,
    ESTILOS,
    LINEA,
    captura,
    codigo,
    h1,
    h2,
    h3,
    numerada,
    p,
    tabla,
    vinetas,
)

PROYECTO = "AutoPrime — Plataforma web para un atelier automotriz"
APRENDIZ = "José Matías Agudelo Bolívar"
DOCUMENTO = "1038928023"
FICHA = "3406211"
PROGRAMA = "Análisis y Desarrollo de Software (ADSO)"
CENTRO = "Centro de Servicio y Gestión Empresarial (CESGE) — Regional Antioquia"
INSTRUCTOR = "César Augusto Moreno Mena"
REPOSITORIO = "https://github.com/matias2421/autoprime"
API_PUBLICA = "https://autoprime-api-z9b6.onrender.com"

# La solicitud del instructor deja estos dos campos en blanco. No se
# inventan: se marcan para rellenarlos con el código oficial.
COMPETENCIA = "[código y nombre de la competencia]"
RAP = "[código y nombre del RAP]"

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre")


def fecha_larga(dia=None):
    dia = dia or date.today()
    return "%d de %s de %d" % (dia.day, MESES[dia.month - 1], dia.year)


# ===========================================================================
# Portada
# ===========================================================================
def portada():
    ficha = [
        ("Aprendiz", APRENDIZ),
        ("Documento de identidad", DOCUMENTO),
        ("Ficha de caracterización", FICHA),
        ("Programa de formación", PROGRAMA),
        ("Centro / Regional", CENTRO),
        ("Competencia", COMPETENCIA),
        ("Resultado de Aprendizaje (RAP)", RAP),
        ("Instructor", INSTRUCTOR),
        ("Fecha de entrega", fecha_larga()),
    ]
    filas = [[Paragraph("<b>%s</b>" % k, ESTILOS["celda"]),
              Paragraph(v, ESTILOS["celda"])] for k, v in ficha]
    t = Table(filas, colWidths=[ANCHO_UTIL * 0.40, ANCHO_UTIL * 0.60],
              hAlign="CENTER")
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINEA),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    return [
        Spacer(1, 1.3 * cm),
        Paragraph("SERVICIO NACIONAL DE APRENDIZAJE — SENA",
                  ESTILOS["portadaCentro"]),
        Paragraph("Centro de Servicio y Gestión Empresarial",
                  ESTILOS["portadaCentro"]),
        Spacer(1, 2.0 * cm),
        Paragraph("MANUAL TÉCNICO", ESTILOS["portadaTitulo"]),
        Paragraph(PROYECTO, ESTILOS["portadaSub"]),
        Spacer(1, 0.6 * cm),
        t,
        Spacer(1, 1.4 * cm),
        Paragraph("Repositorio: %s" % REPOSITORIO, ESTILOS["portadaCentro"]),
        Paragraph("API desplegada: %s" % API_PUBLICA, ESTILOS["portadaCentro"]),
        PageBreak(),
    ]


# ===========================================================================
# Tabla de contenido
# ===========================================================================
def contenido():
    indice = TableOfContents()
    indice.levelStyles = [ESTILOS["toc1"], ESTILOS["toc2"]]
    indice.dotsMinLevel = 0
    return [
        # Con estilo «h1» este título se recogía a sí mismo como primera
        # entrada del índice. Va con un estilo que se ve igual pero que el
        # recolector no mira.
        Paragraph("Tabla de contenido", ESTILOS["tituloSuelto"]),
        Spacer(1, 6),
        indice,
        PageBreak(),
    ]


# ===========================================================================
# 1. Introducción y descripción general
# ===========================================================================
def introduccion():
    bloque = [h1("1. Introducción y descripción general")]

    bloque += [
        h2("1.1 El problema que resuelve"),
        p("Un atelier automotriz —un concesionario de vehículos de alta gama "
          "con taller propio— mueve pocas operaciones al mes, pero cada una "
          "vale mucho y deja rastro en varios sitios a la vez: el vehículo "
          "sale del catálogo, se emite una factura, queda un saldo por cobrar "
          "y casi siempre una cita de entrega o de taller."),
        p("Cuando ese rastro se lleva en una hoja de cálculo y en el correo "
          "aparecen tres problemas, y son los que ataca este proyecto. El "
          "primero es que <b>nadie sabe en tiempo real cómo va el negocio</b>: "
          "para responder «cuánto llevamos este mes» o «cuánto hay pendiente "
          "de cobro» hay que sentarse a sumar. El segundo es que <b>el dato no "
          "tiene un dueño claro</b>: el mismo número vive en la hoja de un "
          "vendedor y en el correo de otro, y cuando no coinciden no hay forma "
          "de saber cuál es el bueno. El tercero es que <b>el cliente queda "
          "fuera</b>: para conocer el estado de su compra, pedir una cita o "
          "reclamar, tiene que llamar y esperar a que alguien lo atienda."),
        p("AutoPrime resuelve los tres con la misma decisión de fondo: una "
          "sola base de datos, una API que es lo único que la toca, y tres "
          "vistas distintas sobre esa misma información según quién entre."),
    ]

    bloque += [
        h2("1.2 Contexto"),
        p("El proyecto se desarrolla como proyecto formativo del programa de "
          "Análisis y Desarrollo de Software, ficha %s. El negocio que se "
          "modela es ficticio pero coherente: un atelier del Eje Cafetero que "
          "vende vehículos de alta gama personalizados y presta servicios de "
          "peritaje, prueba de manejo y taller certificado." % FICHA),
        p("Las reglas que aplica son las colombianas. El IVA se calcula al "
          "19&nbsp;%, los importes van en pesos y se redondean una sola vez, "
          "los teléfonos se validan como celulares de diez dígitos que "
          "empiezan por 3, las fechas se interpretan en la zona horaria de "
          "Bogotá y la agenda respeta los festivos nacionales."),
        p("La zona horaria merece una línea aparte porque costó un fallo real: "
          "el servidor de producción trabaja en UTC, y sin fijar la zona el "
          "informe del día salía vacío a partir de las siete de la tarde, "
          "porque para el servidor ya era mañana. Toda fecha del sistema pasa "
          "hoy por un único módulo que resuelve esa cuestión."),
    ]

    bloque += [
        h2("1.3 Usuarios y actores"),
        p("El sistema reconoce tres roles, y la diferencia entre ellos no es "
          "cosmética: cada uno ve pantallas distintas y, sobre todo, la API le "
          "responde cosas distintas aunque pida exactamente la misma ruta."),
        tabla(
            ["Actor", "Qué puede hacer", "Qué no puede hacer"],
            [
                ["<b>Visitante</b><br/>(sin cuenta)",
                 "Ver el catálogo y la ficha de cada vehículo, consultar los "
                 "servicios, preguntar al asistente y crear una cuenta.",
                 "Nada que toque datos de nadie."],
                ["<b>Cliente</b>",
                 "Ver sus compras, sus facturas, sus citas y sus PQR. Agendar, "
                 "radicar reclamos y descargar sus propias facturas.",
                 "Ver operaciones de otros clientes, registrar ventas, emitir "
                 "facturas o entrar al tablero del negocio."],
                ["<b>Empleado</b>",
                 "Registrar ventas, emitir y anular facturas, gestionar la "
                 "agenda y responder PQR.",
                 "Administrar usuarios ni consultar los informes del negocio."],
                ["<b>Administrador</b>",
                 "Todo lo del empleado, más la gestión de usuarios y del "
                 "catálogo y el tablero con los informes en PDF y Excel.",
                 "—"],
            ],
            [ANCHO_UTIL * 0.17, ANCHO_UTIL * 0.47, ANCHO_UTIL * 0.36]),
        Paragraph("Tabla 1. Actores del sistema y alcance de cada uno.",
                  ESTILOS["pie"]),
    ]
    return bloque


# ===========================================================================
# 2. Objetivos
# ===========================================================================
def objetivos():
    bloque = [h1("2. Objetivos"), h2("2.1 Objetivo general")]
    bloque.append(p(
        "Desarrollar y desplegar una aplicación web que permita a un atelier "
        "automotriz gestionar en un solo lugar su catálogo, sus ventas, su "
        "facturación, su agenda y la atención a sus clientes, con acceso "
        "diferenciado por rol y con la información del negocio disponible en "
        "el momento en que se necesita."))

    bloque.append(h2("2.2 Objetivos específicos"))
    bloque += numerada([
        "<b>Modelar y construir la base de datos relacional</b> que sostiene "
        "el negocio, con la integridad garantizada por claves ajenas y no por "
        "la disciplina de quien escribe.",
        "<b>Construir una API REST con FastAPI</b> que sea el único camino "
        "hacia los datos, que valide todo lo que entra y que documente sola "
        "lo que ofrece.",
        "<b>Implementar autenticación y autorización por rol</b> con JWT y "
        "contraseñas cifradas con bcrypt, de modo que el permiso lo decida "
        "siempre el servidor y nunca la interfaz.",
        "<b>Desarrollar la interfaz en React</b> consumiendo esa API, con "
        "validación en vivo en los formularios y tres vistas separadas según "
        "quién haya entrado.",
        "<b>Generar los documentos del negocio</b> —facturas e informes en "
        "PDF, e informes en Excel— desde el propio servidor, con los cálculos "
        "hechos una sola vez y en un solo sitio.",
        "<b>Desplegar el sistema en internet y dejarlo comprobable</b>: "
        "pruebas automáticas, una batería de peticiones sobre la API y "
        "medidas de seguridad verificables sobre el servidor en producción.",
    ])
    return bloque


# ===========================================================================
# 3. Alcance
# ===========================================================================
def alcance():
    bloque = [h1("3. Alcance del proyecto")]
    bloque.append(p(
        "Decir qué hace un sistema solo sirve si también se dice qué no hace. "
        "Lo segundo se documenta aquí con el mismo detalle que lo primero: son "
        "decisiones tomadas, no cosas que se olvidaron."))

    bloque.append(h2("3.1 Funcionalidades incluidas"))
    bloque.append(tabla(
        ["Módulo", "Qué incluye"],
        [
            ["Catálogo",
             "Alta, edición, baja y consulta de vehículos y de servicios, con "
             "ficha técnica, familia, estado y galería. Consulta pública."],
            ["Cuentas y acceso",
             "Registro de clientes, inicio de sesión con JWT, recuperación de "
             "contraseña por correo, gestión de usuarios y baja lógica."],
            ["Agenda",
             "Consulta de franjas libres, reserva por servicio y vehículo, "
             "reprogramación y cambio de estado. Respeta festivos."],
            ["Ventas",
             "Registro con varias líneas, cálculo de subtotal, descuento e "
             "IVA en el servidor, estados (pendiente, pagada, anulada) y "
             "consulta con filtros y paginación."],
            ["Facturación",
             "Emisión a partir de una venta, numeración propia, anulación sin "
             "borrado y descarga en PDF con importe en letras y código de "
             "verificación."],
            ["Informes",
             "Tablero con cifras del periodo y comparación con el anterior, "
             "gráficas de ingresos por día y de lo más vendido, y descarga "
             "del informe en PDF y en Excel."],
            ["PQR",
             "Radicación por el cliente con número de radicado, respuesta y "
             "cambio de estado por parte del atelier."],
            ["Asistente",
             "Chat con un modelo de lenguaje que responde sobre el catálogo, "
             "los servicios y la agenda, con la conversación guardada."],
            ["Seguridad",
             "Cabeceras de seguridad, límite de intentos en el acceso y en la "
             "recuperación, consultas parametrizadas y escapes en los "
             "documentos generados."],
        ],
        [ANCHO_UTIL * 0.22, ANCHO_UTIL * 0.78]))
    bloque.append(Paragraph("Tabla 2. Alcance funcional implementado.",
                            ESTILOS["pie"]))

    bloque.append(h2("3.2 Funcionalidades explícitamente excluidas"))
    bloque.append(tabla(
        ["Queda fuera", "Por qué"],
        [
            ["Pasarela de pago en línea",
             "Exige un contrato con una entidad recaudadora y tratar datos de "
             "tarjeta, que es justo lo que un proyecto formativo no debe "
             "manipular. La venta registra el cobro; no lo ejecuta."],
            ["Facturación electrónica ante la DIAN",
             "Requiere habilitación como facturador y firma digital. El PDF "
             "reproduce la estructura de una factura, pero no es un documento "
             "fiscal válido, y el propio documento lo advierte."],
            ["Aplicación móvil nativa",
             "La interfaz es adaptable y funciona en el navegador del móvil. "
             "Una aplicación nativa sería otro proyecto."],
            ["Inventario por unidades y proveedores",
             "El catálogo lleva el estado de cada vehículo (disponible o "
             "vendido), no un almacén con entradas, salidas y compras."],
            ["Nómina, contabilidad y cartera",
             "El sistema sabe qué está por cobrar, pero no lleva libros "
             "contables ni gestiona pagos a proveedores."],
            ["Mensajería entre personas",
             "El asistente habla con un modelo de lenguaje. No hay chat entre "
             "cliente y vendedor; para eso están las PQR y WhatsApp."],
        ],
        [ANCHO_UTIL * 0.30, ANCHO_UTIL * 0.70]))
    bloque.append(Paragraph("Tabla 3. Fuera de alcance, y el motivo.",
                            ESTILOS["pie"]))
    return bloque


# ===========================================================================
# 4. Arquitectura de la solución
# ===========================================================================
def arquitectura():
    bloque = [h1("4. Arquitectura de la solución")]
    bloque.append(p(
        "La arquitectura es de tres capas con una separación estricta: el "
        "navegador nunca habla con la base de datos. Todo pasa por la API, y "
        "eso no es una formalidad — es lo que permite que la misma regla de "
        "negocio valga igual para la interfaz, para una petición hecha desde "
        "Postman y para un script."))

    bloque.append(h2("4.1 Diagrama de arquitectura"))
    bloque.append(diagrama_arquitectura(ANCHO_UTIL))
    bloque.append(Paragraph(
        "Figura 1. Capas del sistema, servicios externos y la capa "
        "transversal de seguridad.", ESTILOS["pie"]))

    bloque.append(h2("4.2 Stack tecnológico"))
    bloque.append(tabla(
        ["Capa", "Tecnología", "Por qué esta y no otra"],
        [
            ["Frontend", "React 19 · Vite 8 · Tailwind CSS 4 · React Router 7",
             "Vite da recarga instantánea en desarrollo y un paquete pequeño "
             "en producción. Tailwind mantiene el estilo junto al componente, "
             "sin hojas sueltas que nadie sabe si siguen usándose."],
            ["Backend", "Python 3.12 · FastAPI · Pydantic v2 · Uvicorn",
             "FastAPI valida con Pydantic y publica su propia documentación "
             "OpenAPI: la especificación no puede quedarse atrás del código "
             "porque sale del código."],
            ["Acceso a datos", "SQLAlchemy 2.0 asíncrono · aiomysql",
             "El ORM parametriza todas las consultas, que es la defensa real "
             "contra la inyección SQL. En asíncrono, una consulta lenta no "
             "bloquea al resto de peticiones."],
            ["Base de datos", "MySQL 8 (Aiven en producción, XAMPP en local)",
             "Relacional porque el negocio lo es: una factura sin su venta no "
             "significa nada, y eso lo garantiza una clave ajena."],
            ["Documentos", "reportlab (PDF) · XlsxWriter (Excel)",
             "Son Python puro y no arrastran librerías del sistema. Un "
             "generador que dependiera de Chrome o de cairo funcionaría en el "
             "portátil y fallaría en el servidor."],
            ["Servicios externos", "Groq · SMTP · calendario de festivos",
             "El asistente usa un modelo de lenguaje alojado; el correo sale "
             "por SMTP; los festivos se consultan para no ofrecer citas en "
             "días no hábiles."],
            ["Despliegue", "Render (API) · Vercel (frontend)",
             "Los dos despliegan desde el repositorio en cada push. La API "
             "necesita un proceso vivo; el frontend son archivos estáticos."],
        ],
        [ANCHO_UTIL * 0.16, ANCHO_UTIL * 0.30, ANCHO_UTIL * 0.54]))
    bloque.append(Paragraph("Tabla 4. Stack tecnológico y criterio de "
                            "elección.", ESTILOS["pie"]))

    bloque.append(h2("4.3 Organización del código"))
    bloque.append(p(
        "El backend está dividido por responsabilidad, no por entidad. Cada "
        "carpeta de <font face='Courier'>backend/app</font> hace una sola "
        "cosa:"))
    bloque += vinetas([
        "<b>core</b> — configuración, conexión a la base, seguridad, "
        "cabeceras y el módulo de fechas.",
        "<b>models</b> — las tablas, declaradas con SQLAlchemy.",
        "<b>schemas</b> — lo que entra y lo que sale, validado con Pydantic. "
        "Separado de los modelos a propósito: así una columna interna como "
        "<font face='Courier'>password_hash</font> no puede escaparse en una "
        "respuesta por descuido.",
        "<b>crud</b> — las operaciones sobre la base y las reglas de negocio.",
        "<b>routers</b> — las rutas HTTP, que solo orquestan.",
        "<b>reportes</b> — la generación de PDF y Excel, con sus escapes.",
    ])
    bloque.append(p(
        "El frontend sigue la misma idea: <font face='Courier'>pages</font> "
        "para las pantallas, <font face='Courier'>components</font> para lo "
        "reutilizable, <font face='Courier'>hooks</font> para la lógica "
        "compartida, <font face='Courier'>context</font> para el estado de "
        "sesión y <font face='Courier'>api</font> para el único cliente HTTP "
        "que habla con el backend."))

    bloque.append(tabla(
        ["Parte", "Archivos", "Líneas"],
        [
            ["Backend (backend/app)", str(TAMANO["backend"][0]),
             "{:,}".format(TAMANO["backend"][1]).replace(",", ".")],
            ["Frontend (frontend/src)", str(TAMANO["frontend"][0]),
             "{:,}".format(TAMANO["frontend"][1]).replace(",", ".")],
            ["Pruebas (backend/tests)", str(TAMANO["pruebas"][0]),
             "{:,}".format(TAMANO["pruebas"][1]).replace(",", ".")],
        ],
        [ANCHO_UTIL * 0.45, ANCHO_UTIL * 0.25, ANCHO_UTIL * 0.30]))
    bloque.append(Paragraph("Tabla 5. Tamaño del proyecto.", ESTILOS["pie"]))
    return bloque


# ===========================================================================
# 5. Modelo de datos
# ===========================================================================
# SQLAlchemy nombra los tipos de forma neutra; el manual documenta el
# esquema tal como existe EN MySQL, que es donde alguien va a mirarlo. Los
# dos nombres designan lo mismo, pero quien abra la base va a leer DECIMAL.
TIPOS_LEGIBLES = {
    "INTEGER": "INT",
    "NUMERIC": "DECIMAL",
}


def _tipo_legible(tipo):
    """INTEGER -> INT, NUMERIC(14, 2) -> DECIMAL(14,2)."""
    nombre, _, argumentos = tipo.partition("(")
    nombre = TIPOS_LEGIBLES.get(nombre.strip(), nombre.strip())
    if not argumentos:
        return nombre
    return "%s(%s" % (nombre, argumentos.replace(", ", ","))


def modelo_datos():
    bloque = [h1("5. Modelo de datos")]
    bloque.append(p(
        "El esquema tiene <b>%d tablas</b>. La integridad no depende de que "
        "el código se acuerde de comprobar: las claves ajenas impiden que "
        "exista una factura sin venta, una línea sin factura o un mensaje sin "
        "conversación." % len(ENTIDADES)))

    bloque.append(h2("5.1 Diagrama entidad-relación"))
    bloque.append(diagrama_entidad_relacion(ENTIDADES, ANCHO_UTIL))
    bloque.append(Paragraph(
        "Figura 2. Entidades y claves ajenas. Cada flecha va del lado «muchos» "
        "al lado «uno». Se dibuja leyendo el esquema, así que no puede "
        "discrepar de él.", ESTILOS["pie"]))

    bloque.append(h2("5.2 Decisiones del modelo que conviene conocer"))
    bloque += vinetas([
        "<b>Las líneas guardan copia de la descripción y del precio.</b> Si "
        "mañana sube el precio de un vehículo, una venta de hace tres meses "
        "tiene que seguir valiendo lo que valió. Por eso "
        "<font face='Courier'>detalle_ventas</font> no se limita a apuntar al "
        "producto: copia lo que se vendió y a cuánto.",
        "<b>El estado del catálogo describe el presente, no el pasado.</b> "
        "Que un vehículo se vendiera hace cuarenta días no obliga a que hoy "
        "siga marcado como vendido: el atelier repone. Por eso el estado vive "
        "en <font face='Courier'>productos</font> y el histórico en las "
        "ventas.",
        "<b>Una factura anulada no se borra.</b> Cambia de estado. Un "
        "documento fiscal que desaparece deja un hueco en la numeración, y un "
        "hueco en la numeración es exactamente lo que no debe pasar.",
        "<b>Los importes van en DECIMAL(14,2), nunca en coma flotante.</b> Un "
        "número en coma flotante no puede representar 0,1 con exactitud, y en "
        "dinero eso acaba en céntimos que no cuadran.",
    ])

    bloque.append(h2("5.3 Sobre la tabla de permisos"))
    bloque.append(p(
        "El modelo declara una tabla <font face='Courier'>permisos</font> con "
        "un catálogo de acciones nombradas, heredada de una etapa anterior del "
        "proyecto. Conviene ser explícito: <b>la autorización real no la "
        "resuelve esa tabla</b>, sino el nombre del rol del usuario, que es "
        "lo que comprueban las dependencias de FastAPI en cada ruta "
        "protegida. La tabla se conserva porque describe bien el vocabulario "
        "de acciones del sistema y porque una futura versión con permisos "
        "finos partiría de ahí, pero hoy no interviene en ninguna decisión."))

    bloque.append(h2("5.4 Diccionario de datos"))
    bloque.append(p(
        "Se lee directamente de la declaración de SQLAlchemy, de modo que "
        "coincide con el esquema por construcción y no por revisión."))

    for entidad in ENTIDADES:
        filas = []
        for c in entidad["columnas"]:
            notas = []
            if c["pk"]:
                notas.append("Clave primaria")
            if c["fk"]:
                notas.append("Clave ajena &rarr; %s" % c["fk"])
            if c["unica"] and not c["pk"]:
                notas.append("Único")
            filas.append([
                "<font face='Courier'>%s</font>" % c["nombre"],
                _tipo_legible(c["tipo"]),
                "No" if c["nulo"] else "Sí",
                "; ".join(notas) or "—",
            ])
        bloque.append(h3("%s — %s" % (entidad["tabla"], entidad["proposito"])))
        bloque.append(tabla(
            ["Campo", "Tipo", "Obligatorio", "Notas"],
            filas,
            [ANCHO_UTIL * 0.25, ANCHO_UTIL * 0.23, ANCHO_UTIL * 0.14,
             ANCHO_UTIL * 0.38]))
    bloque.append(Paragraph(
        "Tabla 6. Diccionario de datos de las %d entidades."
        % len(ENTIDADES), ESTILOS["pie"]))
    return bloque


# ===========================================================================
# 6. Diseño de la solución
# ===========================================================================
def diseno():
    bloque = [h1("6. Diseño de la solución")]
    bloque.append(p(
        "Las historias de usuario se escriben desde quien las necesita, y "
        "cada una se enlaza con el endpoint que la resuelve y con la pantalla "
        "donde se usa. Sin ese enlace, una historia es una intención; con él "
        "es algo que se puede comprobar."))

    bloque.append(h2("6.1 Historias de usuario principales"))
    bloque.append(tabla(
        ["ID", "Historia", "Endpoint principal", "Pantalla"],
        [
            ["HU-01",
             "Como <b>visitante</b> quiero ver el catálogo y la ficha de un "
             "vehículo para decidir si me interesa.",
             "GET /api/productos", "/modelos"],
            ["HU-02",
             "Como <b>visitante</b> quiero crear una cuenta para poder "
             "agendar y seguir mis compras.",
             "POST /api/auth/registro", "Ventana de registro"],
            ["HU-03",
             "Como <b>usuario registrado</b> quiero iniciar sesión y "
             "recuperar mi contraseña si la olvido.",
             "POST /api/auth/login<br/>POST /api/auth/recuperar", "/login"],
            ["HU-04",
             "Como <b>cliente</b> quiero agendar una prueba de manejo "
             "eligiendo día y hora entre las franjas libres.",
             "GET /api/citas/disponibilidad<br/>POST /api/citas", "/agendar"],
            ["HU-05",
             "Como <b>empleado</b> quiero registrar una venta con varias "
             "líneas y que el sistema calcule el IVA.",
             "POST /api/ventas", "/panel/ventas"],
            ["HU-06",
             "Como <b>empleado</b> quiero emitir la factura de una venta y "
             "descargarla en PDF para entregarla.",
             "POST /api/facturas/venta/{id}<br/>GET /api/facturas/{id}/pdf",
             "/panel/facturas"],
            ["HU-07",
             "Como <b>administrador</b> quiero ver cómo va el negocio en el "
             "periodo y compararlo con el anterior.",
             "GET /api/reportes/panel<br/>GET /api/reportes/ventas",
             "/panel/tablero"],
            ["HU-08",
             "Como <b>administrador</b> quiero descargar el informe en PDF "
             "para imprimirlo y en Excel para analizarlo.",
             "GET /api/reportes/ventas/pdf<br/>.../excel", "/panel/tablero"],
            ["HU-09",
             "Como <b>cliente</b> quiero radicar una queja y ver la respuesta "
             "sin tener que llamar.",
             "POST /api/pqr<br/>GET /api/pqr", "/panel/pqr"],
            ["HU-10",
             "Como <b>empleado</b> quiero responder una PQR y dejar claro si "
             "el caso queda cerrado.",
             "PATCH /api/pqr/{id}/responder", "/panel/pqr"],
            ["HU-11",
             "Como <b>visitante</b> quiero preguntar por el catálogo o los "
             "servicios sin esperar a que me atiendan.",
             "POST /api/chat/conversaciones/{id}/mensajes",
             "Asistente flotante"],
            ["HU-12",
             "Como <b>administrador</b> quiero dar de alta o de baja usuarios "
             "y cambiarles el rol.",
             "POST /api/usuarios<br/>PATCH /api/usuarios/{id}/estado",
             "/panel/admin"],
        ],
        [ANCHO_UTIL * 0.08, ANCHO_UTIL * 0.42, ANCHO_UTIL * 0.31,
         ANCHO_UTIL * 0.19]))
    bloque.append(Paragraph(
        "Tabla 7. Historias de usuario y su correspondencia con la "
        "implementación.", ESTILOS["pie"]))

    bloque.append(h2("6.2 Flujo de una venta, de principio a fin"))
    bloque.append(p(
        "Es el caso de uso que más piezas toca, y sirve para ver cómo encajan:"))
    bloque += numerada([
        "El empleado busca al cliente (<font face='Courier'>GET "
        "/api/usuarios/clientes</font>) y añade las líneas desde el catálogo.",
        "Al guardar, la API recalcula subtotal, descuento e IVA <b>ignorando "
        "cualquier total que venga del navegador</b>. El importe lo decide el "
        "servidor; si se fiara del cliente, cambiar un número en las "
        "herramientas del navegador cambiaría el precio.",
        "La venta nace en estado <i>pendiente</i> y se registran sus líneas "
        "con copia de descripción y precio.",
        "Cuando se cobra, pasa a <i>pagada</i>; si se cae, a <i>anulada</i>. "
        "Una venta anulada no cuenta como ingreso en ningún informe.",
        "Se emite la factura, que copia las líneas y recibe su propia "
        "numeración. A partir de ahí la factura es independiente.",
        "El PDF se genera bajo demanda con el estado del momento, así que una "
        "factura anulada se descarga marcada como tal.",
    ])
    return bloque


# ===========================================================================
# 7. Manual de instalación y configuración
# ===========================================================================
def instalacion():
    bloque = [h1("7. Manual de instalación y configuración")]
    bloque.append(p(
        "Los pasos que siguen se han ejecutado tal cual sobre Windows 11 y "
        "dejan el proyecto funcionando en local. Quien los siga no necesita "
        "conocer el código."))

    bloque.append(h2("7.1 Requisitos previos"))
    bloque.append(tabla(
        ["Requisito", "Versión", "Para qué"],
        [
            ["Python", "3.12 o superior", "Ejecuta la API."],
            ["Node.js", "20 o superior", "Compila y sirve el frontend."],
            ["MySQL / MariaDB", "8.0 o superior (XAMPP sirve)",
             "Guarda los datos."],
            ["Git", "cualquiera reciente", "Clona el repositorio."],
        ],
        [ANCHO_UTIL * 0.28, ANCHO_UTIL * 0.34, ANCHO_UTIL * 0.38]))
    bloque.append(Paragraph("Tabla 8. Requisitos previos.", ESTILOS["pie"]))

    bloque.append(h2("7.2 Instalación del backend"))
    bloque.append(codigo([
        "git clone https://github.com/matias2421/autoprime.git",
        "cd autoprime/backend",
        "",
        "python -m venv venv",
        "venv\\Scripts\\activate          # en Windows",
        "source venv/bin/activate        # en Linux o macOS",
        "",
        "pip install -r requirements.txt",
    ]))
    bloque.append(p(
        "El archivo <font face='Courier'>requirements.txt</font> fija las "
        "versiones exactas, de modo que la instalación es reproducible: no "
        "depende de qué versión sea la más reciente el día que se instale."))

    bloque.append(h2("7.3 Variables de entorno"))
    bloque.append(p(
        "La configuración va en un archivo <font face='Courier'>.env</font> "
        "dentro de <font face='Courier'>backend/</font>. En el repositorio "
        "hay un <font face='Courier'>.env.example</font> con todos los "
        "nombres; el <font face='Courier'>.env</font> real está excluido del "
        "control de versiones <b>a propósito</b>, porque contiene "
        "contraseñas. Ninguna credencial aparece en el código fuente."))
    bloque.append(codigo(["copy .env.example .env    # y se rellena"]))
    bloque.append(tabla(
        ["Variable", "Para qué sirve", "Ejemplo"],
        [[nombre, sentido or "—", ejemplo or "—"]
         for nombre, sentido, ejemplo in VARIABLES_ENTORNO],
        [ANCHO_UTIL * 0.28, ANCHO_UTIL * 0.47, ANCHO_UTIL * 0.25]))
    bloque.append(Paragraph("Tabla 9. Variables de entorno del backend.",
                            ESTILOS["pie"]))

    bloque.append(h2("7.4 Preparar la base de datos"))
    bloque.append(codigo([
        "venv\\Scripts\\python preparar_base.py",
        "",
        "# Y, para poder enseñar el sistema con movimiento dentro:",
        "venv\\Scripts\\python sembrar_demo.py",
    ]))
    bloque.append(p(
        "El primero crea el esquema, el catálogo, los roles y tres cuentas de "
        "acceso. El segundo añade encima clientes, ventas cobradas y por "
        "cobrar, facturas, citas, PQR y conversaciones: sin eso los tableros "
        "salen a cero, y una pantalla en blanco no demuestra nada."))

    bloque.append(h2("7.5 Arrancar"))
    bloque.append(codigo([
        "# API, desde backend/",
        "venv\\Scripts\\python servidor.py        # queda en el puerto 8000",
        "",
        "# Frontend, desde frontend/",
        "npm install",
        "npm run dev                             # queda en el puerto 5173",
    ]))
    bloque.append(p(
        "La API se arranca con <font face='Courier'>servidor.py</font> y no "
        "con uvicorn directamente por una razón concreta de Windows: el bucle "
        "de eventos que asyncio elige por defecto no consigue levantar una "
        "conexión cifrada con la base, y falla con un error que no menciona "
        "el cifrado por ningún lado. El arrancador fija el bucle correcto "
        "antes de que uvicorn cree el suyo. En Linux no hace falta, y por eso "
        "en el servidor se lanza uvicorn directamente."))
    bloque.append(p(
        "Con las dos piezas en marcha, la aplicación queda en "
        "<font face='Courier'>http://localhost:5173</font> y la documentación "
        "interactiva de la API en "
        "<font face='Courier'>http://localhost:8000/docs</font>."))

    bloque.append(h2("7.6 Despliegue en producción"))
    bloque.append(tabla(
        ["Pieza", "Dónde", "Cómo"],
        [
            ["API", "Render",
             "Desde <font face='Courier'>render.yaml</font>. Las variables "
             "sensibles se cargan en el panel, nunca en el repositorio. La "
             "comprobación de salud apunta a "
             "<font face='Courier'>/vivo</font>."],
            ["Frontend", "Vercel",
             "Carpeta raíz <font face='Courier'>frontend</font> y la variable "
             "<font face='Courier'>VITE_API_URL</font> apuntando a la API con "
             "<font face='Courier'>/api</font> al final."],
            ["Base de datos", "Aiven (MySQL)",
             "Enlace cifrado con TLS y certificado verificado. "
             "<font face='Courier'>/salud</font> informa del estado del "
             "cifrado, que es la única forma de confirmarlo desde fuera."],
        ],
        [ANCHO_UTIL * 0.16, ANCHO_UTIL * 0.16, ANCHO_UTIL * 0.68]))
    bloque.append(Paragraph("Tabla 10. Despliegue de cada pieza.",
                            ESTILOS["pie"]))
    bloque.append(p(
        "Un detalle del despliegue que costó un fallo real y que conviene "
        "documentar: la comprobación de salud del proveedor apunta a "
        "<font face='Courier'>/vivo</font>, que solo confirma que el proceso "
        "responde, y <b>no</b> a <font face='Courier'>/salud</font>, que "
        "consulta la base. Con la comprobación atada a la base, un fallo "
        "pasajero de la base tumba también los despliegues y puede hacer que "
        "el proveedor retire un servicio que funcionaba."))
    return bloque


# ===========================================================================
# 8. Documentación técnica de la API
# ===========================================================================
def documentacion_api():
    total = sum(len(v) for v in ENDPOINTS.values())
    bloque = [h1("8. Documentación técnica de la API")]
    bloque.append(p(
        "La API expone <b>%d operaciones</b> repartidas en %d grupos, versión "
        "%s. El listado que sigue se genera leyendo la especificación OpenAPI "
        "que publica la propia aplicación, así que no puede quedarse atrás "
        "del código."
        % (total, len(ENDPOINTS), VERSION_API)))
    bloque.append(p(
        "La documentación interactiva está siempre disponible en "
        "<font face='Courier'>/docs</font>, donde además se puede probar cada "
        "ruta. La columna <b>Token</b> indica si la operación exige haber "
        "iniciado sesión."))

    for etiqueta, operaciones in ENDPOINTS.items():
        bloque.append(h3("%s (%d operaciones)" % (etiqueta, len(operaciones))))
        bloque.append(tabla(
            ["Método", "Ruta", "Qué hace", "Token"],
            [["<b>%s</b>" % o["metodo"],
              "<font face='Courier'>%s</font>" % o["ruta"],
              o["resumen"] or "—",
              "Sí" if o["protegido"] else "No"] for o in operaciones],
            [ANCHO_UTIL * 0.11, ANCHO_UTIL * 0.37, ANCHO_UTIL * 0.42,
             ANCHO_UTIL * 0.10]))
    bloque.append(Paragraph(
        "Tabla 11. Catálogo completo de endpoints.", ESTILOS["pie"]))

    bloque.append(h2("8.1 Formato de las respuestas"))
    bloque.append(p(
        "Todas las respuestas son JSON. Los nombres viajan en "
        "<i>camelCase</i> aunque en Python se escriban con guion bajo: es la "
        "convención de JavaScript, y traducirlos en un solo sitio evita que "
        "cada pantalla lo haga a su manera."))
    bloque.append(p(
        "Los errores tienen siempre la misma forma, de modo que el cliente "
        "puede tratarlos sin adivinar. El campo "
        "<font face='Courier'>codigo</font> es estable y sirve para decidir; "
        "<font face='Courier'>mensaje</font> está redactado para leerse; "
        "<font face='Courier'>detalles</font> dice qué campo concreto falla, "
        "cuando se puede señalar uno."))

    bloque.append(h2("8.2 Ejemplo: iniciar sesión"))
    bloque.append(p("<b>Petición</b>"))
    bloque.append(codigo([
        "POST /api/auth/login",
        "Content-Type: application/json",
        "",
        "{",
        '  "correo": "admin@autoprime.com.co",',
        '  "password": "Admin2026!"',
        "}",
    ]))
    bloque.append(p("<b>Respuesta 200</b>"))
    bloque.append(codigo([
        "{",
        '  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",',
        '  "usuario": {',
        '    "id": 1,',
        '    "nombre": "Jose Matias",',
        '    "apellido": "Agudelo Bolivar",',
        '    "correo": "admin@autoprime.com.co",',
        '    "rol": "administrador"',
        "  }",
        "}",
    ]))
    bloque.append(p(
        "El token se envía después en cada petición protegida con la cabecera "
        "<font face='Courier'>Authorization: Bearer &lt;token&gt;</font>. "
        "Lleva dentro el usuario, su rol y la caducidad, y va firmado: eso es "
        "lo que impide alterarlo."))

    bloque.append(h2("8.3 Ejemplo: registrar una venta"))
    bloque.append(p("<b>Petición</b>"))
    bloque.append(codigo([
        "POST /api/ventas",
        "Authorization: Bearer <token de empleado o administrador>",
        "",
        "{",
        '  "usuarioId": 12,',
        '  "estado": "pendiente",',
        '  "lineas": [',
        '    { "productoId": 3, "cantidad": 1 },',
        '    { "servicioId": 2, "cantidad": 1 }',
        "  ]",
        "}",
    ]))
    bloque.append(p("<b>Respuesta 201</b> (recortada)"))
    bloque.append(codigo([
        "{",
        '  "venta": {',
        '    "id": 36,',
        '    "numero": "V-2026-00073",',
        '    "subtotal": 4800000000.00,',
        '    "impuestos": 912000000.00,',
        '    "total": 5712000000.00,',
        '    "estado": "pendiente"',
        "  }",
        "}",
    ]))
    bloque.append(p(
        "Obsérvese que la petición <b>no manda importes</b>. Los calcula el "
        "servidor a partir del catálogo. Si los aceptara del cliente, "
        "cambiar un número con las herramientas del navegador cambiaría el "
        "precio de una venta."))

    bloque.append(h2("8.4 Ejemplo: un error de validación"))
    bloque.append(codigo([
        "POST /api/auth/registro   ->   422",
        "",
        "{",
        '  "codigo": "datos_invalidos",',
        '  "mensaje": "Los datos enviados no cumplen el formato esperado.",',
        '  "ruta": "/api/auth/registro",',
        '  "detalles": [',
        '    { "campo": "telefono", "problema": "String should match ..." },',
        '    { "campo": "correo",   "problema": "value is not a valid ..." }',
        "  ]",
        "}",
    ]))
    bloque.append(p(
        "<font face='Courier'>detalles</font> nombra el campo tal como lo "
        "conoce el cliente, y por eso el formulario puede marcar la casilla "
        "exacta en lugar de mostrar un aviso genérico. Los conflictos (un "
        "correo o un documento ya registrados, que responden 409) usan la "
        "misma estructura por el mismo motivo."))
    return bloque


# ===========================================================================
# 9. Manual de usuario
# ===========================================================================
def manual_usuario():
    bloque = [h1("9. Manual de usuario")]
    bloque.append(p(
        "Las capturas de este apartado no son ilustraciones: se tomaron "
        "ejecutando el sistema con datos dentro, de forma automatizada, y se "
        "pueden volver a generar con "
        "<font face='Courier'>herramientas/capturas_quinta.py</font>."))

    bloque.append(h2("9.1 Entrar al sistema"))
    bloque.append(p(
        "Desde <b>Mi cuenta</b> se llega al acceso. Quien no tiene cuenta "
        "puede crearla desde ahí mismo: el formulario valida mientras se "
        "escribe —si algo falta, dice cuál es y lleva el foco hasta él— y la "
        "contraseña muestra su nivel de seguridad. Si se olvida, se pide un "
        "enlace de recuperación que llega por correo y caduca."))
    bloque.append(p(
        "Según el rol de la cuenta, el menú lateral enseña unas opciones u "
        "otras. Conviene insistir en algo: ese menú es una comodidad, no la "
        "defensa. Aunque alguien escribiera a mano la dirección de una "
        "pantalla que no le corresponde, la API no le devolvería los datos."))

    bloque.append(h2("9.2 El tablero del administrador"))
    bloque.append(p(
        "Es la pantalla que resume el negocio. Arriba, los indicadores del "
        "periodo elegido, cada uno con su variación frente al periodo "
        "anterior — que es lo que convierte un número en una noticia. Debajo, "
        "los ingresos día a día y el desglose por estado."))
    bloque += captura(
        "q01-tablero-ingresos",
        "Figura 3. Tablero administrativo. Los botones PDF y EXCEL descargan "
        "el mismo informe en los dos formatos.")
    bloque.append(p(
        "La gráfica de ingresos <b>solo cuenta lo cobrado</b>: una venta "
        "anulada no ingresó nada, y contarla daría una cifra que no existe. "
        "El selector de periodo (hoy, 7, 30 o 90 días) vuelve a pedir los "
        "datos al servidor; no filtra en el navegador lo que ya tenía."))

    bloque.append(h2("9.3 Registrar una venta"))
    bloque.append(p(
        "En <b>Ventas</b>, el empleado busca al cliente, añade las líneas "
        "desde el catálogo y guarda. El subtotal, el IVA y el total los "
        "calcula el servidor: la pantalla los muestra, no los decide."))
    bloque += captura(
        "q04-ventas-listado",
        "Figura 4. Listado de ventas con filtros por estado, buscador y "
        "paginación.")

    bloque.append(h2("9.4 Emitir y descargar una factura"))
    bloque.append(p(
        "Desde una venta se emite su factura, que recibe numeración propia. "
        "El PDF se genera en el momento y refleja el estado del momento."))
    bloque += captura(
        "q07-factura-pdf",
        "Figura 5. Factura en PDF: banda de estado, bloque fiscal, desglose "
        "del IVA, importe en letras y código de verificación.")
    bloque.append(p(
        "El importe en letras lo compone un conversor propio. Parece un "
        "detalle menor y no lo es: los números en letras tienen más casos "
        "particulares de los que parece —el apócope de «uno», el salto del "
        "millón, la concordancia— y por eso tiene sus propias pruebas."))

    bloque.append(h2("9.5 Atención al cliente (PQR)"))
    bloque.append(p(
        "El cliente radica su petición, queja o reclamo y recibe un número de "
        "radicado. Desde el atelier se responde y se decide en qué estado "
        "queda el caso: responder sin decir si se cierra deja el asunto a "
        "medias, así que las dos cosas se eligen a la vez."))
    bloque += captura(
        "q10-pqr-listado",
        "Figura 6. Solicitudes radicadas, con su número, tipo y estado.")

    bloque.append(h2("9.6 El asistente"))
    bloque.append(p(
        "El botón flotante abre un chat que responde sobre el catálogo, los "
        "servicios y cómo agendar. Está construido para no inventar: cuando "
        "no tiene el dato, dice dónde conseguirlo en lugar de improvisar una "
        "respuesta. Si la clave del modelo no está configurada, avisa y "
        "ofrece los canales de contacto en vez de fallar en silencio."))
    bloque += captura(
        "q12-chat-asistente",
        "Figura 7. El asistente responde con los modelos reales del catálogo, "
        "leídos de la base de datos.")

    bloque.append(h2("9.7 Lo que ve un cliente"))
    bloque.append(p(
        "El cliente entra a la misma aplicación y ve otra cosa: sus compras, "
        "sus citas y sus PQR. El filtro por dueño lo aplica la API, no la "
        "pantalla."))
    bloque += captura(
        "q14-panel-cliente",
        "Figura 8. Panel del cliente. Ni rastro de las operaciones de otros.")
    return bloque


# ===========================================================================
# 10. Pruebas realizadas
# ===========================================================================
def pruebas():
    bloque = [h1("10. Pruebas realizadas")]
    bloque.append(p(
        "El sistema se comprueba en tres niveles distintos, y cada uno cubre "
        "lo que los otros no pueden."))
    bloque.append(tabla(
        ["Nivel", "Herramienta", "Qué cubre", "Resultado"],
        [
            ["Unitarias y de integración", "pytest + pytest-asyncio",
             "La lógica de negocio contra una base en memoria: ventas, "
             "facturas, informes, PQR, chat, números en letras, documentos "
             "seguros y endurecimiento.",
             "<b>175 pruebas, 0 fallos</b>"],
            ["Extremo a extremo (HTTP)", "pruebas_api.py",
             "La API contra MySQL de verdad, con los cinco métodos. Cubre lo "
             "que SQLite no puede: tipos ENUM, claves ajenas reales y que el "
             "esquema tenga las columnas que el modelo declara.",
             "<b>81 comprobaciones</b>"],
            ["Batería de peticiones", "Postman / Newman",
             "La colección que se entrega, generada del propio OpenAPI y "
             "ejecutable desde la línea de órdenes.",
             "<b>69 peticiones, 62 comprobaciones, 0 fallos</b>"],
        ],
        [ANCHO_UTIL * 0.20, ANCHO_UTIL * 0.18, ANCHO_UTIL * 0.42,
         ANCHO_UTIL * 0.20]))
    bloque.append(Paragraph("Tabla 12. Niveles de prueba y resultados.",
                            ESTILOS["pie"]))

    bloque.append(h2("10.1 Pruebas automáticas"))
    bloque += captura(
        "q17-pruebas-pytest",
        "Figura 9. Ejecución de la suite, con el desglose por archivo.")

    bloque.append(h2("10.2 La colección de Postman"))
    bloque.append(p(
        "Se genera a partir de la especificación OpenAPI de la propia "
        "aplicación, de modo que la lista de rutas no puede quedarse atrás "
        "cuando se añade una. Se ejecuta desde la línea de órdenes:"))
    bloque.append(codigo([
        "npx newman run backend/postman/AutoPrime.postman_collection.json \\",
        "    -e backend/postman/AutoPrime.postman_environment.json",
    ]))
    bloque += captura(
        "q18-postman-newman",
        "Figura 10. Resultado de la batería completa.")

    bloque.append(h2("10.3 Pruebas de seguridad"))
    bloque.append(p(
        "La seguridad no se afirma: se comprueba. Estas son las tres "
        "comprobaciones que se ejecutan contra el sistema en marcha."))
    bloque.append(h3("Inyección SQL"))
    bloque.append(p(
        "Se envían cinco cargas clásicas contra el buscador, que es el sitio "
        "donde se intentaría. Ninguna llega a la sentencia: el texto viaja "
        "siempre como parámetro enlazado. Un 200 con cero resultados es la "
        "respuesta correcta —la cadena se buscó tal cual y no coincidió con "
        "nadie—; lo que no puede salir por ningún lado es un error 500."))
    bloque += captura(
        "q19-inyeccion-sql",
        "Figura 11. Las cinco cargas, y la tabla intacta después.")

    bloque.append(h3("Prueba de contraseñas por fuerza bruta"))
    bloque.append(p(
        "bcrypt protege el hash si alguien roba la tabla, pero no protege de "
        "que le pregunten al servidor mil veces por segundo. De eso se ocupa "
        "un límite de ocho intentos por minuto que cuenta <b>por origen y por "
        "correo</b>: contando solo por correo, quien va cambiando la "
        "dirección en cada intento —que es justo lo que hace quien prueba una "
        "clave común contra muchas cuentas— no gastaría nunca el cupo."))

    bloque.append(h3("Cabeceras de seguridad"))
    bloque.append(p(
        "Se leen del servidor en producción, que es donde importan."))
    bloque += captura(
        "q22-cabeceras",
        "Figura 12. Cabeceras del despliegue real y estado del cifrado con "
        "la base.")

    bloque.append(h2("10.4 Defectos encontrados y corregidos"))
    bloque.append(p(
        "Las pruebas sirven cuando encuentran algo. Estos son los defectos "
        "que destaparon y que están corregidos:"))
    bloque.append(tabla(
        ["Defecto", "Cómo se detectó", "Corrección"],
        [
            ["El informe diario salía vacío a partir de las 19:00.",
             "Comparando la hora del servidor con la local.",
             "Un único módulo de fechas fija la zona horaria de Bogotá para "
             "todo el sistema."],
            ["El enlace con la base viajaba sin cifrar en producción.",
             "Consultando <font face='Courier'>Ssl_cipher</font> en la propia "
             "base.",
             "Configuración explícita de TLS con certificado verificado, y "
             "<font face='Courier'>/salud</font> informa del estado."],
            ["El Excel convertía el texto de un cliente en fórmula viva.",
             "Prueba con una carga de inyección de fórmulas.",
             "El texto se escribe siempre como texto y se antepone un "
             "apóstrofo a lo que empiece por un carácter peligroso."],
            ["Un PDF con etiquetas sin cerrar en el texto rompía la descarga.",
             "Prueba con marcado inválido en un campo libre.",
             "Escape de todo el texto que entra en los documentos."],
            ["Una comprobación de Postman llevaba días en rojo.",
             "Al hacer que la evidencia mostrara el resumen de newman y no "
             "solo el principio.",
             "La comprobación ya no cuenta claves: verifica que estén las "
             "cifras que el tablero necesita."],
            ["El registro pedía revisar «los campos en rojo» sin que hubiera "
             "ninguno.",
             "Reproduciendo el formulario con todo relleno menos la casilla "
             "de términos.",
             "El aviso nombra lo que falta, el foco salta al campo y la "
             "casilla se marca como cualquier otro."],
        ],
        [ANCHO_UTIL * 0.32, ANCHO_UTIL * 0.32, ANCHO_UTIL * 0.36]))
    bloque.append(Paragraph(
        "Tabla 13. Defectos detectados por las pruebas y su corrección.",
        ESTILOS["pie"]))
    return bloque


# ===========================================================================
# 11. Conclusiones y recomendaciones
# ===========================================================================
def conclusiones():
    bloque = [h1("11. Conclusiones y recomendaciones")]

    bloque.append(h2("11.1 Conclusiones"))
    bloque += numerada([
        "<b>Separar la interfaz de la API fue la decisión más rentable.</b> "
        "Que el navegador no toque nunca la base obliga a que toda regla viva "
        "en un solo sitio, y eso es lo que permite que la misma comprobación "
        "valga para la pantalla, para Postman y para un script.",
        "<b>La validación tiene que estar en los dos lados, y por motivos "
        "distintos.</b> En el navegador es comodidad: avisa antes de enviar. "
        "En el servidor es la defensa, porque una petición puede llegar sin "
        "pasar por ningún formulario.",
        "<b>Lo que no se comprueba, no está.</b> Los defectos de la tabla 13 "
        "no los encontró una revisión a ojo: los encontró ejecutar el sistema "
        "y mirar la salida real. Dos de ellos —la zona horaria y el cifrado "
        "de la base— no daban ningún error visible.",
        "<b>Generar los documentos en el servidor evitó duplicar los "
        "cálculos.</b> La factura, el informe en PDF y el informe en Excel "
        "salen de la misma función de negocio. Si el IVA cambiara, cambiaría "
        "en los tres a la vez.",
        "<b>Desplegar temprano enseña problemas que en local no existen.</b> "
        "La zona horaria, el cifrado de la base y la comprobación de salud "
        "atada a la base solo aparecieron al poner el sistema en internet.",
    ])

    bloque.append(h2("11.2 Recomendaciones para una futura versión"))
    bloque += numerada([
        "<b>Pasar la autorización a permisos finos.</b> Hoy se decide por el "
        "nombre del rol, que basta con tres. El vocabulario ya está en la "
        "tabla <font face='Courier'>permisos</font>; faltaría enlazarlo y "
        "comprobar el permiso en lugar del rol.",
        "<b>Añadir migraciones de esquema (Alembic).</b> Ahora el esquema se "
        "crea desde cero con un script. Con datos reales en producción hace "
        "falta poder evolucionarlo sin perderlos.",
        "<b>Registrar auditoría de las operaciones sensibles.</b> Quién anuló "
        "una factura y cuándo es una pregunta que hoy no tiene respuesta.",
        "<b>Cubrir el frontend con pruebas automáticas.</b> Las 175 pruebas "
        "cubren el backend; la interfaz se comprueba a mano. Una suite con "
        "Vitest y Testing Library cerraría ese hueco.",
        "<b>Integrar una pasarela de pago</b> cuando el proyecto salga del "
        "ámbito formativo, para que el estado «pagada» lo confirme el "
        "recaudador y no una persona.",
        "<b>Limpiar la tabla <font face='Courier'>rol_permiso</font></b>, que "
        "sigue existiendo en la base pero ya no tiene modelo que la use "
        "(apartado 5.3). O se retoma con la recomendación 1, o se retira.",
    ])
    return bloque


# ===========================================================================
# 12. Anexos
# ===========================================================================
def anexos():
    bloque = [h1("12. Anexos")]

    bloque.append(h2("12.1 Enlaces"))
    bloque.append(tabla(
        ["Recurso", "Dirección"],
        [
            ["Repositorio del proyecto",
             "<font face='Courier'>%s</font>" % REPOSITORIO],
            ["API desplegada",
             "<font face='Courier'>%s</font>" % API_PUBLICA],
            ["Documentación interactiva de la API",
             "<font face='Courier'>%s/docs</font>" % API_PUBLICA],
            ["Estado del servicio",
             "<font face='Courier'>%s/salud</font>" % API_PUBLICA],
        ],
        [ANCHO_UTIL * 0.38, ANCHO_UTIL * 0.62]))
    bloque.append(Paragraph("Tabla 14. Enlaces del proyecto.", ESTILOS["pie"]))

    bloque.append(h2("12.2 Cuentas de demostración"))
    bloque.append(p(
        "Creadas por <font face='Courier'>preparar_base.py</font> para poder "
        "probar el sistema. Son cuentas de demostración de un proyecto "
        "formativo, sin datos reales de nadie."))
    bloque.append(tabla(
        ["Rol", "Correo", "Contraseña"],
        [
            ["Administrador", "admin@autoprime.com.co", "Admin2026!"],
            ["Empleado", "empleado@autoprime.com.co", "Empleado2026!"],
            ["Cliente", "cliente@autoprime.com.co", "Cliente2026!"],
        ],
        [ANCHO_UTIL * 0.25, ANCHO_UTIL * 0.45, ANCHO_UTIL * 0.30]))
    bloque.append(Paragraph("Tabla 15. Cuentas de acceso para la revisión.",
                            ESTILOS["pie"]))

    bloque.append(h2("12.3 Dependencias del backend"))
    bloque.append(tabla(
        ["Paquete", "Versión"],
        [["<font face='Courier'>%s</font>" % n, v]
         for n, v in DEPENDENCIAS_BACKEND],
        [ANCHO_UTIL * 0.55, ANCHO_UTIL * 0.45]))
    bloque.append(Paragraph(
        "Tabla 16. Dependencias de Python, con versión fija.", ESTILOS["pie"]))

    normales, desarrollo = DEPENDENCIAS_FRONTEND
    bloque.append(h2("12.4 Dependencias del frontend"))
    bloque.append(tabla(
        ["Paquete", "Versión", "Uso"],
        [["<font face='Courier'>%s</font>" % n, v, "Producción"]
         for n, v in normales]
        + [["<font face='Courier'>%s</font>" % n, v, "Desarrollo"]
           for n, v in desarrollo],
        [ANCHO_UTIL * 0.45, ANCHO_UTIL * 0.25, ANCHO_UTIL * 0.30]))
    bloque.append(Paragraph("Tabla 17. Dependencias de Node.", ESTILOS["pie"]))

    bloque.append(h2("12.5 Otras evidencias entregadas"))
    bloque += vinetas([
        "<b>Evidencias del quinto avance</b> (PDF) — 22 capturas del sistema "
        "en marcha, organizadas por lo que demuestran.",
        "<b>Lista de chequeo</b> (Excel) — el instrumento con cada captura "
        "pegada en su casilla.",
        "<b>Colección de Postman</b> — "
        "<font face='Courier'>backend/postman/</font>, con su entorno y su "
        "archivo de instrucciones.",
        "<b>Muestras de documentos generados</b> — "
        "<font face='Courier'>evidencias/muestras/</font>: una factura y un "
        "informe en PDF, y un informe en Excel.",
    ])

    bloque.append(h2("12.6 Cómo se generó este manual"))
    bloque.append(p(
        "Este documento se compone con "
        "<font face='Courier'>herramientas/manual_tecnico.py</font>. El "
        "diccionario de datos, el diagrama entidad-relación, el catálogo de "
        "endpoints, las dependencias y las variables de entorno <b>se leen "
        "del proyecto</b> al generarlo, no están transcritos. Volver a "
        "lanzarlo deja el manual al día con el código."))
    bloque.append(p(
        "Lo que sí está escrito a mano es lo que no puede deducirse del "
        "código: el problema que resuelve, los objetivos, el alcance, las "
        "decisiones de diseño y estas conclusiones."))
    return bloque


# ===========================================================================
def relato_completo():
    """Todas las secciones, en el orden que pide la solicitud."""
    piezas = []
    piezas += portada()
    piezas += contenido()
    piezas += introduccion()
    piezas += objetivos()
    piezas += alcance()
    piezas += [PageBreak()]
    piezas += arquitectura()
    piezas += [PageBreak()]
    piezas += modelo_datos()
    piezas += [PageBreak()]
    piezas += diseno()
    piezas += [PageBreak()]
    piezas += instalacion()
    piezas += [PageBreak()]
    piezas += documentacion_api()
    piezas += [PageBreak()]
    piezas += manual_usuario()
    piezas += [PageBreak()]
    piezas += pruebas()
    piezas += [PageBreak()]
    piezas += conclusiones()
    piezas += [PageBreak()]
    piezas += anexos()
    return piezas
