/**
 * Traduce el nombre de archivo que guarda la base a la imagen compilada.
 *
 * La base guarda `"mansory-pugnator-perfil.webp"`, un nombre a secas, porque
 * es lo razonable en una columna de MySQL. Pero Vite, al compilar, mueve las
 * fotos a `/assets/` y les añade un hash del contenido, así que ese nombre no
 * sirve como dirección: hay que traducirlo.
 *
 * Los datos locales de `vehiculos.js` no tienen este problema porque importan
 * cada foto, y entonces `imagen` ya es la URL buena. Por eso esta función
 * acepta las dos formas: los componentes no necesitan saber de dónde vino el
 * vehículo, si de la API o del archivo.
 *
 * `import.meta.glob` con `eager` construye la tabla **en tiempo de
 * compilación**. Eso importa: las fotos entran en el paquete como cualquier
 * otro import, y si una falta se nota al compilar y no más tarde, en el
 * navegador de quien visita, con un 404.
 */
const MODULOS = import.meta.glob("../assets/images/*.{webp,jpg,jpeg,png,avif}", {
  eager: true,
  import: "default",
});

const POR_NOMBRE = Object.fromEntries(
  Object.entries(MODULOS).map(([ruta, url]) => [ruta.split("/").pop(), url]),
);

/** Devuelve la URL utilizable, o `null` si no hay foto que valga. */
export function imagenDeVehiculo(imagen) {
  if (!imagen) return null;

  // Ya resuelta: viene de un import, de una URL externa o de un dato incrustado.
  if (/^(https?:|data:|blob:|\/)/.test(imagen)) return imagen;

  return POR_NOMBRE[imagen] ?? null;
}

/** Los nombres que sí tienen foto. Útil para comprobarlo en una prueba. */
export const NOMBRES_DISPONIBLES = Object.keys(POR_NOMBRE);
