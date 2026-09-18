/**
 * Formato de cifras y fechas, en un solo sitio.
 *
 * Estaba repetido en cada pantalla, y repetido quiere decir distinto: una
 * tabla mostraba «$3200000000» y la de al lado «3.200.000.000 COP». Un panel
 * en el que el mismo importe se escribe de dos maneras obliga a leer dos
 * veces para comprobar que es el mismo número.
 */

/**
 * Pesos colombianos.
 *
 * Sin decimales a propósito: en Colombia los centavos no circulan, y un
 * catálogo donde todo acaba en «,00» gasta cuatro caracteres por fila en no
 * decir nada. La base sí los guarda, porque una suma tiene que cuadrar; lo
 * que se recorta es la presentación.
 */
export const pesos = (valor) =>
  new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(valor) || 0);

/** Un importe grande, abreviado, para cuando el ancho manda. */
export const pesosCortos = (valor) => {
  const n = Number(valor) || 0;
  if (Math.abs(n) >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(1)} mil M`;
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(0)} M`;
  if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(0)} mil`;
  return pesos(n);
};

export const numero = (valor) =>
  new Intl.NumberFormat("es-CO").format(Number(valor) || 0);

/**
 * Una fecha ISO (`2026-09-17`) a texto legible.
 *
 * Se parte a mano en vez de `new Date(iso)` porque esa forma interpreta la
 * cadena como UTC y, en Colombia, devuelve el día anterior: una venta del 17
 * aparecería fechada el 16 en toda la tabla.
 */
export const fechaCorta = (iso) => {
  if (!iso) return "—";
  const [a, m, d] = iso.slice(0, 10).split("-").map(Number);
  return new Date(a, m - 1, d).toLocaleDateString("es-CO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
};

/** Igual, pero con día de la semana. Para cabeceras y detalles. */
export const fechaLarga = (iso) => {
  if (!iso) return "—";
  const [a, m, d] = iso.slice(0, 10).split("-").map(Number);
  return new Date(a, m - 1, d).toLocaleDateString("es-CO", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
};

/** Marca de tiempo completa (`2026-09-17T22:54:00`). */
export const fechaHora = (iso) => {
  if (!iso) return "—";
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return "—";
  return fecha.toLocaleString("es-CO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

/** Solo el día y el mes, para los ejes de las gráficas. */
export const diaMes = (iso) => {
  if (!iso) return "";
  const [, m, d] = iso.slice(0, 10).split("-").map(Number);
  return `${String(d).padStart(2, "0")}/${String(m).padStart(2, "0")}`;
};

/** El día de hoy en formato ISO, según el reloj del navegador. */
export const hoyIso = () => {
  const ahora = new Date();
  const desfase = ahora.getTimezoneOffset() * 60_000;
  return new Date(ahora.getTime() - desfase).toISOString().slice(0, 10);
};

/** Hace `dias` días, en ISO. Para los rangos por defecto de los reportes. */
export const haceDias = (dias) => {
  const fecha = new Date();
  fecha.setDate(fecha.getDate() - dias);
  const desfase = fecha.getTimezoneOffset() * 60_000;
  return new Date(fecha.getTime() - desfase).toISOString().slice(0, 10);
};
