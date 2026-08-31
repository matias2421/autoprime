import { IDIOMAS } from "../data/traducciones";
import { useIdioma } from "../hooks/useIdioma";

/**
 * Selector de idioma.
 *
 * Son dos opciones, así que van como un grupo de botones a la vista en lugar
 * de un desplegable: se ve el idioma activo sin tener que abrir nada.
 */
function SelectorIdioma({ className = "" }) {
  const { idioma, setIdioma, t } = useIdioma();

  return (
    <div
      role="group"
      aria-label={t("idioma.elegir")}
      className={`flex items-center border border-trazo ${className}`}
    >
      {IDIOMAS.map(({ valor, etiqueta, nombre }) => {
        const activo = valor === idioma;

        return (
          <button
            key={valor}
            type="button"
            lang={valor}
            onClick={() => setIdioma(valor)}
            aria-pressed={activo}
            title={nombre}
            className={[
              "pulsable flex h-11 min-w-11 cursor-pointer items-center justify-center px-3",
              "font-sans text-xs uppercase tracking-[0.14em]",
              activo
                ? "bg-accion-fondo text-hueso"
                : "text-plomo hover:text-hueso",
            ].join(" ")}
          >
            {etiqueta}
            <span className="sr-only"> — {nombre}</span>
          </button>
        );
      })}
    </div>
  );
}

export default SelectorIdioma;
