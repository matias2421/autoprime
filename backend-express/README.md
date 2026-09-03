# AutoPrime — Backend (Tercer Avance)

API REST en **Node.js + Express** conectada a **MySQL/MariaDB**, con
autenticación **JWT**, contraseñas hasheadas con **bcrypt** y control de roles.

---

## Puesta en marcha

**1. Encender MySQL.** Abre el panel de XAMPP y arranca *MySQL*.

**2. Crear la base de datos:**

```bash
"C:\xampp\mysql\bin\mysql.exe" -u root < backend/sql/autoprime.sql
```

**3. Instalar dependencias y crear los usuarios de prueba:**

```bash
cd backend
npm install
npm run seed
```

**4. Levantar el servidor:**

```bash
npm run dev
```

Queda en <http://localhost:3000>.

---

## Usuarios de prueba

Los crea `npm run seed` con la contraseña ya hasheada.

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@autoprime.com.co` | `Admin2026!` |
| Empleado | `empleado@autoprime.com.co` | `Empleado2026!` |
| Cliente | `cliente@autoprime.com.co` | `Cliente2026!` |

---

## Estructura

```
backend/
├── .env                      Variables de entorno
├── sql/
│   ├── autoprime.sql         Script de creación de la BD (entregable 4)
│   ├── seed-usuarios.js      Usuarios de prueba con hash bcrypt
│   └── pruebas-api.sh        51 pruebas de los endpoints
└── src/
    ├── server.js             Arranque; verifica la BD antes de escuchar
    ├── app.js                Express, CORS, rutas y manejo de errores
    ├── config/db.js          Pool de conexiones mysql2
    ├── models/               Consultas SQL (usuario, producto, servicio, cita)
    ├── controllers/          Lógica de cada endpoint
    ├── routes/               Definición de rutas y permisos
    ├── middlewares/          verificarToken y permitirRoles
    └── utils/validaciones.js Validación del lado servidor
```

---

## Base de datos

Siete tablas relacionadas:

| Tabla | Para qué |
|---|---|
| `roles` | administrador, empleado, cliente |
| `permisos` | Acciones concretas del sistema |
| `rol_permiso` | Qué permisos tiene cada rol |
| `usuarios` | Clientes registrados + personal |
| `productos` | Los 10 vehículos del catálogo |
| `servicios` | Lo que se puede agendar |
| `citas` | Agendamiento (fecha, hora, estado) |

La contraseña se guarda en `password_hash` mediante bcrypt con 10 rondas.
**Nunca** se almacena en texto plano, y por eso los usuarios de prueba se crean
desde `seed-usuarios.js` y no desde el `.sql`.

La restricción `uq_cupo (fecha, hora, producto_id)` impide que dos clientes
reserven la misma franja para el mismo vehículo.

---

## Endpoints

`401` = falta token · `403` = el rol no tiene permiso

### Autenticación — `/api/auth`

| Método | Ruta | Acceso |
|---|---|---|
| POST | `/registro` | Público |
| POST | `/login` | Público |
| GET | `/perfil` | Autenticado |

### Usuarios — `/api/usuarios`

| Método | Ruta | Acceso |
|---|---|---|
| GET | `/` | Admin, empleado |
| GET | `/:id` | Admin, empleado |
| POST | `/` | Admin |
| PUT | `/:id` | Admin |
| PATCH | `/:id/estado` | Admin |
| DELETE | `/:id` | Admin |

### Productos — `/api/productos`

| Método | Ruta | Acceso |
|---|---|---|
| GET | `/` · `/:slug` | Público |
| POST | `/` | Admin, empleado |
| PUT | `/:id` | Admin, empleado |
| DELETE | `/:id` | Admin |

### Servicios — `/api/servicios`

| Método | Ruta | Acceso |
|---|---|---|
| GET | `/` · `/:id` | Público |
| POST | `/` · PUT `/:id` | Admin, empleado |
| DELETE | `/:id` | Admin |

### Citas — `/api/citas`

| Método | Ruta | Acceso |
|---|---|---|
| GET | `/disponibilidad?fecha=&productoId=` | Público |
| GET | `/` | Autenticado (el cliente solo ve las suyas) |
| GET | `/resumen` | Autenticado |
| POST | `/` | Autenticado |
| PATCH | `/:id/estado` | Autenticado (el cliente solo cancela las suyas) |
| DELETE | `/:id` | Admin |

---

## Pruebas de los endpoints

Con el servidor encendido:

```bash
bash backend/sql/pruebas-api.sh
```

Ejecuta **51 pruebas**: registro, login, JWT, CRUD de las cuatro entidades,
respuestas de error (400, 401, 403, 404, 409) y control de roles. Sirve como
evidencia equivalente a la colección de Postman.

Para probar a mano con Postman:

1. `POST /api/auth/login` con el correo y la contraseña.
2. Copia el `token` de la respuesta.
3. En las demás peticiones, pestaña **Authorization → Bearer Token**.
