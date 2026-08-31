import { useEffect, useState } from "react";
import { useIdioma } from "../hooks/useIdioma";

/* Se asoma cuando ya hay bastante recorrido por detrás. */
const UMBRAL = 700;

/**
 * Botón para volver al inicio de la página.
 *
 * Va sobre cristal, en la esquina inferior izquierda, para no chocar con el
 * botón de WhatsApp que ocupa la derecha. El desplazamiento respeta la
 * preferencia de menos movimiento: en ese caso salta sin animación.
 */
function BotonArriba() {
  const [visible, setVisible] = useState(false);
  const { t } = useIdioma();

  useEffect(() => {
    let pendiente = false;

    const alDesplazar = () => {
      if (pendiente) return;
      pendiente = true;

      // Se agrupa la lectura en el siguiente fotograma para no forzar
      // un recálculo de estilo en cada evento de scroll.
      window.requestAnimationFrame(() => {
        setVisible(window.scrollY > UMBRAL);
        pendiente = false;
      });
    };

    alDesplazar();
    window.addEventListener("scroll", alDesplazar, { passive: true });
    return () => window.removeEventListener("scroll", alDesplazar);
  }, []);

  const subir = () => {
    const reducido = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reducido ? "instant" : "smooth" });
  };

  return (
    <button
      type="button"
      onClick={subir}
      aria-label={t("acc.arriba")}
      title={t("acc.arriba")}
      // Cuando está oculto se retira del foco y del árbol de accesibilidad.
      tabIndex={visible ? 0 : -1}
      aria-hidden={!visible}
      className={[
        "cristal pulsable fixed bottom-6 left-5 z-40 flex h-12 w-12 items-center justify-center",
        "text-hueso transition-[opacity,transform] duration-300 sm:left-8",
        visible
          ? "translate-y-0 opacity-100"
          : "pointer-events-none translate-y-3 opacity-0",
      ].join(" ")}
    >
      <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" aria-hidden="true">
        <path
          d="M12 19V5m0 0-6 6m6-6 6 6"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </button>
  );
}

export default BotonArriba;
