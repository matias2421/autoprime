# AutoPrime — Atelier automotriz

**Cuarto Avance · React + Vite + FastAPI**
Aprendiz: Jose Matías Agudelo Bolívar · Ficha 3406211 · Ambiente 702 · ADSO — SENA
Instructor: Jhan Hader Muñoz

Aplicación web de un atelier automotriz con **React 19 + Vite 8** en el
frontend y **FastAPI + SQLAlchemy** sobre **MySQL** en el backend.

```
React + Vite  →  FastAPI  →  SQLAlchemy  →  MySQL
   :5173          :8000                      :3306
```

En el cuarto avance el backend pasó de **Express a FastAPI** conservando el
dominio, la base de datos y el contrato de la API, de modo que **el frontend
no cambió ni un componente**. El backend anterior queda en `backend-express/`
como evidencia del tercer avance.

---

## Aviso de uso académico

Este repositorio es un **trabajo escolar** del programa ADSO del SENA. No es un
producto comercial, no está en explotación y no se distribuye como tal.

AutoPrime es un concesionario **ficticio**. Los datos de contacto, la dirección,
las noticias, los testimonios y los precios son inventados para el ejercicio.

El material de terceros que contiene se usa **solo con fines educativos**, sin
ánimo de lucro y sin relación alguna con sus titulares:

| Material | Origen | Titular |
|---|---|---|
| 58 fotografías del catálogo | Galerías oficiales de cada vehículo | **MANSORY Design & Holding GmbH** |
| 3 vídeos de la portada | TikTok | **@hasneditz**, **@infinity_motors_2.0**, **@espx.x** |
| Fotografías de detalle y ambiente | [Pexels](https://www.pexels.com) | Licencia libre |
| Modelos 3D y código | Trabajo propio del autor | — |

Las marcas MANSORY, Ferrari, Bugatti, Rolls-Royce, Porsche, Bentley,
Lamborghini, Mercedes-AMG y Tesla pertenecen a sus respectivos propietarios y
aparecen únicamente a título descriptivo. Las marcas de agua de MANSORY se
conservan intactas en todas las fotografías, precisamente para no ocultar su
procedencia.

**Si eres titular de alguno de estos materiales y quieres que se retire, abre
una incidencia en el repositorio y se elimina.**

---

## Cómo ejecutar

Hacen falta tres cosas encendidas: MySQL, el backend y el frontend.

**1. Base de datos** — arranca MySQL desde el panel de XAMPP. Solo la primera vez:

```bash
"C:/xampp/mysql/bin/mysql.exe" -u root < backend/sql/autoprime.sql
node backend-express/sql/seed-usuarios.js
```

**2. Backend (FastAPI)**

```bash
cd backend
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Documentación interactiva en **http://localhost:8000/docs**.

**3. Frontend**

```bash
cd frontend
npm install
npm run dev
```

La web queda en **http://localhost:5173**.

### Cuentas de prueba

| Correo | Contraseña | Rol |
|---|---|---|
| `admin@autoprime.com.co` | `Admin2026!` | administrador |
| `empleado@autoprime.com.co` | `Empleado2026!` | empleado |
| `cliente@autoprime.com.co` | `Cliente2026!` | cliente |

## Cumplimiento de los requerimientos

| # | Requerimiento | Dónde está implementado |
|---|---------------|--------------------------|
| 1 | Integración de Tailwind CSS con Vite | `frontend/vite.config.js` (plugin `@tailwindcss/vite`), `frontend/src/index.css` (`@import "tailwindcss"` + tokens `@theme`) |
| 2 | Carrusel de 10 imágenes con título y descripción | `src/components/Carousel.jsx` + `src/data/vehiculos.js` |
| 3 | Módulo de inicio de sesión | `src/components/auth/Login.jsx`, página `src/pages/IniciarSesion.jsx` |
| 4 | Componente `RecoverPassword` independiente | `src/components/auth/RecoverPassword.jsx` |
| 5 | Formulario de registro (9 campos) | `src/components/auth/RegisterModal.jsx` |
| 6 | Registro dentro de un Modal | `src/components/ui/Modal.jsx` |
| 7 | Validaciones en tiempo real | `src/utils/validaciones.js` + `src/hooks/useFormulario.js` |
| 8 | Componentes reutilizables | `src/components/ui/` (Button, Input, Select, Checkbox, Modal, Icono) |
| 9 | Uso de Hooks | `useState`, `useEffect`, `useCallback`, `useMemo`, `useRef`, `useId`, `useParams`, `useSearchParams` + hook propio `useFormulario` |
| 10 | Integración con la estructura existente | Se conservan Index, ¿Quiénes Somos?, Contacto, Header, Footer, Carousel y `src/assets/images` |

---

## Rutas

| Ruta | Página | Descripción |
|------|--------|-------------|
| `/` | `Index` | Portada con hero, carrusel y secciones editoriales |
| `/modelos` | `Modelos` | **Catálogo con filtros por familia** |
| `/modelos/:slug` | `ModeloDetalle` | Ficha técnica completa de cada modelo |
| `/quienes-somos` | `QuienesSomos` | Historia, misión, visión y trayectoria |
| `/contacto` | `Contacto` | Formulario validado + datos de contacto |
| `/login` | `IniciarSesion` | Inicio de sesión, recuperación y registro |
| `*` | `NoEncontrado` | Error 404 |

Los filtros del catálogo se sincronizan con la URL (`/modelos?familia=edicion`),
así que se pueden compartir y funcionan con los botones atrás/adelante.

---

## Flujo de la aplicación

```
Página principal (/)
        ↓  "Mi cuenta"
Inicio de sesión (/login)
        ↓  "Crear una cuenta"
Registro de cliente (Modal)
        ↓  validación en tiempo real de los 9 campos
Confirmación del registro
        ↓  "Ir a iniciar sesión"  (deja el correo prellenado)
Sesión iniciada
```

Desde el login también se accede a **¿Olvidaste tu contraseña?**, que muestra el
componente `RecoverPassword` sin salir de la página.

---

## Validaciones implementadas

Todas se ejecutan **mientras el usuario escribe**, no solo al enviar.

| Validación | Detalle |
|------------|---------|
| Campos obligatorios | Los 9 campos del registro + aceptación de términos |
| Longitud mínima y máxima | Nombre 2–40, dirección 5–80, contraseña 8–32, etc. |
| Limitación de caracteres | `maxLength` en cada campo, con contador visible donde aplica |
| Restricción de caracteres | Sanitizadores que impiden escribir caracteres no permitidos (letras en teléfono, símbolos en nombre…) |
| Tipos de datos | El documento admite letras solo si el tipo es Pasaporte; los demás solo dígitos |
| Expresiones regulares | `REGEX` en `src/utils/validaciones.js` |
| Formato de correo | Regex + bloqueo de espacios |
| Número de documento | 6–11 dígitos (CC/TI/CE), 9–10 (NIT), 6–15 alfanumérico (Pasaporte) |
| Número telefónico | Exactamente 10 dígitos, debe iniciar en 3 (celular Colombia) |
| Contraseña | Mayúscula + minúscula + número + carácter especial, con medidor de seguridad |
| Confirmación de contraseña | Debe coincidir con la contraseña |

Los errores aparecen junto al campo con `role="alert"` y `aria-invalid`, para
que los anuncie un lector de pantalla.

---

## Diseño

Sistema generado con la skill `ui-ux-pro-max` y documentado en
[`design-system/autoprime-concesionario/MASTER.md`](design-system/autoprime-concesionario/MASTER.md),
donde queda registrado por qué se descartó el estilo que sugirió la búsqueda
inicial y qué se tomó como referencia.

- **Lenguaje:** atelier automotriz — fondo `#020204`, fotografía a sangre
  completa, **esquinas rectas en todo** y secciones que alternan negro, humo y
  azul a lo largo de la página.
- **Tipografía:** Cormorant Garamond peso 300 para los titulares grandes
  (a partir de 2rem) + Inter para toda la interfaz.
- **Acento:** azul acero `#829fb0`. Como texto sobre negro rinde 7.4:1; como
  relleno **exige texto `#020204`**, porque en blanco caería a 2.8:1.
- **Portada de una sola pantalla:** no se desplaza. Solo el vídeo de fondo, el
  titular y dos accesos. Es la única página con el scroll bloqueado; todas las
  demás se desplazan con normalidad. Todo lo que antes colgaba debajo —catálogo, cifras,
  actualidad, recorrido inmersivo, testimonios— vive ahora en *Quiénes somos*.
- **Vídeo de fondo encadenado:** tres clips que se relevan con fundido cruzado
  y vuelven a empezar (51 s de bucle). El siguiente se precarga para que el
  relevo no tenga espera; con `prefers-reduced-motion` no se carga ninguno y
  queda una fotografía fija.
- **Cortina de entrada:** el nombre entra con el tracking abierto y lo va
  cerrando mientras dos marcas de líneas salen de detrás de él hacia los lados.
  Aparece en **cada carga y recarga** de la página, se salta con un clic o
  cualquier tecla y no se monta si el sistema pide menos movimiento.
- **Todo oscuro:** no hay ninguna superficie clara en el sitio. La jerarquía
  entre secciones se construye con cuatro tonos de negro muy próximos, bordes
  de 1 px y paneles de cristal, nunca invirtiendo a blanco.
- **Modelos 3D:** el Pugnator Tricolore y el SF90 Soft Kit tienen un apartado
  "En 3D" con visor orbital. Ni la librería ni el modelo se descargan hasta
  que se pulsa el botón. Es un campo del catálogo (`modelo3d`), no un caso
  especial: cualquier otro vehículo lo mostraría con solo añadirle el suyo.
- **Cursor de lente:** en escritorio, el puntero del sistema se sustituye por
  una bola de cristal que se rezaga y distorsiona el fondo por el que pasa, más
  un punto que sí va exacto para no perder precisión. Crece sobre lo pulsable y
  se contrae al presionar. En Chromium la distorsión es refracción real, con un
  mapa de desplazamiento SVG; en el resto, desenfoque. No aparece en táctil ni
  con `prefers-reduced-motion`.
- **Liquid glass:** cabecera, menú, diálogos, campos de formulario, tarjetas de
  modelo, celdas de la ficha técnica, testimonios, paneles de rol y botones
  flotantes van sobre superficie translúcida con desenfoque. Detrás de cada
  sección que hospeda cristal hay un resplandor de ambiente muy tenue: sin él
  el desenfoque no tendría nada que refractar y se vería como un gris liso.
- **Español e inglés:** el selector cambia navegación, botones, títulos de
  sección y mensajes, y actualiza el atributo `lang` del documento. Las fichas
  de cada vehículo son datos del catálogo y se mantienen en español.

### Interacción y rendimiento

- Microinteracciones en botones y enlaces: hundido al presionar, barrido de luz
  al pasar el puntero y subrayado que crece desde la izquierda.
- Transición de entrada entre páginas, reiniciada con la ruta.
- Botón de volver arriba, que aparece pasados 700 px de recorrido.
- Esqueletos de carga que reservan el hueco exacto del contenido (`Esqueleto.jsx`).
- Sección de testimonios y enlaces a redes en el pie.
- Imágenes con `width`/`height` declarados, `loading="lazy"` fuera del primer
  pliegue y `decoding="async"`; el catálogo se sirve en WebP a 1600 px.
- Favicon propio y `theme-color` fijado al negro base.

**Verificaciones hechas antes de entregar** (medidas en el navegador):

- Contraste: texto secundario 10.2:1, terciario 6.4:1, blanco sobre el azul
  de relleno 6.6:1. Medido compositando el canal alfa y con las transiciones
  congeladas: 0 fallos en portada, catálogo y ficha de modelo.
- Objetivos táctiles ≥ 44×44 px
- Sin scroll horizontal en las 8 rutas a 375 px
- Foco visible; el Modal atrapa el foco y se cierra con `Escape`
- Iconos SVG propios, ningún emoji como icono
- `prefers-reduced-motion` respetado (detiene el carrusel y las animaciones)
- Imágenes en WebP con `alt`, `width`/`height` y `loading="lazy"`

---

## Tercer avance: backend, base de datos y roles

El proyecto pasó de ser solo frontend a una aplicación **full stack**.

### Cómo ejecutarlo completo

1. Enciende **MySQL** desde el panel de XAMPP.
2. Crea la base de datos:

```bash
"C:\xampp\mysql\bin\mysql.exe" -u root < backend/sql/autoprime.sql
```

3. Backend (terminal 1):

```bash
cd backend && npm install && npm run seed && npm run dev
```

4. Frontend (terminal 2):

```bash
cd frontend && npm run dev
```

### Usuarios de prueba

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | admin@autoprime.com.co | Admin2026! |
| Empleado | empleado@autoprime.com.co | Empleado2026! |
| Cliente | cliente@autoprime.com.co | Cliente2026! |

### Cumplimiento del tercer entregable

| # | Requerimiento | Dónde está |
|---|---|---|
| 1 | Base de datos SQL relacional | [autoprime.sql](backend/sql/autoprime.sql) — 7 tablas relacionadas |
| 2 | Roles de usuario | Tablas `roles`, `permisos`, `rol_permiso` |
| 3 | Carpeta backend | [backend/src](backend/src) — config, models, controllers, routes, middlewares |
| 4 | Conexión Front ↔ Back ↔ BD | [api/cliente.js](frontend/src/api/cliente.js) → API → MySQL |
| 5 | Registro conectado | [RegisterModal.jsx](frontend/src/components/auth/RegisterModal.jsx) → `POST /api/auth/registro` |
| 6 | Login con JWT | [auth.controller.js](backend/src/controllers/auth.controller.js) |
| 7 | Endpoints de la API | 5 grupos de rutas — ver [backend/README.md](backend/README.md) |
| 8 | Protección con JWT y roles | [auth.middleware.js](backend/src/middlewares/auth.middleware.js) |
| 9 | Operaciones CRUD | Usuarios, productos, servicios y citas |
| 10 | Panel de administrador | [PanelAdmin.jsx](frontend/src/pages/panel/PanelAdmin.jsx) |
| 11 | Panel de empleado | [PanelEmpleado.jsx](frontend/src/pages/panel/PanelEmpleado.jsx) |
| 12 | Panel de cliente | [PanelCliente.jsx](frontend/src/pages/panel/PanelCliente.jsx) |
| 13 | Usuario autenticado en el Navbar | [Header.jsx](frontend/src/components/Header.jsx) |
| 14 | Validaciones en tiempo real | Frontend y **también** backend ([validaciones.js](backend/src/utils/validaciones.js)) |
| 15 | Botón flotante de WhatsApp | [WhatsAppButton.jsx](frontend/src/components/WhatsAppButton.jsx) |
| 16 | Organización del proyecto | `frontend/` y `backend/` separados |
| 17 | Contraseñas hasheadas | bcrypt con 10 rondas, nunca en texto plano |
| 18 | Pruebas de los endpoints | [pruebas-api.sh](backend/sql/pruebas-api.sh) — 51 pruebas |

### Agendamiento de citas

Los botones **Cotizar** y **Agendar prueba** del catálogo llevan a
`/agendar?modelo=<slug>&servicio=<tipo>`, donde el cliente elige fecha y hora.
Las franjas disponibles se consultan al backend, así que nunca se ofrece una
hora ya reservada. La restricción `uq_cupo` de la tabla `citas` lo garantiza
incluso si dos personas envían el formulario al mismo tiempo.

### Rutas nuevas

| Ruta | Acceso |
|---|---|
| `/agendar` | Pública (pide iniciar sesión al confirmar) |
| `/panel/admin` | Solo administrador |
| `/panel/empleado` | Administrador y empleado |
| `/panel/cliente` | Cualquier usuario autenticado |

---

## Modelos 3D

Dos vehículos tienen malla tridimensional, hechas por el autor del trabajo:

| Vehículo | Origen | Web |
|---|---|---|
| Pugnator Tricolore | 126 MB | **1,79 MB** |
| SF90 Soft Kit | 124 MB | **1,43 MB** |

Ambos llegaron igual: OBJ de un millón de triángulos con las texturas PBR
sueltas y sin `.mtl`. El proceso, que está guardado en
`herramientas/convertir-modelo-3d.sh` para los que vengan:

| Paso | Resultado |
|---|---|
| OBJ + MTL escrito a mano → GLB | 126 MB → 37 MB |
| Soldado y simplificado al 12 % | 1.000.000 → ~187.000 triángulos |
| Texturas reducidas a tres, en JPEG | 19 MB → 0,91 MB |
| Compresión Draco | **1,4–1,8 MB** |

Añadir un modelo nuevo es convertirlo, dejarlo en `frontend/public/modelos3d/`
y darle al vehículo su campo en el catálogo:

```js
modelo3d: { archivo: "/modelos3d/sf90.glb", peso: "1,4 MB" }
```

El apartado "En 3D" y su entrada en el submenú aparecen solos; no hay que
tocar ninguna página.

Tres detalles del camino:

1. **El OBJ no traía `.mtl`**, así que las texturas estaban sueltas y nada las
   referenciaba. Hubo que escribir el material y enlazarlas.
2. **`texture_pbr.png` era el mapa ORM combinado** (oclusión en rojo, rugosidad
   en verde, metalicidad en azul: sus medias coincidían exactamente con los
   mapas sueltos de rugosidad y metalicidad). Usarlo hizo redundantes otros dos
   archivos, y el mapa de emisión era negro puro, así que también sobraba.
3. **Draco y no meshopt.** La primera versión salió con meshopt a 4,47 MB, pero
   `model-viewer` no incluye ese decodificador y fallaba al cargar. Draco sí
   viene incorporado y además comprime más: 1,79 MB.

### Tres trampas del componente `model-viewer`

Las tres dieron el mismo síntoma —"el modelo no se ve"— por causas distintas:

1. **`reveal` solo admite `auto` y `manual`.** Con cualquier otro valor el
   póster interno del visor no se retira nunca y tapa la escena con un
   rectángulo opaco. Aquí estaba puesto en `eager`, que no existe: el modelo
   cargaba bien y quedaba oculto detrás.
2. **Un lienzo WebGL dentro de un elemento con `backdrop-filter` no se compone
   en Chromium.** El panel de cristal iba envolviendo al visor; ahora va como
   capa hermana por detrás, con el mismo aspecto.
3. **`inset-0` no basta para estirarlo.** `model-viewer` fija
   `width: 300px; height: 150px` en su `:host`, e `inset: 0` solo estira
   cuando ambas medidas son `auto`. Sin `width`/`height` explícitos al 100 %
   el lienzo se queda en 300×150 pegado a la esquina superior izquierda.

### Por qué el material se corrige en tiempo de ejecución

El modelo salía **negro sobre negro**. La causa estaba en su mapa PBR:

| Dato medido | Valor |
|---|---|
| Difuso, luminancia mediana | 30 / 255 |
| Metalicidad media (canal B del ORM) | 0,53 |
| `metallicFactor` en el material | 1,0 |
| Oclusión (canal R) | 255 constante — canal vacío |

En PBR una superficie metálica **no tiene componente difusa**: su color sale
entero de reflejar el entorno. Con metalicidad efectiva 0,53, una textura
difusa de mediana 30/255 —el coche es negro carbono— y la iluminación de
estudio *neutral*, que es tenue, el resultado era negro.

En un escaneo el aspecto ya viene horneado en la textura difusa, así que
`Visor3D` pone `metallicFactor` a 0 y `roughnessFactor` a 0,65 al terminar la
carga, y sube la exposición a 2. **Si el modelo sigue viéndose oscuro, el
`exposure` del componente es el mando a subir.**

El visor va anclado al contenedor con `absolute inset-0` y no con
`height: 100%`: la altura en porcentaje dependía de que toda la cadena de
padres tuviera altura definida, y basta con que uno no la tenga para que el
lienzo quede a cero.

El visor es `@google/model-viewer`, importado dinámicamente: queda en su propio
trozo de 1 MB que solo se descarga al pulsar "Ver en 3D". El paquete principal
no cambia de tamaño.

## Cuarto avance: el backend en FastAPI

El requisito era **reemplazar la tecnología del backend** manteniendo todo lo
demás. El resultado: 29 endpoints en FastAPI sobre la misma base MySQL, y el
frontend intacto.

| | Tercer avance | Cuarto avance |
|---|---|---|
| Framework | Express 5 | **FastAPI** |
| Lenguaje | JavaScript | **Python 3.14** |
| Acceso a datos | `mysql2` a mano | **SQLAlchemy 2** |
| Validación | Funciones propias | **Pydantic** |
| Contraseñas | bcrypt | **bcrypt** (los mismos hashes) |
| Tokens | `jsonwebtoken` | **python-jose** |
| Documentación | — | **Swagger en `/docs`** |

Tres decisiones explican por qué el frontend no cambió:

1. **La API habla camelCase.** El código Python usa `snake_case`, pero todos
   los esquemas heredan de una base con `alias_generator=to_camel`. Pydantic
   traduce en ambos sentidos, así que `tipoDocumento` sigue funcionando sin
   tocar los 19 sitios donde aparece.
2. **Las respuestas van en los mismos sobres.** El backend anterior devolvía
   `{"usuarios": [...]}` y no una lista suelta; se conservó ese contrato.
3. **Los hashes son compatibles.** bcrypt es el mismo algoritmo y el mismo
   formato `$2b$10$`, de modo que las cuentas creadas por el backend en Node
   siguen iniciando sesión sin volver a registrarse.

Arquitectura, endpoints y el resto de decisiones en
[`backend/README.md`](backend/README.md).

**Pruebas:** `backend/pruebas_api.py` ejercita **65 casos por HTTP**
—autenticación, registro con validaciones, CRUD de las cuatro entidades,
control de roles (401 frente a 403) y las reglas de la agenda—. Además hay
colección de Postman con 40 peticiones en
`backend/sql/AutoPrime.postman_collection.json`.

## Imágenes

Las fotografías de detalle y de ambiente provienen de
**[Pexels](https://www.pexels.com)**, cuya licencia permite el uso gratuito,
comercial y sin atribución obligatoria. Ninguna imagen se repite en todo el
sitio.

**Vehículos del catálogo (10 modelos, 58 fotografías).** Son fotografías de
estudio de preparaciones MANSORY, guardadas por el autor del trabajo desde las
galerías oficiales de cada vehículo y usadas aquí **con fines exclusivamente
académicos**: este proyecto no se distribuye ni se comercializa.

El tratamiento fue deliberadamente mínimo:

1. **Sin recorte alguno.** Las 58 llegaron en 3:2 exacto, así que todos los
   contenedores del sitio usan `aspect-[3/2]` y `object-cover` no recorta nada:
   ningún coche queda cortado por el encuadre.
2. **Reescalado** a 1600 px de ancho como máximo y recompresión WebP a calidad
   88 (8,7 MB → 6,2 MB, un 29 % menos) sin pérdida visible en pantalla.
3. **Verificación de duplicados** por hash MD5: se detectaron y eliminaron dos
   repetidas, una del Carbonado y otra del Monza.

Las marcas de agua de MANSORY se conservan tal cual: borrarlas sería ocultar la
procedencia de la fotografía, y además el vehículo *es* un MANSORY.

**Vídeos de la portada (3 clips, 6 MB).** Los guardó el autor del trabajo desde
TikTok —@hasneditz, @infinity_motors_2.0 y @espx.x— y se usan aquí **con fines
exclusivamente académicos**: este proyecto no se distribuye ni se comercializa.
Están sin recodificar, tal cual se descargaron: 1024×576, entre 14 y 21 s. El
navegador los pide por rangos (`206 Partial Content`), así que la portada no
descarga los 6 MB de golpe.

**Modelos incluidos:** Pugnator Tricolore (Ferrari Purosangue), Phantom VIII
(Rolls-Royce), SF90 Soft Kit (Ferrari SF90 Stradale), Vivere (Bugatti Chiron),
Art Piece AL3C (Mercedes-AMG G 63), Carbonado EVO (Lamborghini Aventador SVJ),
Elongation EVO (Tesla Cybertruck), Monza SP2 (Ferrari), Bentley GT (Continental
GT) y P9LM EVO 900 Cabrio (Porsche 911 Turbo S). Las cifras son las que publica
el preparador; los precios en pesos son estimaciones de mercado, porque MANSORY
no publica tarifas.

---

## Estructura del frontend

```
src/
├── assets/images/        18 fotografías en WebP
├── components/
│   ├── auth/             Login, RegisterModal, RecoverPassword
│   ├── ui/               Button, Input, Select, Checkbox, Modal, Icono
│   ├── Header.jsx  Footer.jsx  Carousel.jsx
├── data/vehiculos.js     Catálogo de 10 modelos con ficha técnica
├── hooks/useFormulario.js
├── pages/                Index, Modelos, ModeloDetalle, QuienesSomos,
│                         Contacto, IniciarSesion, NoEncontrado
├── router/AppRouter.jsx
└── utils/                validaciones.js, clientes.js
```

> **Nota:** `src/utils/clientes.js` guarda los registros en `localStorage` solo
> para poder demostrar el flujo completo en esta entrega. En un sistema real la
> contraseña se envía al servidor y se almacena cifrada, nunca en el navegador.
