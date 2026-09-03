# Backend de AutoPrime — FastAPI

**Cuarto Avance · React + Vite + FastAPI**
Aprendiz: Jose Matías Agudelo Bolívar · Ficha 3406211 · Ambiente 702 · ADSO — SENA
Instructor: Jhan Hader Muñoz

API REST del atelier AutoPrime construida con **FastAPI**, **SQLAlchemy 2** y
**MySQL/MariaDB**. Sustituye al backend en Express del tercer avance
conservando el mismo dominio, la misma base de datos y **el mismo contrato**,
de modo que el frontend en React no tuvo que cambiar ni un componente.

```
React + Vite  →  FastAPI  →  SQLAlchemy  →  MySQL
   :5173          :8000                      :3306
```

---

## Puesta en marcha

Con XAMPP arrancado (MySQL en el 3306) y la base cargada:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

La documentación interactiva queda en **http://localhost:8000/docs**, con el
botón *Authorize* para pegar el token y probar los endpoints protegidos.

Si la base aún no existe:

```bash
"C:\xampp\mysql\bin\mysql.exe" -u root < sql/autoprime.sql
```

Los tres usuarios de prueba se crean con el script del avance anterior
(`backend-express/sql/seed-usuarios.js`), y **sus contraseñas siguen sirviendo**:
bcrypt es el mismo algoritmo y el mismo formato, así que nadie tuvo que
registrarse de nuevo al cambiar de Node a Python.

| Correo | Contraseña | Rol |
|---|---|---|
| `admin@autoprime.com.co` | `Admin2026!` | administrador |
| `empleado@autoprime.com.co` | `Empleado2026!` | empleado |
| `cliente@autoprime.com.co` | `Cliente2026!` | cliente |

---

## Estructura

```
backend/
├── app/
│   ├── core/
│   │   ├── configuracion.py   Ajustes leídos del entorno (pydantic-settings)
│   │   ├── base_datos.py      Motor, sesión y dependencia de conexión
│   │   └── seguridad.py       bcrypt y firma/validación de los JWT
│   ├── models/autoprime.py    Mapeo SQLAlchemy de las 7 tablas
│   ├── schemas/               Validación de entrada y forma de salida
│   ├── crud/                  Acceso a datos, sin saber nada de HTTP
│   ├── routers/               Un router por recurso
│   ├── dependencias.py        Sesión, identidad y permisos inyectables
│   ├── errores.py             Excepciones de dominio
│   └── main.py                App, CORS y manejadores de error
├── sql/autoprime.sql          Esquema y datos iniciales
├── pruebas_api.py             65 pruebas de extremo a extremo
├── requirements.txt
└── .env.example
```

**`models` y `schemas` no son lo mismo y por eso están separados.** Un modelo
describe una fila de la base; un esquema describe lo que entra o sale por la
API. Un usuario tiene `password_hash` en el modelo, y ese campo no aparece en
ningún esquema de salida: así es imposible filtrarlo por descuido.

---

## Endpoints

Base: `http://localhost:8000` · Todo bajo `/api` · Ninguna ruta lleva barra final.

### Autenticación

| Método | Ruta | Acceso |
|---|---|---|
| POST | `/api/auth/registro` | público — alta de cliente, devuelve sesión iniciada |
| POST | `/api/auth/login` | público — devuelve el JWT |
| GET | `/api/auth/perfil` | token — revalida la sesión |

### Usuarios · solo administrador

| Método | Ruta |
|---|---|
| GET | `/api/usuarios` — filtros `?rol` `?estado` `?buscar` |
| POST | `/api/usuarios` |
| GET · PUT · DELETE | `/api/usuarios/{id}` |
| PATCH | `/api/usuarios/{id}/estado` |

### Productos · lectura pública, escritura con rol

| Método | Ruta | Acceso |
|---|---|---|
| GET | `/api/productos` — filtros `?familia` `?estado` | público |
| GET | `/api/productos/{id o slug}` | público |
| POST · PUT | `/api/productos` · `/api/productos/{id}` | administrador o empleado |
| DELETE | `/api/productos/{id}` | administrador |

### Servicios · igual que productos

`GET` público · `POST`/`PUT` de personal · `DELETE` de administrador.

### Citas

| Método | Ruta | Acceso |
|---|---|---|
| GET | `/api/citas/disponibilidad?fecha=&productoId=` | público |
| GET | `/api/citas` · `/api/citas/resumen` | token — un cliente ve solo las suyas |
| POST | `/api/citas` | token |
| GET · PUT | `/api/citas/{id}` | token, y que sea suya |
| PATCH | `/api/citas/{id}/estado` | el cliente solo puede **cancelar** |
| DELETE | `/api/citas/{id}` | administrador o empleado |

---

## Decisiones que conviene conocer

### La API habla camelCase, el código Python snake_case

El frontend envía `tipoDocumento` y `numeroDocumento` desde el primer avance.
En vez de tocar los 19 sitios donde aparecen, todos los esquemas heredan de
`Esquema`, que lleva `alias_generator=to_camel`. Pydantic traduce en ambos
sentidos y, con `populate_by_name`, una petición escrita en `snake_case`
desde Postman también funciona.

### Las respuestas van en sobres

El backend anterior devolvía `{"usuarios": [...]}` en lugar de una lista
suelta, y el frontend lo lee así. Se conservó ese contrato: es lo que permite
afirmar que **solo cambió la tecnología del backend**, no la aplicación.

### Un único formato de error

Todo error sale igual, venga de una excepción de dominio, de Pydantic o de la
base de datos:

```json
{
  "codigo": "correo_ya_registrado",
  "mensaje": "Ya existe una cuenta con el correo ana@ejemplo.com.",
  "ruta": "/api/auth/registro",
  "detalles": null
}
```

`codigo` es estable y sirve para decidir en el frontend; `mensaje` está
redactado para mostrarse y puede cambiar. En los errores de validación,
`detalles` trae `[{campo, problema}]`, que el cliente aplana para marcar cada
input.

### 401 y 403 no son lo mismo

`401` es "no sé quién eres" y lleva al login. `403` es "sé quién eres, pero no
puedes" y muestra un aviso. Se tratan por separado en toda la API.

### El token se revalida contra la base en cada petición

Que un JWT tenga firma válida no significa que la cuenta siga vigente. La
dependencia `usuario_actual` relee el usuario, de modo que inactivar a alguien
surte efecto de inmediato y no cuando caduque el token que ya tiene abierto.

### bcrypt en vez de passlib

El PDF sugiere `passlib/bcrypt`, pero passlib ya no recibe mantenimiento y
falla con bcrypt 4.x al leer su atributo `__about__`. Se usa la biblioteca
`bcrypt` directamente: mismo algoritmo, mismo formato `$2b$10$`, y por eso los
usuarios creados por el backend en Node siguen pudiendo iniciar sesión.

---

## Pruebas

```bash
# Con la API levantada en otra terminal
venv\Scripts\python pruebas_api.py
```

**65 pruebas** de extremo a extremo por HTTP, igual que las hará Postman:
autenticación, registro con sus validaciones, CRUD de las cuatro entidades,
control de roles (401 frente a 403) y las reglas de la agenda —franja
ocupada, fecha pasada, domingo, hora fuera de horario—.

También hay colección de Postman en `sql/AutoPrime.postman_collection.json`.
