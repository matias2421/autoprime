# -*- coding: utf-8 -*-
"""Genera la coleccion de Postman a partir del OpenAPI de la propia API.

Escribirla a mano seria escribir dos veces la misma lista de endpoints, y a
la segunda semana una de las dos estaria desactualizada. Aqui se lee el
esquema que FastAPI ya publica, asi que la coleccion no puede quedarse atras:
si se anade un endpoint, aparece al regenerarla.

Lo que si va a mano son las pruebas de cada peticion, porque eso es lo que un
esquema no sabe: que el login guarde el token, que un cliente reciba 403 en
lo del personal, que el precio que devuelve la venta sea el del catalogo.
"""

import io
import json
import sys
from pathlib import Path

# Rutas relativas a este archivo: el generador tiene que correr en
# cualquier maquina donde se clone el proyecto, no solo en la que lo
# escribio.
RAIZ = Path(__file__).resolve().parent.parent
BACKEND = RAIZ / "backend"
sys.path.insert(0, str(BACKEND))

from app.main import app  # noqa: E402

SALIDA = BACKEND / "postman" / "AutoPrime.postman_collection.json"
ENTORNO = BACKEND / "postman" / "AutoPrime.postman_environment.json"

esquema = app.openapi()

# ---------------------------------------------------------------- cuerpos ---
# Ejemplos por endpoint. Van aqui y no en el esquema porque muchos dependen de
# variables que solo existen al correr la coleccion ({{ventaId}}).
CUERPOS = {
    ("post", "/api/auth/login"): {
        "correo": "{{correoAdmin}}", "password": "{{claveAdmin}}"
    },
    ("post", "/api/auth/registro"): {
        "nombre": "Prueba", "apellido": "Postman", "tipoDocumento": "CC",
        "numeroDocumento": "{{documentoNuevo}}", "direccion": "Calle 1 # 2-3",
        "telefono": "3001112233", "correo": "{{correoNuevo}}",
        "password": "Postman2026!", "confirmarPassword": "Postman2026!",
    },
    ("post", "/api/auth/recuperar"): {"correo": "{{correoAdmin}}"},
    ("post", "/api/ventas"): {
        "usuarioId": "{{clienteId}}",
        "lineas": [{"productoId": "{{productoId}}", "cantidad": 1}],
    },
    ("patch", "/api/ventas/{venta_id}/estado"): {"estado": "pagada"},
    ("post", "/api/pqr"): {
        "tipo": "reclamo",
        "asunto": "Prueba desde Postman",
        "descripcion": "Descripcion de prueba con mas de veinte caracteres.",
    },
    ("patch", "/api/pqr/{pqr_id}/responder"): {
        "respuesta": "Respuesta de prueba enviada desde Postman.",
        "estado": "respondida",
    },
    ("patch", "/api/pqr/{pqr_id}/estado"): {"estado": "cerrada"},
    ("post", "/api/chat/conversaciones"): {"titulo": "Prueba Postman"},
    ("post", "/api/chat/conversaciones/{conversacion_id}/mensajes"): {
        "contenido": "Que vehiculos tienen disponibles?"
    },
    ("post", "/api/productos"): {
        "slug": "prueba-postman", "marca": "MANSORY", "modelo": "Prueba Postman",
        "familia": "gama", "base": "Unidad de prueba",
        "lema": "Creado por la bateria de Postman",
        "descripcion": "Vehiculo de prueba que la coleccion crea y borra.",
        "imagen": "placeholder.webp", "anio": 2026, "precio": 100000000,
        "motor": "V8", "potencia": "500 hp", "aceleracion": "4.0 s",
        "velocidad": "300 km/h", "transmision": "Automatica", "traccion": "Integral",
    },
    ("put", "/api/productos/{producto_id}"): {"precio": 120000000},
    ("post", "/api/servicios"): {
        "nombre": "Servicio de prueba", "descripcion": "Creado por Postman",
        "duracionMin": 30, "precio": 50000,
    },
    ("put", "/api/servicios/{servicio_id}"): {"precio": 60000},
    ("post", "/api/citas"): {
        "servicioId": 1, "productoId": "{{productoId}}",
        "fecha": "{{fechaCita}}", "hora": "10:00:00",
    },
}

# ---------------------------------------------------------------- pruebas ---
# Esto es lo que convierte la coleccion en una bateria y no en una lista de
# enlaces: cada peticion comprueba algo y, cuando hace falta, guarda un id
# para la siguiente.
GUARDAR_TOKEN = """pm.test("Responde 200", () => pm.response.to.have.status(200));
pm.test("Devuelve token y usuario", () => {
    const d = pm.response.json();
    pm.expect(d).to.have.property("token");
    pm.expect(d.usuario).to.have.property("rol");
    pm.collectionVariables.set("token", d.token);
    pm.collectionVariables.set("rol", d.usuario.rol);
});"""

PRUEBAS = {
    ("post", "/api/auth/login"): GUARDAR_TOKEN,

    ("post", "/api/auth/registro"): """// 409 es correcto si la coleccion ya se corrio antes: la cuenta existe.
pm.test("Responde 201 o 409 si ya existia", () => {
    pm.expect(pm.response.code).to.be.oneOf([201, 409]);
});
if (pm.response.code === 201) {
    // Se guarda para que los PUT y DELETE de usuarios actuen sobre ESTA
    // cuenta y no sobre una de verdad.
    pm.collectionVariables.set("usuarioId", pm.response.json().usuario.id);
}""",

    ("get", "/api/auth/perfil"): """pm.test("Responde 200", () => pm.response.to.have.status(200));
pm.test("El perfil viene dentro de 'usuario'", () => {
    // El frontend lee datos.usuario; devolverlo suelto cerraba la sesion al
    // recargar la pagina, y es un fallo que solo se ve recargando.
    pm.expect(pm.response.json()).to.have.property("usuario");
});""",

    ("get", "/api/productos"): """pm.test("Responde 200", () => pm.response.to.have.status(200));
pm.test("El catalogo trae vehiculos", () => {
    const d = pm.response.json();
    pm.expect(d.productos).to.be.an("array").that.is.not.empty;
    const disponible = d.productos.find(p => p.estado === "disponible" && p.precio);
    pm.expect(disponible, "hace falta un vehiculo disponible con precio").to.exist;
    pm.collectionVariables.set("productoId", disponible.id);
    pm.collectionVariables.set("precioProducto", disponible.precio);
});""",

    ("post", "/api/productos"): """pm.test("Responde 201", () => pm.response.to.have.status(201));
pm.test("Guarda el vehiculo creado para editarlo y borrarlo despues", () => {
    pm.collectionVariables.set("productoCreadoId", pm.response.json().producto.id);
});""",

    ("post", "/api/servicios"): """pm.test("Responde 201", () => pm.response.to.have.status(201));
pm.test("Guarda el servicio creado", () => {
    pm.collectionVariables.set("servicioId", pm.response.json().servicio.id);
});""",

    ("get", "/api/usuarios/clientes"): """pm.test("Responde 200", () => pm.response.to.have.status(200));
pm.test("Solo devuelve lo justo para elegir comprador", () => {
    const c = pm.response.json().clientes[0];
    pm.expect(c).to.have.all.keys("id", "nombre", "apellido", "documento", "correo");
    pm.collectionVariables.set("clienteId", c.id);
});""",

    ("post", "/api/ventas"): """pm.test("Responde 201", () => pm.response.to.have.status(201));
pm.test("El precio sale del catalogo, no del cuerpo", () => {
    const v = pm.response.json().venta;
    pm.expect(v.lineas[0].precioUnitario)
      .to.eql(Number(pm.collectionVariables.get("precioProducto")));
});
pm.test("El total lleva el IVA del 19%", () => {
    const v = pm.response.json().venta;
    pm.expect(v.total).to.be.closeTo(v.subtotal * 1.19, 1);
});
pm.test("El consecutivo no es el provisional", () => {
    const v = pm.response.json().venta;
    pm.expect(v.numero).to.match(/^V-\\d{4}-\\d{5}$/);
    pm.collectionVariables.set("ventaId", v.id);
});""",

    ("get", "/api/ventas"): """pm.test("Responde 200", () => pm.response.to.have.status(200));
pm.test("Viene paginado y el total no es el de la pagina", () => {
    const d = pm.response.json();
    pm.expect(d).to.have.property("pagina");
    pm.expect(d.pagina.total).to.eql(d.total);
});""",

    ("post", "/api/facturas/venta/{venta_id}"): """pm.test("Responde 201", () => pm.response.to.have.status(201));
pm.test("La factura copia el detalle de la venta", () => {
    const f = pm.response.json().factura;
    pm.expect(f.lineas).to.be.an("array").that.is.not.empty;
    pm.expect(f.numero).to.match(/^F-\\d{4}-\\d{5}$/);
    pm.collectionVariables.set("facturaId", f.id);
});""",

    ("get", "/api/facturas/{factura_id}/pdf"): """pm.test("Responde 200", () => pm.response.to.have.status(200));
pm.test("Es un PDF de verdad", () => {
    pm.expect(pm.response.headers.get("Content-Type")).to.include("application/pdf");
    // %PDF- son los cinco primeros bytes de cualquier PDF.
    pm.expect(pm.response.text().slice(0, 5)).to.eql("%PDF-");
});
pm.test("Se descarga con nombre", () => {
    pm.expect(pm.response.headers.get("Content-Disposition")).to.include("attachment");
});""",

    ("get", "/api/reportes/ventas"): """pm.test("Responde 200", () => pm.response.to.have.status(200));
pm.test("Sin fechas, el reporte es el de hoy", () => {
    const r = pm.response.json().reporte;
    pm.expect(r.rango.dias).to.eql(1);
    pm.expect(r.porDia).to.have.lengthOf(1);
});
pm.test("Dice de quien son las cifras", () => {
    pm.expect(pm.response.json().reporte.alcance).to.be.a("string").that.is.not.empty;
});""",

    ("get", "/api/reportes/ventas/excel"): """pm.test("Responde 200", () => pm.response.to.have.status(200));
pm.test("Es un libro de Excel", () => {
    // Un .xlsx es un zip: empieza por PK.
    pm.expect(pm.response.text().slice(0, 2)).to.eql("PK");
});""",

    # No se cuentan las claves. Contarlas parece mas estricto, pero lo unico
    # que consigue es romperse cada vez que el panel crece —que es lo que
    # paso al pasar de ocho cifras a catorce— sin haber detectado nunca nada.
    # Se comprueba que estan las que el panel necesita y que son numeros, que
    # es lo que de verdad lo dejaria inservible si faltara.
    ("get", "/api/reportes/panel"): """pm.test("Responde 200", () => pm.response.to.have.status(200));
pm.test("Trae las cifras del negocio, y son numeros", () => {
    const panel = pm.response.json().panel;
    [
        "ventasHoy", "ingresosHoy", "ventasPorCobrar", "importePorCobrar",
        "ventasSinFacturar", "citasPendientes", "pqrAbiertas",
        "usuariosActivos", "vehiculosDisponibles", "facturasEmitidas",
    ].forEach((clave) => {
        pm.expect(panel, clave).to.have.property(clave);
        pm.expect(panel[clave], clave).to.be.a("number");
    });
});""",

    ("post", "/api/pqr"): """pm.test("Responde 201", () => pm.response.to.have.status(201));
pm.test("Nace pendiente y con radicado", () => {
    const p = pm.response.json().pqr;
    pm.expect(p.estado).to.eql("pendiente");
    pm.expect(p.numero).to.match(/^P-\\d{4}-\\d{5}$/);
    pm.collectionVariables.set("pqrId", p.id);
});""",

    ("post", "/api/citas"): """pm.test("Responde 201", () => pm.response.to.have.status(201));
pm.test("Guarda la cita para reprogramarla y borrarla despues", () => {
    pm.collectionVariables.set("citaId", pm.response.json().cita.id);
});""",

    ("get", "/api/chat/estado"): """pm.test("Responde 200", () => pm.response.to.have.status(200));
pm.test("Dice si el asistente esta disponible", () => {
    pm.expect(pm.response.json()).to.have.property("disponible");
});""",

    ("post", "/api/chat/conversaciones"): """pm.test("Responde 201", () => pm.response.to.have.status(201));
pm.test("Guarda el hilo", () => {
    pm.collectionVariables.set("conversacionId", pm.response.json().conversacion.id);
});""",

    ("get", "/salud"): """pm.test("Responde 200", () => pm.response.to.have.status(200));
pm.test("La base responde", () => {
    pm.expect(pm.response.json().base_datos).to.eql("conectada");
});
pm.test("Cada respuesta trae su identificador", () => {
    // Lo pone el middleware; sirve para encontrar la peticion en el registro.
    pm.expect(pm.response.headers.has("X-Peticion-Id")).to.be.true;
});""",
}

# Peticiones extra que no salen del esquema: los casos que deben fallar.
NEGATIVAS = [
    # Esta carpeta no monta nada: se apoya en lo que dejaron las
    # anteriores. Puede hacerlo porque los borrados se movieron a la
    # carpeta de limpieza, que corre despues: cuando llega aqui, el
    # vehiculo sigue vendido y la venta sigue facturada, que es justo el
    # estado en el que estos casos tienen sentido.
    {
        "name": "Sin token -> 401 con WWW-Authenticate",
        "metodo": "GET", "ruta": "/api/ventas", "sin_token": True,
        "prueba": """pm.test("Responde 401", () => pm.response.to.have.status(401));
pm.test("Dice como autenticarse", () => {
    // La norma HTTP lo exige; sin eso, un cliente generico no sabe que debe
    // pedir un token en vez de rendirse.
    pm.expect(pm.response.headers.get("WWW-Authenticate")).to.eql("Bearer");
});
pm.test("El error trae el formato de la API", () => {
    const d = pm.response.json();
    pm.expect(d).to.have.all.keys("codigo", "mensaje", "ruta", "detalles");
});""",
    },
    {
        "name": "Token invalido -> 401",
        "metodo": "GET", "ruta": "/api/ventas", "sin_token": True,
        "cabeceras": [{"key": "Authorization", "value": "Bearer basura"}],
        "prueba": """pm.test("Responde 401", () => pm.response.to.have.status(401));""",
    },
    {
        "name": "Vender sin lineas -> 422 diciendo que campo",
        "metodo": "POST", "ruta": "/api/ventas", "cuerpo": {"lineas": []},
        "prueba": """pm.test("Responde 422", () => pm.response.to.have.status(422));
pm.test("Senala el campo, no solo que algo fallo", () => {
    const d = pm.response.json();
    pm.expect(d.detalles).to.be.an("array").that.is.not.empty;
    pm.expect(d.detalles[0]).to.have.all.keys("campo", "problema");
});""",
    },
    {
        "name": "Vender el mismo vehiculo dos veces -> 409",
        "metodo": "POST", "ruta": "/api/ventas",
        "cuerpo": {"lineas": [{"productoId": "{{productoId}}"}]},
        "prueba": """pm.test("Responde 409", () => pm.response.to.have.status(409));
pm.test("Con el codigo del dominio", () => {
    pm.expect(pm.response.json().codigo).to.eql("vehiculo_no_disponible");
});""",
    },
    {
        "name": "Facturar dos veces la misma venta -> 409",
        "metodo": "POST", "ruta": "/api/facturas/venta/{{ventaId}}",
        "prueba": """pm.test("Responde 409", () => pm.response.to.have.status(409));
pm.test("Una venta, una factura", () => {
    pm.expect(pm.response.json().codigo).to.eql("venta_ya_facturada");
});""",
    },
    {
        "name": "Borrar una venta ya facturada -> 409",
        "metodo": "DELETE", "ruta": "/api/ventas/{{ventaId}}",
        "prueba": """pm.test("Responde 409", () => pm.response.to.have.status(409));
pm.test("El consecutivo no puede quedar con huecos", () => {
    pm.expect(pm.response.json().codigo).to.eql("venta_con_factura");
});""",
    },
    {
        "name": "Pedir mas filas de la cuenta -> 422",
        "metodo": "GET", "ruta": "/api/ventas?porPagina=5000",
        "prueba": """pm.test("Responde 422", () => pm.response.to.have.status(422));""",
    },
]


def variables_de(ruta: str) -> str:
    """Convierte /api/ventas/{venta_id} en /api/ventas/{{ventaId}}."""
    import re

    def camel(m):
        partes = m.group(1).split("_")
        return "{{" + partes[0] + "".join(p.capitalize() for p in partes[1:]) + "}}"

    ruta = re.sub(r"\{(\w+)\}", camel, ruta)

    # Lo destructivo sobre el catalogo apunta a lo que creo la coleccion.
    # Sin esto, `DELETE /api/productos/{{productoId}}` borraria un vehiculo
    # del catalogo de verdad, porque `productoId` lo llena el listado.
    if "/api/productos/" in ruta:
        ruta = ruta.replace("{{productoId}}", "{{productoCreadoId}}")
    return ruta


def peticion(metodo: str, ruta: str, detalle: dict) -> dict:
    cuerpo = CUERPOS.get((metodo, ruta))
    prueba = PRUEBAS.get((metodo, ruta))
    # Quien necesita token lo dice el propio esquema, operacion por
    # operacion. Adivinarlo por prefijo de ruta estaba mal: `GET
    # /api/productos` es publico y `POST /api/productos` no, pero los dos
    # empiezan igual, asi que el alta de vehiculos salia sin cabecera y
    # respondia 401 en cada corrida.
    publico = not detalle.get("security")

    item = {
        "name": detalle.get("summary") or f"{metodo.upper()} {ruta}",
        "request": {
            "method": metodo.upper(),
            "header": ([] if publico else [
                {"key": "Authorization", "value": "Bearer {{token}}"}
            ]) + ([{"key": "Content-Type", "value": "application/json"}] if cuerpo else []),
            "url": {
                "raw": "{{baseUrl}}" + variables_de(ruta),
                "host": ["{{baseUrl}}"],
                "path": [p for p in variables_de(ruta).split("/") if p],
            },
            "description": (detalle.get("description") or "").strip(),
        },
        "response": [],
    }
    if cuerpo:
        item["request"]["body"] = {
            "mode": "raw",
            "raw": json.dumps(cuerpo, indent=2, ensure_ascii=False),
            "options": {"raw": {"language": "json"}},
        }
    if prueba:
        item["event"] = [{"listen": "test", "script": {"type": "text/javascript",
                                                       "exec": prueba.split("\n")}}]
    return item


# Se agrupan por la etiqueta que ya trae el esquema.
grupos: dict[str, list] = {}
for ruta, metodos in esquema["paths"].items():
    for metodo, detalle in metodos.items():
        etiqueta = (detalle.get("tags") or ["Sistema"])[0]
        grupos.setdefault(etiqueta, []).append(peticion(metodo, ruta, detalle))

# El orden de las carpetas es deliberado, no alfabetico.
#
# La bateria se corre en secuencia y cada carpeta deja preparado lo que
# necesita la siguiente: sin iniciar sesion no hay token, sin catalogo no hay
# vehiculo que vender, sin venta no hay factura que emitir. En orden
# alfabetico, "Facturas" corria antes que "Ventas" y se saltaba entera por
# falta de una venta a la que facturar.
ORDEN = [
    "Sistema",          # salud primero: si la base no responde, lo demas sobra
    "Autenticación",    # deja el token
    "Productos",        # deja un vehiculo del catalogo y uno propio
    "Servicios",
    "Usuarios",         # deja un cliente al que vender
    "Citas",
    "Ventas",           # deja una venta
    "Facturas",         # la factura de esa venta
    "Reportes",         # que ya tienen algo que reportar
    "PQR",
    "Asistente",
]

carpetas = [
    {"name": nombre, "item": grupos[nombre]}
    for nombre in ORDEN
    if nombre in grupos
]
# Por si el esquema gana una etiqueta nueva y nadie la anade a ORDEN.
carpetas += [
    {"name": nombre, "item": items}
    for nombre, items in sorted(grupos.items())
    if nombre not in ORDEN
]

# --------------------------------------------------------------- limpieza ---
#
# Los DELETE salen de sus carpetas y se juntan al final.
#
# El motivo es de orden: "Ventas" terminaba borrando su propia venta, y
# "Facturas" -que corre despues- se encontraba con un 404 al intentar
# facturarla. Una bateria que se corre en secuencia tiene que crear primero,
# ejercitar despues y recoger al final; con cada carpeta recogiendo lo suyo,
# la siguiente empieza con la mesa vacia.

limpieza = []
for carpeta in carpetas:
    borrados = [i for i in carpeta["item"] if i["request"]["method"] == "DELETE"]
    carpeta["item"] = [i for i in carpeta["item"] if i["request"]["method"] != "DELETE"]
    limpieza += borrados

for item in limpieza:
    if "/api/ventas/" in item["request"]["url"]["raw"]:
        # Esta puede no poder borrarse, y es correcto: si ya se le emitio
        # factura, el consecutivo no puede quedar con huecos. Se aceptan las
        # dos respuestas porque las dos son la API funcionando bien.
        item["event"] = [{"listen": "test", "script": {
            "type": "text/javascript", "exec": [
                'pm.test("Se borra, o se explica por que no", () => {',
                "    pm.expect(pm.response.code).to.be.oneOf([204, 409]);",
                "    if (pm.response.code === 409) {",
                "        pm.expect(pm.response.json().codigo).to.eql('venta_con_factura');",
                "    }",
                "});",
            ]}}]
    else:
        item["event"] = [{"listen": "test", "script": {
            "type": "text/javascript", "exec": [
                'pm.test("Responde 204 sin cuerpo, o 200", () => {',
                "    pm.expect(pm.response.code).to.be.oneOf([200, 204]);",
                "});",
            ]}}]


# La carpeta de casos que deben fallar va al final, con nombre explicito.
negativas = []
for caso in NEGATIVAS:
    cabeceras = caso.get("cabeceras", [])
    if not caso.get("sin_token"):
        cabeceras = [{"key": "Authorization", "value": "Bearer {{token}}"}] + cabeceras
    item = {
        "name": caso["name"],
        "request": {
            "method": caso["metodo"],
            "header": cabeceras + ([{"key": "Content-Type", "value": "application/json"}]
                                   if caso.get("cuerpo") else []),
            "url": {
                "raw": "{{baseUrl}}" + caso["ruta"],
                "host": ["{{baseUrl}}"],
                "path": [p for p in caso["ruta"].split("?")[0].split("/") if p],
            },
        },
        "event": [{"listen": "test", "script": {
            "type": "text/javascript", "exec": caso["prueba"].split("\n")}}],
        "response": [],
    }
    if caso.get("cuerpo"):
        item["request"]["body"] = {
            "mode": "raw",
            "raw": json.dumps(caso["cuerpo"], indent=2, ensure_ascii=False),
            "options": {"raw": {"language": "json"}},
        }
    if "?" in caso["ruta"]:
        consulta = caso["ruta"].split("?")[1]
        item["request"]["url"]["query"] = [
            {"key": k, "value": v}
            for k, v in (p.split("=") for p in consulta.split("&"))
        ]
    negativas.append(item)

carpetas.append({
    "name": "Casos que deben fallar",
    "description": (
        "Lo que NO debe poder hacerse. Una bateria que solo prueba el camino "
        "feliz no detecta que se cayo una comprobacion de permisos: el "
        "endpoint sigue respondiendo 200, solo que a quien no debia."
    ),
    "item": negativas,
})

carpetas.append({
    "name": "Limpieza",
    "description": (
        "Borra lo que creo la corrida. Va al final para que las carpetas "
        "anteriores encuentren lo que necesitan.\n\n"
        "La venta puede quedarse: si se le emitio factura, borrarla dejaria "
        "un hueco en el consecutivo, y la API lo impide a proposito. Contra "
        "el despliegue, conviene quitarla a mano de vez en cuando."
    ),
    "item": limpieza,
})

coleccion = {
    "info": {
        "name": "AutoPrime API",
        "description": (
            "Bateria de la API de AutoPrime (quinto avance).\n\n"
            "Generada a partir del OpenAPI que publica la propia aplicacion, "
            "asi que la lista de endpoints no puede quedarse atras.\n\n"
            "COMO CORRERLA\n"
            "1. Importa tambien el entorno (AutoPrime.postman_environment.json) "
            "y elige si apunta a local o al despliegue.\n"
            "2. Usa el Collection Runner en orden: la peticion de login guarda "
            "el token y las siguientes lo reutilizan; el catalogo guarda un "
            "vehiculo, la venta guarda su id, y asi.\n"
            "3. La ultima carpeta comprueba lo que debe fallar.\n\n"
            "Ojo: correr la coleccion entera crea filas de verdad (una venta, "
            "una factura, una PQR). Contra el despliegue, borrarlas despues."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "variable": [
        {"key": "baseUrl", "value": "http://127.0.0.1:8000"},
        {"key": "correoAdmin", "value": "admin@autoprime.com.co"},
        {"key": "claveAdmin", "value": "Admin2026!"},
        {"key": "correoNuevo", "value": "postman@autoprime.com.co"},
        {"key": "documentoNuevo", "value": "1099887766"},
        {"key": "token", "value": ""},
        {"key": "rol", "value": ""},
        {"key": "productoId", "value": ""},
        {"key": "productoCreadoId", "value": ""},
        {"key": "precioProducto", "value": ""},
        {"key": "clienteId", "value": ""},
        {"key": "ventaId", "value": ""},
        {"key": "facturaId", "value": ""},
        {"key": "pqrId", "value": ""},
        {"key": "conversacionId", "value": ""},
        # Los ids de lo que la coleccion NO crea arrancan vacios a
        # proposito. Con un "1" por defecto, `DELETE /api/usuarios/{id}`
        # apuntaba al administrador: correr la coleccion entera lo borraba.
        # Vacios, esas peticiones se saltan solas (ver el guion de abajo).
        {"key": "usuarioId", "value": ""},
        {"key": "servicioId", "value": ""},
        {"key": "citaId", "value": ""},
        {"key": "identificador", "value": ""},
        {"key": "fechaCita", "value": ""},
    ],
    "event": [{
        "listen": "prerequest",
        "script": {"type": "text/javascript", "exec": [
            "// Freno de mano.",
            "//",
            "// Una coleccion generada del OpenAPI trae tambien los DELETE y los",
            "// PUT, y sus ids hay que rellenarlos con algo. La primera version",
            "// los dejaba en 1, y al correrla entera borro el administrador de",
            "// la base: la peticion era correcta, el objetivo era real.",
            "//",
            "// Ahora la regla es que la bateria solo toca lo que ella misma ha",
            "// creado. Si el id que necesita una peticion sigue vacio, es que",
            "// nada en esta corrida lo lleno, y la peticion se salta.",
            "const url = pm.request.url.toString();",
            r"const pendiente = (url.match(/{{(\\w+)}}/g) || [])",
            "    .map(v => v.slice(2, -2))",
            "    .find(v => !pm.collectionVariables.get(v) && v !== 'baseUrl');",
            "if (pendiente) {",
            "    console.log(`Se salta ${pm.info.requestName}: falta ${pendiente}.`);",
            "    pm.execution.skipRequest();",
            "}",
            "",
            "// La fecha de la cita tiene que ser futura y no caer en domingo,",
            "// o el alta se rechaza con 422 y la prueba falla por el calendario",
            "// en vez de por la API.",
            "const d = new Date();",
            "d.setDate(d.getDate() + 3);",
            "if (d.getDay() === 0) d.setDate(d.getDate() + 1);",
            "pm.collectionVariables.set('fechaCita', d.toISOString().slice(0, 10));",
        ]},
    }],
    "item": carpetas,
}

entorno = {
    "name": "AutoPrime - local",
    "values": [
        {"key": "baseUrl", "value": "http://127.0.0.1:8000", "enabled": True},
        {"key": "baseUrlDespliegue",
         "value": "https://autoprime-api-z9b6.onrender.com", "enabled": False},
    ],
    "_postman_variable_scope": "environment",
}

SALIDA.parent.mkdir(parents=True, exist_ok=True)
io.open(SALIDA, "w", encoding="utf-8").write(
    json.dumps(coleccion, indent=2, ensure_ascii=False)
)
io.open(ENTORNO, "w", encoding="utf-8").write(
    json.dumps(entorno, indent=2, ensure_ascii=False)
)

total = sum(len(c["item"]) for c in carpetas)
con_pruebas = sum(1 for c in carpetas for i in c["item"] if i.get("event"))
print(f"  {len(carpetas)} carpetas, {total} peticiones, {con_pruebas} con pruebas")
for c in carpetas:
    print(f"    {c['name']:<24} {len(c['item'])}")
