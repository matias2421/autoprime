# Desplegar AutoPrime

Tres piezas en tres sitios, todos con plan gratuito:

```
Vercel                 Render                  Aiven
frontend (React)  -->   backend (FastAPI)  -->  MySQL
```

La base va en Aiven y no en Render porque **la base gratuita de Render caduca
a los 30 días** y luego se borra. La de Aiven no expira. Y al ser MySQL de
verdad, el proyecto se despliega **sin cambiar una línea de código**: solo
cambian variables de entorno.

---

## Lo que ya está preparado

No hace falta tocar el código. Estos cambios ya están hechos y probados:

| Qué | Dónde |
|---|---|
| Acepta la cadena de conexión entera del proveedor | `app/core/configuracion.py` |
| Traduce `mysql://…?ssl-mode=REQUIRED` a lo que entiende el driver | ídem |
| Cifrado TLS con la base remota | `app/core/base_datos.py` |
| Orígenes de CORS configurables por variable | `app/main.py` |
| Prepara una base vacía desde cero | `backend/preparar_base.py` |
| Configuración del servicio de Render | `render.yaml` |
| Rutas de React en Vercel | `frontend/vercel.json` |

Sobre `frontend/vercel.json`, que no admite comentarios por ser JSON: la regla
de reescritura manda todo a `index.html` porque el enrutado lo lleva React en
el navegador. Sin ella, entrar directo a `/modelos` o recargar en
`/panel/admin` daría 404, porque Vercel buscaría un archivo con ese nombre. Los
archivos que sí existen se sirven antes de llegar a esa regla.

---

## 1. La base de datos, en Aiven

Se empieza por aquí a propósito: es la pieza de la que dependen las otras dos,
y si algo falla —la cadena de conexión, el TLS— falla aquí. Mejor descubrirlo
en el portátil que en un servidor.

1. Crea la cuenta en [aiven.io](https://aiven.io) (no pide tarjeta).
2. **Create service → MySQL → plan Free**. Tarda un par de minutos en quedar
   en *Running*.
3. Copia el **Service URI**. Tiene esta forma:
   `mysql://avnadmin:CLAVE@mysql-xxx.aivencloud.com:12345/defaultdb?ssl-mode=REQUIRED`
4. *(Opcional pero recomendable)* descarga el **CA Certificate** que ofrece esa
   misma pantalla y guárdalo como `backend/ca.pem`.

Ahora, en tu equipo, en `backend/.env`:

```
DATABASE_URL=mysql://avnadmin:CLAVE@mysql-xxx.aivencloud.com:12345/defaultdb?ssl-mode=REQUIRED
DB_SSL_CA=ca.pem
```

`DB_SSL_CA` es opcional. Sin él la conexión se cifra igual, pero sin comprobar
contra quién se habla.

Carga el esquema y los datos:

```bash
cd backend
venv\Scripts\python preparar_base.py
```

Debe listar las siete tablas con sus filas y las tres cuentas de prueba. Si
dice que ya hay tablas, repite con `--reiniciar`.

**Comprueba que la API funciona contra la base remota antes de seguir:**

```bash
venv\Scripts\python -m uvicorn app.main:app --port 8000
```

y en otra consola:

```bash
venv\Scripts\python pruebas_api.py
```

Si salen las 81 en verde, lo difícil está hecho.

---

## 2. El backend, en Render

1. Crea la cuenta en [render.com](https://render.com) entrando con GitHub.
2. **New → Blueprint**, elige el repositorio `autoprime`. Detecta el
   `render.yaml` y propone el servicio ya configurado.
3. Te pedirá las variables que el archivo deja en blanco. Rellena por ahora:

   | Variable | Valor |
   |---|---|
   | `DATABASE_URL` | la misma URI de Aiven |
   | `ORIGENES_PERMITIDOS` | déjalo vacío de momento |
   | `URL_FRONTEND` | déjalo vacío de momento |
   | `SMTP_*` | lo de tu Gmail, si quieres el correo de recuperación |

   `SECRET_KEY` la genera Render sola. Es mejor que traer la de local: esa ha
   pasado por tu portátil, por el historial de la consola y por las copias del
   `.env`.

4. Cuando termine, abre `https://<tu-servicio>.onrender.com/salud`. Debe
   responder `"base_datos": "conectada"`.

No subas `ca.pem` al repositorio. Sin él, la conexión sigue cifrada.

---

## 3. El frontend, en Vercel

1. **Add New → Project**, elige el mismo repositorio.
2. **Root Directory: `frontend`**. Este es el paso que más se olvida: sin él
   Vercel busca el `package.json` en la raíz y no lo encuentra.
3. Añade la variable:

   ```
   VITE_API_URL = https://<tu-servicio>.onrender.com/api
   ```

   El `/api` del final es obligatorio: el cliente concatena las rutas a partir
   de ahí.

4. Deploy.

---

## 4. Cerrar el círculo

Este paso es el que hace que funcione, y es fácil saltárselo porque las dos
primeras piezas ya parecen listas.

Vuelve a Render, al servicio, **Environment**, y ahora sí:

```
ORIGENES_PERMITIDOS = https://<tu-proyecto>.vercel.app
URL_FRONTEND        = https://<tu-proyecto>.vercel.app
```

Guarda: Render reinicia solo.

Sin la primera, el navegador bloquea todas las peticiones del frontend y la web
parece rota aunque la API esté perfecta. Sin la segunda, el enlace del correo
de recuperación apunta a `localhost` y no lleva a ninguna parte.

---

## Lo que se duerme

En el plan gratuito de Render el servicio **se apaga a los 15 minutos** sin
visitas y tarda entre 30 y 60 segundos en despertar. Aiven también apaga la
base tras una inactividad larga, pero avisa antes por correo.

Para sustentar: abre la web un par de minutos antes y llegará caliente. Si el
instructor la abre en frío, verá la primera carga lenta y luego todo normal.

---

## Si algo falla

| Síntoma | Causa casi segura |
|---|---|
| La web carga pero ningún dato aparece | Falta `ORIGENES_PERMITIDOS` con la URL de Vercel. Mira la consola del navegador: dirá *blocked by CORS policy* |
| `404` al recargar en `/modelos` | No se está aplicando `frontend/vercel.json`; comprueba que el Root Directory sea `frontend` |
| `/salud` responde 500 | La cadena de `DATABASE_URL` está mal, o la base de Aiven está apagada |
| `Access denied` al preparar la base | Usuario o contraseña mal copiados de la URI |
| El primer acceso tarda un minuto | Es el plan gratuito despertando. No es un fallo |
| El correo de recuperación no llega | `backend/probar_correo.py` lo diagnostica |

---

## Y por si acaso

La última fila de la lista de chequeo pide **«Url del Drive o Git Hub»**. El
repositorio ya cumple ese requisito: desplegar suma, pero no es obligatorio
para la entrega.
