import { useEffect } from "react";

/**
 * Lleva la posición del puntero a la pieza `.reflejo` que hay debajo.
 *
 * Un único escuchador para toda la página, en lugar de uno por tarjeta: en el
 * catálogo hay más de veinte piezas con esta clase y registrar un evento en
 * cada una sería desperdiciarlo. Las coordenadas se escriben como porcentaje
 * en `--mx` y `--my`, que es lo que consume el degradado del CSS.
 *
 * Solo actúa con puntero fino: en táctil no hay "pasar por encima" y el
 * reflejo no llegaría a verse.
 */
export function useReflejoPuntero() {
  useEffect(() => {
    if (!window.matchMedia?.("(pointer: fine)").matches) return undefined;

    let ultima = null;
    let pendiente = false;
    let evento = null;

    const pintar = () => {
      pendiente = false;
      if (!evento) return;

      const pieza = evento.target?.closest?.(".reflejo");

      // Al salir de una pieza se le devuelven sus valores por defecto.
      if (pieza !== ultima && ultima) {
        ultima.style.removeProperty("--mx");
        ultima.style.removeProperty("--my");
      }

      ultima = pieza ?? null;
      if (!pieza) return;

      const caja = pieza.getBoundingClientRect();
      pieza.style.setProperty("--mx", `${((evento.clientX - caja.left) / caja.width) * 100}%`);
      pieza.style.setProperty("--my", `${((evento.clientY - caja.top) / caja.height) * 100}%`);
    };

    const alMover = (e) => {
      evento = e;
      // Se agrupa en el fotograma siguiente: el puntero dispara muchos más
      // eventos de los que la pantalla llega a mostrar.
      if (pendiente) return;
      pendiente = true;
      window.requestAnimationFrame(pintar);
    };

    document.addEventListener("pointermove", alMover, { passive: true });
    return () => document.removeEventListener("pointermove", alMover);
  }, []);
}
