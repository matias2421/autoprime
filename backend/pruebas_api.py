# -*- coding: utf-8 -*-
"""Pruebas de extremo a extremo contra la API en ejecución.

No usan pytest a propósito: ejercitan el servicio real por HTTP, igual que lo
hará el frontend o Postman, así que hace falta tener la API levantada:

    venv\\Scripts\\python -m uvicorn app.main:app --port 8000
    python pruebas_api.py

Cada prueba declara el código que espera; al final se imprime el recuento.
"""

import json
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

API = "http://127.0.0.1:8000"

correctas = 0
fallidas = 0
tokens: dict[str, str] = {}


def peticion(metodo: str, ruta: str, cuerpo=None, token: str | None = None):
    """Lanza una petición y devuelve (código, cuerpo decodificado)."""
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    pet = urllib.request.Request(API + ruta, data=datos, method=metodo)

    if datos is not None:
        pet.add_header("Content-Type", "application/json")
    if token:
        pet.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(pet, timeout=15) as respuesta:
            crudo = respuesta.read().decode()
            return respuesta.status, (json.loads(crudo) if crudo else None)
    except urllib.error.HTTPError as error:
        crudo = error.read().decode()
        try:
            return error.code, json.loads(crudo)
        except json.JSONDecodeError:
            return error.code, crudo


def probar(descripcion, esperado, metodo, ruta, cuerpo=None, token=None):
    """Ejecuta una prueba y anota el resultado."""
    global correctas, fallidas

    codigo, salida = peticion(metodo, ruta, cuerpo, token)

    if codigo == esperado:
        correctas += 1
        print(f"  OK   {codigo}  {metodo:6} {ruta:44} {descripcion}")
    else:
        fallidas += 1
        print(f"  FALLA esperaba {esperado} obtuvo {codigo}  {metodo} {ruta}")
        print(f"        {descripcion}")
        print(f"        {json.dumps(salida, ensure_ascii=False)[:180]}")

    return salida


def seccion(titulo):
    print()
    print("=" * 78)
    print(f" {titulo}")
    print("=" * 78)


# --------------------------------------------------------------------------
seccion("SISTEMA")
probar("presentacion de la API", 200, "GET", "/")
probar("salud y conexion a MySQL", 200, "GET", "/salud")
probar("ruta inexistente -> 404", 404, "GET", "/api/no-existe")

# --------------------------------------------------------------------------
seccion("AUTENTICACION")

sesion = probar(
    "login administrador",
    200,
    "POST",
    "/api/auth/login",
    {"correo": "admin@autoprime.com.co", "password": "Admin2026!"},
)
tokens["admin"] = sesion["token"]

sesion = probar(
    "login empleado",
    200,
    "POST",
    "/api/auth/login",
    {"correo": "empleado@autoprime.com.co", "password": "Empleado2026!"},
)
tokens["empleado"] = sesion["token"]

sesion = probar(
    "login cliente",
    200,
    "POST",
    "/api/auth/login",
    {"correo": "cliente@autoprime.com.co", "password": "Cliente2026!"},
)
tokens["cliente"] = sesion["token"]

probar(
    "contrasena incorrecta -> 401",
    401,
    "POST",
    "/api/auth/login",
    {"correo": "admin@autoprime.com.co", "password": "incorrecta"},
)
probar(
    "correo inexistente -> 401",
    401,
    "POST",
    "/api/auth/login",
    {"correo": "nadie@autoprime.com.co", "password": "Cualquiera1!"},
)
probar(
    "correo mal formado -> 422",
    422,
    "POST",
    "/api/auth/login",
    {"correo": "no-es-un-correo", "password": "Cualquiera1!"},
)
probar("perfil con token", 200, "GET", "/api/auth/perfil", token=tokens["admin"])
probar("perfil sin token -> 401", 401, "GET", "/api/auth/perfil")
probar(
    "perfil con token invalido -> 401",
    401,
    "GET",
    "/api/auth/perfil",
    token="esto.no.es.un.token",
)

# --------------------------------------------------------------------------
seccion("REGISTRO")

sufijo = date.today().strftime("%H%M%S") + str(abs(hash(str(date.today()))) % 9999)
nuevo = {
    "nombre": "Prueba",
    "apellido": "Automatica",
    "tipo_documento": "CC",
    "numero_documento": f"9{sufijo[:8]}",
    "direccion": "Calle 10 # 20-30",
    "telefono": "3001234567",
    "correo": f"prueba{sufijo[:6]}@autoprime.com.co",
    "password": "Prueba2026!",
    "confirmar_password": "Prueba2026!",
}

sesion_nueva = probar("registro valido", 201, "POST", "/api/auth/registro", nuevo)
# El alta deja la sesion iniciada, asi que devuelve token + usuario.
creado = sesion_nueva["usuario"] if sesion_nueva else None
if creado:
    print(f"        -> id {creado['id']}, rol {creado['rol']}, token emitido")
    assert "password" not in creado, "la respuesta no debe incluir la contrasena"
    assert "passwordHash" not in creado, "la respuesta no debe incluir el hash"
    assert "password_hash" not in creado, "la respuesta no debe incluir el hash"

probar("correo duplicado -> 409", 409, "POST", "/api/auth/registro", nuevo)

probar(
    "contrasena debil -> 422",
    422,
    "POST",
    "/api/auth/registro",
    {**nuevo, "correo": f"otro{sufijo[:6]}@x.com", "password": "corta", "confirmar_password": "corta"},
)
probar(
    "contrasenas que no coinciden -> 422",
    422,
    "POST",
    "/api/auth/registro",
    {
        **nuevo,
        "correo": f"otro2{sufijo[:5]}@x.com",
        "confirmar_password": "Distinta2026!",
    },
)
probar(
    "nombre con numeros -> 422",
    422,
    "POST",
    "/api/auth/registro",
    {**nuevo, "correo": f"otro3{sufijo[:5]}@x.com", "nombre": "Juan123"},
)
probar(
    "telefono con letras -> 422",
    422,
    "POST",
    "/api/auth/registro",
    {**nuevo, "correo": f"otro4{sufijo[:5]}@x.com", "telefono": "300ABC1234"},
)

# --------------------------------------------------------------------------
seccion("PRODUCTOS")

catalogo = probar("listar (publico)", 200, "GET", "/api/productos")
print(f"        -> {catalogo['total']} vehiculos en catalogo")

probar("filtrar por familia", 200, "GET", "/api/productos?familia=edicion")
probar("consultar por id", 200, "GET", "/api/productos/1")
probar("id inexistente -> 404", 404, "GET", "/api/productos/99999")

nuevo_producto = {
    "slug": f"prueba-{sufijo[:6]}",
    "marca": "Prueba",
    "modelo": "Test",
    "familia": "gama",
    "base": "Base de prueba",
    "lema": "Solo una prueba",
    "descripcion": "Vehiculo creado por el script de pruebas.",
    "imagen": "mansory-pugnator-perfil.webp",
    "anio": 2025,
    "kilometraje": 0,
    "precio": 100000000,
    "motor": "V6",
    "potencia": "300 hp",
    "aceleracion": "5,0 s",
    "velocidad": "250 km/h",
    "transmision": "Automatica",
    "traccion": "Trasera",
}

probar("crear sin token -> 401", 401, "POST", "/api/productos", nuevo_producto)
probar(
    "crear como cliente -> 403",
    403,
    "POST",
    "/api/productos",
    nuevo_producto,
    tokens["cliente"],
)
creado_p = probar(
    "crear como admin", 201, "POST", "/api/productos", nuevo_producto, tokens["admin"]
)
producto_id = creado_p["producto"]["id"]

probar("slug duplicado -> 409", 409, "POST", "/api/productos", nuevo_producto, tokens["admin"])
probar(
    "actualizar (PUT)",
    200,
    "PUT",
    f"/api/productos/{producto_id}",
    {"precio": 95000000},
    tokens["admin"],
)
probar(
    "anio fuera de rango -> 422",
    422,
    "PUT",
    f"/api/productos/{producto_id}",
    {"anio": 1800},
    tokens["admin"],
)
probar(
    "empleado NO elimina -> 403",
    403,
    "DELETE",
    f"/api/productos/{producto_id}",
    token=tokens["empleado"],
)
probar(
    "eliminar como admin",
    200,
    "DELETE",
    f"/api/productos/{producto_id}",
    token=tokens["admin"],
)

# --------------------------------------------------------------------------
seccion("SERVICIOS")

servicios = probar("listar (publico)", 200, "GET", "/api/servicios")
print(f"        -> {servicios['total']} servicios")

probar("consultar por id", 200, "GET", "/api/servicios/1")
probar("id inexistente -> 404", 404, "GET", "/api/servicios/99999")

nuevo_servicio = {
    "nombre": "Servicio de prueba",
    "descripcion": "Creado por el script de pruebas.",
    "duracion_min": 60,
    "precio": 50000,
}
probar("crear sin token -> 401", 401, "POST", "/api/servicios", nuevo_servicio)
creado_s = probar(
    "crear como empleado", 201, "POST", "/api/servicios", nuevo_servicio, tokens["empleado"]
)
servicio_id = creado_s["servicio"]["id"]

probar(
    "duracion invalida -> 422",
    422,
    "PUT",
    f"/api/servicios/{servicio_id}",
    {"duracion_min": 5},
    tokens["admin"],
)
probar(
    "eliminar como admin",
    200,
    "DELETE",
    f"/api/servicios/{servicio_id}",
    token=tokens["admin"],
)

# --------------------------------------------------------------------------
seccion("USUARIOS")

probar("listar sin token -> 401", 401, "GET", "/api/usuarios")
probar("listar como cliente -> 403", 403, "GET", "/api/usuarios", token=tokens["cliente"])
probar("listar como empleado -> 403", 403, "GET", "/api/usuarios", token=tokens["empleado"])
lista = probar("listar como admin", 200, "GET", "/api/usuarios", token=tokens["admin"])
print(f"        -> {lista['total']} usuarios")

probar("filtrar por rol", 200, "GET", "/api/usuarios?rol=cliente", token=tokens["admin"])
probar("buscar por texto", 200, "GET", "/api/usuarios?buscar=admin", token=tokens["admin"])

if creado:
    uid = creado["id"]
    probar("consultar uno", 200, "GET", f"/api/usuarios/{uid}", token=tokens["admin"])
    probar(
        "actualizar",
        200,
        "PUT",
        f"/api/usuarios/{uid}",
        {"direccion": "Carrera 50 # 10-20"},
        tokens["admin"],
    )
    probar(
        "inactivar",
        200,
        "PATCH",
        f"/api/usuarios/{uid}/estado",
        {"estado": "inactivo"},
        tokens["admin"],
    )
    probar(
        "el inactivo NO inicia sesion -> 401",
        401,
        "POST",
        "/api/auth/login",
        {"correo": nuevo["correo"], "password": nuevo["password"]},
    )
    probar(
        "reactivar",
        200,
        "PATCH",
        f"/api/usuarios/{uid}/estado",
        {"estado": "activo"},
        tokens["admin"],
    )
    probar("eliminar", 200, "DELETE", f"/api/usuarios/{uid}", token=tokens["admin"])

probar("id inexistente -> 404", 404, "GET", "/api/usuarios/99999", token=tokens["admin"])

# --------------------------------------------------------------------------
seccion("CITAS")

# Se busca un dia laborable proximo: los domingos el taller no atiende.
manana = date.today() + timedelta(days=1)
while manana.weekday() == 6:
    manana += timedelta(days=1)
fecha = manana.isoformat()

probar("disponibilidad (publica)", 200, "GET", f"/api/citas/disponibilidad?fecha={fecha}")
probar("listar sin token -> 401", 401, "GET", "/api/citas")
probar("resumen con token", 200, "GET", "/api/citas/resumen", token=tokens["cliente"])

cuerpo_cita = {"servicio_id": 1, "producto_id": 1, "fecha": fecha, "hora": "10:00", "notas": "Prueba"}

probar("crear sin token -> 401", 401, "POST", "/api/citas", cuerpo_cita)
creada = probar("crear como cliente", 201, "POST", "/api/citas", cuerpo_cita, tokens["cliente"])
cita = creada["cita"]
cita_id = cita["id"]
print(f"        -> cita {cita_id} el {cita['fecha']} a las {cita['hora']}")

probar("misma franja -> 409", 409, "POST", "/api/citas", cuerpo_cita, tokens["cliente"])
probar(
    "fecha pasada -> 422",
    422,
    "POST",
    "/api/citas",
    {**cuerpo_cita, "fecha": "2020-01-01", "hora": "11:00"},
    tokens["cliente"],
)
# Proximo domingo: weekday() 6. Si hoy ya es domingo se toma el siguiente.
dias_al_domingo = (6 - date.today().weekday()) % 7 or 7
domingo = (date.today() + timedelta(days=dias_al_domingo)).isoformat()
probar(
    "domingo -> 422",
    422,
    "POST",
    "/api/citas",
    {**cuerpo_cita, "fecha": domingo, "hora": "11:00"},
    tokens["cliente"],
)
probar(
    "hora fuera de horario -> 422",
    422,
    "POST",
    "/api/citas",
    {**cuerpo_cita, "hora": "23:00", "producto_id": 2},
    tokens["cliente"],
)

probar("cliente ve las suyas", 200, "GET", "/api/citas", token=tokens["cliente"])
probar("admin ve todas", 200, "GET", "/api/citas", token=tokens["admin"])
probar("empleado confirma", 200, "PATCH", f"/api/citas/{cita_id}/estado", {"estado": "confirmada"}, tokens["empleado"])
probar(
    "cliente NO confirma -> 403",
    403,
    "PATCH",
    f"/api/citas/{cita_id}/estado",
    {"estado": "completada"},
    tokens["cliente"],
)
probar(
    "cliente cancela la suya",
    200,
    "PATCH",
    f"/api/citas/{cita_id}/estado",
    {"estado": "cancelada"},
    tokens["cliente"],
)
probar("eliminar (admin)", 200, "DELETE", f"/api/citas/{cita_id}", token=tokens["admin"])

# --------------------------------------------------------------------------
print()
print("=" * 78)
print(f" RESULTADO:  {correctas} pruebas OK, {fallidas} fallidas")
print("=" * 78)

sys.exit(1 if fallidas else 0)
