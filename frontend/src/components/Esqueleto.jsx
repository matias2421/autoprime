/**
 * Piezas de carga.
 *
 * Reservan exactamente el sitio que va a ocupar el contenido real, de modo
 * que al llegar los datos nada salte (CLS). Van marcadas como `status` para
 * que un lector de pantalla anuncie que se está cargando en lugar de leer
 * una ristra de cajas vacías.
 */

/** Bloque suelto: se le da la forma con clases de Tailwind. */
export function Bloque({ className = "" }) {
  return <span className={`esqueleto block ${className}`} aria-hidden="true" />;
}

/** Silueta de una tarjeta de vehículo: foto 3:2, título y dos líneas. */
export function EsqueletoTarjeta() {
  return (
    <div className="border border-linea" aria-hidden="true">
      <Bloque className="aspect-[3/2] w-full" />
      <div className="space-y-3 p-6">
        <Bloque className="h-3 w-24" />
        <Bloque className="h-6 w-3/5" />
        <Bloque className="h-3 w-full" />
        <Bloque className="h-3 w-4/5" />
      </div>
    </div>
  );
}

/** Rejilla de tarjetas mientras llega el catálogo. */
export function EsqueletoCatalogo({ cantidad = 3, mensaje = "Cargando catálogo" }) {
  return (
    <div role="status" aria-live="polite" className="grid gap-6 lg:grid-cols-3">
      <span className="sr-only">{mensaje}</span>
      {Array.from({ length: cantidad }, (_, i) => (
        <EsqueletoTarjeta key={i} />
      ))}
    </div>
  );
}

/** Filas de una tabla de panel. */
export function EsqueletoFilas({ filas = 5, columnas = 4 }) {
  return (
    <div role="status" aria-live="polite" className="space-y-px">
      <span className="sr-only">Cargando datos</span>
      {Array.from({ length: filas }, (_, f) => (
        <div key={f} className="flex gap-4 bg-carbon p-4" aria-hidden="true">
          {Array.from({ length: columnas }, (_, c) => (
            <Bloque key={c} className={`h-4 ${c === 0 ? "w-1/4" : "flex-1"}`} />
          ))}
        </div>
      ))}
    </div>
  );
}
