import Icono from "../ui/Icono";

/*
 * Va fuera de `Paginador` a proposito. Definido dentro, React ve un tipo de
 * componente distinto en cada render: desmonta el boton anterior y monta uno
 * nuevo, perdiendo el foco del teclado justo despues de pulsarlo, que es
 * cuando mas falta hace conservarlo.
 */
function Boton({ hacia, etiqueta, icono, deshabilitado, onCambiar }) {
  return (
    <button
      type="button"
      onClick={() => onCambiar(hacia)}
      disabled={deshabilitado}
      aria-label={etiqueta}
      className="inline-flex h-11 w-11 items-center justify-center border border-trazo
                 text-hueso transition-colors hover:border-hueso hover:bg-hueso/10
                 focus-visible:outline-2 focus-visible:outline-offset-2
                 focus-visible:outline-accion-claro
                 disabled:cursor-not-allowed disabled:border-linea disabled:text-trazo
                 disabled:hover:bg-transparent motion-reduce:transition-none"
    >
      <Icono nombre={icono} className="h-4 w-4" />
    </button>
  );
}


/**
 * Paginador de los listados.
 *
 * Dice en qué página se está y cuántas hay, no solo «anterior / siguiente».
 * Sin ese contexto no se sabe si faltan dos filas o dos mil, y la decisión de
 * si vale la pena seguir pasando páginas es imposible de tomar.
 *
 * Los botones miden 44 px, que es el mínimo táctil del proyecto, y se
 * desactivan en los extremos en vez de desaparecer: un control que cambia de
 * sitio al llegar al final obliga a volver a buscarlo.
 */
function Paginador({ pagina, onCambiar }) {
  if (!pagina || pagina.paginas <= 1) return null;

  const { pagina: actual, paginas, total, porPagina } = pagina;
  const desde = (actual - 1) * porPagina + 1;
  const hasta = Math.min(actual * porPagina, total);

  return (
    <div className="flex flex-wrap items-center justify-between gap-4">
      <p className="font-sans text-xs uppercase tracking-[0.12em] text-plomo">
        {desde}–{hasta} de {total}
        <span className="mx-2 text-trazo">·</span>
        página {actual} de {paginas}
      </p>

      <div className="flex items-center gap-2">
        <Boton
          hacia={actual - 1}
          etiqueta="Página anterior"
          icono="izquierda"
          deshabilitado={actual <= 1}
          onCambiar={onCambiar}
        />
        <Boton
          hacia={actual + 1}
          etiqueta="Página siguiente"
          icono="derecha"
          deshabilitado={actual >= paginas}
          onCambiar={onCambiar}
        />
      </div>
    </div>
  );
}

export default Paginador;
