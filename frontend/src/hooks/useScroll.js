import { useEffect, useRef, useState } from "react";

/** ¿El sistema pide menos movimiento? */
export function useMovimientoReducido() {
  const [reducido, setReducido] = useState(false);

  useEffect(() => {
    const consulta = window.matchMedia("(prefers-reduced-motion: reduce)");
    const actualizar = () => setReducido(consulta.matches);
    actualizar();
    consulta.addEventListener("change", actualizar);
    return () => consulta.removeEventListener("change", actualizar);
  }, []);

  return reducido;
}

/**
 * Progreso (0 a 1) del recorrido de un elemento alto a través de la pantalla.
 * Sirve para animar una sección fijada con `position: sticky`.
 *
 * El cálculo se hace dentro de requestAnimationFrame para no bloquear el hilo
 * principal en cada evento de scroll.
 */
export function useProgresoScroll(ref) {
  const [progreso, setProgreso] = useState(0);
  const cuadroRef = useRef(0);

  useEffect(() => {
    const elemento = ref.current;
    if (!elemento) return undefined;

    const calcular = () => {
      cuadroRef.current = 0;
      const caja = elemento.getBoundingClientRect();
      const recorrido = caja.height - window.innerHeight;

      if (recorrido <= 0) {
        setProgreso(0);
        return;
      }
      setProgreso(Math.min(1, Math.max(0, -caja.top / recorrido)));
    };

    const alDesplazar = () => {
      if (!cuadroRef.current) {
        cuadroRef.current = window.requestAnimationFrame(calcular);
      }
    };

    calcular();
    window.addEventListener("scroll", alDesplazar, { passive: true });
    window.addEventListener("resize", alDesplazar);

    return () => {
      window.cancelAnimationFrame(cuadroRef.current);
      window.removeEventListener("scroll", alDesplazar);
      window.removeEventListener("resize", alDesplazar);
    };
  }, [ref]);

  return progreso;
}

/**
 * Devuelve [ref, enVista]. `enVista` pasa a true la primera vez que el
 * elemento entra en pantalla, para animaciones de aparición que no se repiten.
 */
export function useEnVista(margen = "0px 0px -12% 0px") {
  const ref = useRef(null);

  // Estado inicial perezoso: sin IntersectionObserver el contenido nace
  // visible, así nunca queda oculto en navegadores que no lo soportan.
  const [enVista, setEnVista] = useState(
    () => typeof IntersectionObserver === "undefined"
  );

  useEffect(() => {
    const elemento = ref.current;
    if (!elemento || typeof IntersectionObserver === "undefined") {
      return undefined;
    }

    const observador = new IntersectionObserver(
      ([entrada]) => {
        if (entrada.isIntersecting) {
          setEnVista(true);
          observador.disconnect();
        }
      },
      { rootMargin: margen, threshold: 0.05 }
    );

    observador.observe(elemento);
    return () => observador.disconnect();
  }, [margen]);

  return [ref, enVista];
}
