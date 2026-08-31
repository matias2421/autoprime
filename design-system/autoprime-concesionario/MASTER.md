# Design System Master File

> **LÓGICA:** Al construir una página, primero revisa `design-system/pages/[nombre].md`.
> Si ese archivo existe, sus reglas **anulan** este Master.
> Si no, sigue estrictamente las reglas de abajo.

---

**Proyecto:** AutoPrime
**Categoría:** Automotriz / Concesionario de altas prestaciones
**Generado con:** skill `ui-ux-pro-max`
**Última revisión:** 13 de agosto de 2026

---

## Dirección de diseño

Lenguaje **editorial automotriz**: fondo casi negro, fotografía a sangre
completa, tipografía de display en mayúsculas con **peso regular** (no bold),
**esquinas rectas en todo (radius 0)** y un único acento sólido.

### Historial de decisiones

**1. Estilo inicial descartado.** La primera búsqueda devolvió
*3D & Hyperrealism*, marcado en la propia base de datos como
`Performance: ❌ Poor` y `Accessibility: ⚠ Not accessible`, y requiere
WebGL/Three.js. Choca con las prioridades 1 (Accesibilidad, CRITICAL) y 3
(Performance, HIGH) de la skill y con el stack del proyecto.

**2. Referencia adoptada.** A petición del aprendiz se estudió el sitio de
Lamborghini para extraer su **lenguaje de diseño** (no sus activos ni su
marca). Medido directamente sobre el sitio:

| Señal observada | Valor | Aplicado en AutoPrime |
|---|---|---|
| `border-radius` de botones | `0px` | `* { border-radius: 0 }` global |
| Peso de los titulares | `400` | clase `.display` |
| Transformación de titulares | `uppercase` | clase `.display` |
| Alto de botón principal | `72px` | `min-h-16` (64px) / `min-h-14` |
| Relleno de botón | `24px` | `px-10` |
| Filtros activo / inactivo | blanco / `#969696` | `text-hueso` / `text-plomo` |
| Estructura de catálogo | pestañas + fichas a sangre completa | `/modelos` |

**Lo que NO se copió:** el amarillo corporativo `#FFC000`, la tipografía
propietaria *LamboType*, el nombre, el logotipo y las fotografías. AutoPrime
conserva su acento rojo `#DC2626` del sistema original.

---

## Reglas globales

### Paleta

**Toda la página es oscura: no existe ninguna superficie clara.** La jerarquía
entre secciones se construye con cuatro tonos de negro muy próximos, bordes de
1 px y paneles de cristal, nunca invirtiendo a blanco.

| Rol | Hex | Variable | Contraste sobre `#020204` |
|---|---|---|---|
| Fondo base | `#020204` | `--color-negro` | — |
| Secciones alternas | `#07070b` | `--color-carbon` | — |
| Tarjetas y campos | `#0d0d13` | `--color-grafito` | — |
| Superficie elevada | `#13131b` | `--color-pizarra` | — |
| Separadores | `#22222b` | `--color-linea` | — |
| Bordes de control | `#3c3c47` | `--color-trazo` | — |
| Texto principal | `#ffffff` | `--color-hueso` | 20.6:1 |
| Texto secundario | `#b6b6b6` | `--color-ceniza` | 10.2:1 |
| Texto terciario | `#8f8f93` | `--color-plomo` | 6.4:1 |
| Acento (texto) | `#829fb0` | `--color-accion` | 7.4:1 |
| Acento (relleno) | `#3d6274` | `--color-accion-fondo` | 3.2:1 con blanco encima a 6.6:1 |

> **El azul tiene dos tonos y no son intercambiables.** `#829fb0` sirve para
> texto, bordes y subrayados sobre negro (7.4:1). Como relleno de superficie es
> demasiado luminoso —marca 0.33 de luminancia y rompe una página que quiere
> ser toda oscura—, así que los botones y las marcas usan `#3d6274`, que se
> queda en 0.11, separa del fondo y admite texto blanco con 6.6:1.

### Tipografía

Dos familias con papeles separados: **serif ligera para los titulares grandes,
sans de palo seco para toda la interfaz.**

- **Display:** Cormorant Garamond — peso 300, caja alta y baja, `line-height: 1.02`
- **Texto e interfaz:** Inter — 16px base, `line-height: 1.6`
- **Etiquetas:** Inter 11px, peso 500, `letter-spacing: 0.14em`, mayúsculas

```css
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500&family=Inter:wght@300;400;500;600&display=swap');
```

> La serif **solo se usa a partir de 2rem**. Por debajo de ese cuerpo pierde
> legibilidad: los botones, la navegación y los rótulos van siempre en Inter.

### Clases utilitarias definidas

| Clase | Uso |
|---|---|
| `.display` | Titulares grandes: serif peso 300, caja alta y baja |
| `.display-alta` | Igual, en mayúsculas: nombre de marca y rótulos grandes |
| `.etiqueta` | Kickers, categorías, fechas: 11px con tracking 0.14em |
| `.velo` | Degradado sobre las fotos que garantiza legibilidad del texto |
| `.lineas-kv` | Haz de diagonales de la identidad, en mezcla `lighten` |

### Portada

Ocupa exactamente una pantalla (`100svh`, no `100vh`: en móvil la barra del
navegador se contrae al desplazar y `100vh` deja la sección más alta que la
ventana) y bloquea el desplazamiento mientras está montada. El pie no se
renderiza en esa ruta: sería inalcanzable y reintroduciría el scroll.

De fondo van tres clips encadenados. Se montan los tres a la vez, superpuestos,
y solo uno es visible; al terminar cede el turno al siguiente con un fundido
cruzado de 1 s. Montarlos todos evita el parpadeo negro que deja cambiar el
`src` de un único elemento, y el siguiente se precarga para que el relevo no
tenga espera.

### Bloqueo del desplazamiento

Solo la portada bloquea el scroll; el resto del sitio se desplaza con
normalidad. Cuatro cosas pueden pedir el bloqueo —la cortina de entrada, la
portada, el menú a pantalla completa y los diálogos—, y pueden solaparse.

Todas pasan por `useBloqueoScroll(motivo)`, que mantiene un **conjunto de
motivos**: el bloqueo está puesto mientras quede alguno y se levanta cuando no
queda ninguno.

> El patrón habitual de "guardo el valor anterior y lo restauro al salir"
> **está mal aquí** y llegó a producirse: la cortina bloqueaba guardando `""`,
> la portada llegaba después y guardaba `"hidden"` —el de la cortina—, la
> cortina se retiraba devolviendo `""` y, al salir de la portada, esta
> restauraba `"hidden"`. El desplazamiento quedaba bloqueado en todo el sitio.
> Con un conjunto de motivos no hay valor que restaurar.

### Cortina de entrada

El nombre entra con el tracking muy abierto y lo va cerrando hasta su medida
de reposo, mientras las dos marcas de líneas salen de detrás de él hacia los
lados. Se salta con un clic o cualquier tecla, se muestra **una sola vez por
pestaña** (`sessionStorage`) y no llega a montarse si el visitante pidió menos
movimiento.

| Pieza | Retardo | Duración |
|---|---|---|
| Nombre (tracking + desenfoque) | 160 ms | 1000 ms |
| Marcas de líneas (hacia fuera) | 620 ms | 820 ms |
| Haz de diagonales | 900 ms | 900 ms |
| Barra del acento | 1400 ms | 620 ms |
| Rótulo inferior | 1580 ms | 620 ms |
| Retirada | 2100 ms | 620 ms |

El nombre va en **versalitas** (`font-variant-caps: small-caps`), que dejan la
«A» y la «P» a caja alta y el resto en capitales pequeñas. Las marcas son la
misma pieza (`MarcaLineas`) usada dos veces; la de la derecha se refleja
**dentro** del SVG, no en su elemento raíz, para dejar libre el `transform`
que necesita la animación.

### Capas de CSS

Las clases propias —cristal, resplandores, microinteracciones, esqueletos—
viven dentro de **`@layer components`**, y eso no es cosmético.

Sin capa ganarían a las utilidades de Tailwind, que están en
`@layer utilities`: el `position: relative` de `.cristal` anulaba el `fixed`
de un botón flotante y el `absolute` de un panel superpuesto, y ambos volvían
al flujo normal rompiendo la maqueta. Dentro de la capa de componentes,
cualquier utilidad escrita en el marcado manda sobre ellas, que es el orden
correcto: la clase pone el aspecto, la utilidad decide la posición.

### Liquid glass

| Clase | Uso |
|---|---|
| `.cristal` | Panel estándar: tarjetas, diálogos, cabecera al desplazar |
| `.cristal-sutil` | Extensiones grandes que apenas deben despegarse del fondo |
| `.cristal-denso` | Encima de fotografía a todo color |
| `.cristal-vivo` | Añade teñido de acento en el borde al pasar el puntero o al enfocar |

Las tres variantes llevan realce especular en el borde superior, una línea
oscura en el inferior y sombra de contacto. Sin soporte de `backdrop-filter`
pasan a opacas mediante `@supports not`: la diferencia es entre un cristal y un
panel liso, nunca entre legible e ilegible.

### Resplandores de ambiente

El cristal sobre negro plano no refracta nada: se ve como un gris liso. Lo que
le da vida es que haya algo detrás. `.resplandor` coloca al fondo de una sección
dos manchas radiales muy tenues del azul de acento (16 % y 11 %) para que los
paneles tengan qué difuminar; `.resplandor-centro` es la variante de una sola
mancha centrada.

**Sin resplandor detrás, el cristal no se aprecia.** Es la pieza que hace que
el sistema funcione, no un adorno opcional.

### Cursor de lente

Sustituye al puntero del sistema en escritorio. Son **dos piezas**: un punto de
5 px que va exactamente donde está el ratón —para no perder precisión— y detrás
una bola de cristal que se rezaga interpolando un 19 % por fotograma.

La distorsión sale de `backdrop-filter` sobre el fondo real de la página:
desenfoque, saturación y brillo. Donde el navegador admite **filtros SVG en
`backdrop-filter`** (hoy, Chromium) se antepone un `feDisplacementMap` con
turbulencia, que curva de verdad la imagen como haría un vidrio; el resto se
queda con la versión de solo desenfoque, que ya se lee como cristal.

| Estado | Escala | Diámetro |
|---|---|---|
| Reposo | 0.44 | 30 px |
| Sobre algo pulsable | 1 | 68 px |
| Presionado | 0.32 | 22 px |

> **El tamaño se cambia con `scale`, nunca con `width`.** La caja mide siempre
> 68 px; animar el ancho obligaría a recalcular la maqueta en cada fotograma de
> algo que persigue al puntero a 60 fps. Por eso hay dos capas: el ancla, que
> traslada el JS, y la lente de dentro, que escala el CSS. Si compartieran
> elemento, la traslación pisaría la escala.

Va en `z-index: 110`, por encima de la cortina de entrada: con el cursor del
sistema oculto, quedar por debajo de algo dejaría al visitante sin puntero
visible justo cuando la cortina se puede saltar con un clic.

No se monta con puntero grueso (táctil) ni si el visitante pidió menos
movimiento: en ambos casos manda el cursor del sistema.

### Microinteracciones

| Clase | Efecto |
|---|---|
| `.pulsable` | El elemento cede al presionarlo (`translateY(1px) scale(0.985)`) |
| `.barrido` | Una banda de luz cruza la pieza al pasar el puntero o al enfocarla |
| `.subrayado` | Subrayado que crece desde la izquierda |
| `.esqueleto` | Bloque de carga con barrido continuo |
| `.pagina-entra` | Entrada de página; se reinicia con la `key` de la ruta |
| `.reflejo` | Halo del acento que sigue al puntero por dentro de la pieza |
| `.alza` | La pieza se levanta 6 px y gana sombra al apuntarla |
| `.avanza` | La flecha de un enlace se desplaza a la derecha |
| `.abre-letras` | El rótulo separa sus letras al apuntarlo |

Las coordenadas de `.reflejo` las escribe `useReflejoPuntero` en `--mx` y
`--my`. Es **un solo escuchador para toda la página**, agrupado por fotograma:
en el catálogo hay más de veinte piezas con esa clase y poner un evento en
cada una sería desperdiciarlo.

Todas quedan neutralizadas por la regla global de `prefers-reduced-motion`.

### Fotografía### Fotografía

Las 58 fotografías del catálogo son **3:2 exacto**. Todo contenedor de imagen
usa `aspect-[3/2]`, de modo que `object-cover` no recorta absolutamente nada.

### Componentes

```
Botón primario   → bg-accion, texto blanco, radius 0, min-h 56–64px, px 40px
Botón contorno   → borde hueso/35, hover borde sólido + bg hueso/10
Botón texto      → sin caja, subrayado en hover
Campo de texto   → bg-carbon, borde linea, radius 0, min-h 56px
Modal            → bg-carbon, borde linea, fondo negro/85 + backdrop-blur
Ficha de modelo  → imagen a sangre 80–88vh + velo + texto abajo a la izquierda
```

---

## Patrón de página

**Catálogo (`/modelos`)** — la pantalla más importante:

1. Cabecera oscura con miga de pan (`Inicio / Modelos`) y titular a dos tonos
2. **Pestañas de filtro** (Todos · Gama · Edición limitada · Colección),
   sincronizadas con la URL mediante `?familia=` para permitir deep linking
3. Contador de resultados
4. Fichas **sobre fondo claro alterno** (`#ffffff` / `#f2f2f2`), cada una con:
   marca, modelo en grande, **lema como marca de agua detrás del vehículo**,
   el carro **recortado de perfil**, descripción, 4 datos técnicos y 3 CTA
5. Cierre con CTA

### Presentación del vehículo

Regla central del catálogo: **el vehículo va recortado, de perfil y flotando**
sobre fondo claro, con sombra de piso elíptica. Nunca a sangre completa con su
fondo original. El lema va detrás en `text-negro/8` y `aria-hidden` (es
decorativo, no informativo).

El carrusel repite la misma puesta en escena y añade:
- **Desplazamiento hacia la izquierda**: pista `flex` de ancho `N × 100%` con
  `translateX(-(i × 100 / N)%)` — acelerado por GPU, sin animar propiedades de
  layout.
- **Flechas hexagonales** (`clip-path: polygon(50% 0%, 100% 25%, 100% 75%,
  50% 100%, 0% 75%, 0% 25%)`), con un hexágono exterior de contorno y otro
  interior de relleno, porque `clip-path` no dibuja bordes.
- **Pestañas inferiores** con el nombre de cada modelo.

**Home (`/`)** — hero a pantalla completa → cifras → carrusel de 10 modelos →
gama en cuadrícula → editorial de competición → showroom + proceso → noticias → CTA.

---

## Antipatrones (NO usar)

- ❌ Esquinas redondeadas de cualquier radio
- ❌ La serif por debajo de 2rem (ahí manda Inter)
- ❌ Recortar una fotografía del catálogo: son 3:2 y caben enteras
- ❌ Titulares en negrita (el peso correcto es 300)
- ❌ Emojis como iconos → SVG propios en `components/ui/Icono.jsx`
- ❌ Texto blanco sobre el azul de acento (2.8:1) → usar `--color-negro`
- ❌ Sombras difusas: la profundidad viene de la imagen y los bordes de 1px
- ❌ Cambios de estado instantáneos (usar 150–300 ms)
- ❌ Foco invisible

---

## Checklist previo a la entrega

- [x] Contraste ≥ 4.5:1 en todo el texto (medido en navegador)
- [x] Objetivos táctiles ≥ 44×44 px
- [x] Sin scroll horizontal en 375 / 768 / 1024 / 1280 px
- [x] Foco visible; el Modal atrapa el foco y cierra con `Escape`
- [x] Iconos SVG, ningún emoji
- [x] `prefers-reduced-motion` respetado
- [x] Imágenes en WebP, con `alt`, `width`/`height` y `loading="lazy"`
- [x] Deep linking en los filtros del catálogo
