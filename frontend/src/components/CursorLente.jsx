import { useEffect, useRef, useState } from "react";

/* Interpolación por fotograma: cuanto más bajo, más se rezaga la lente. */
const SEGUIMIENTO = 0.19;

/* Qué se considera "interactivo" y hace crecer la lente. */
const INTERACTIVOS =
  'a[href], button, input, select, textarea, summary, [role="button"], [role="tab"], [tabindex]:not([tabindex="-1"])';

function debeActivarse() {
  if (typeof window === "undefined") return false;

  // Sin puntero fino (táctil) no hay cursor que sustituir.
  if (!window.matchMedia?.("(pointer: fine)").matches) return false;

  // Con menos movimiento se deja el cursor del sistema, que no se rezaga.
  return !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Cursor de lente.
 *
 * Son dos piezas: un punto que sigue al ratón con exactitud —para no perder
 * precisión— y detrás una bola de cristal que se rezaga y distorsiona lo que
 * pasa por debajo.
 *
 * La distorsión se consigue con `backdrop-filter`: desenfoque, saturación y
 * brillo sobre el fondo real de la página. Donde el navegador admite filtros
 * SVG en `backdrop-filter` se añade además un mapa de desplazamiento, que
 * curva de verdad la imagen como haría un vidrio; donde no, queda la versión
 * de solo desenfoque, que es la que se ve en la mayoría de navegadores.
 *
 * No se monta en táctil ni si el visitante pidió menos movimiento: en ambos
 * casos manda el cursor del sistema.
 */
function CursorLente() {
  const [activo] = useState(debeActivarse);
  const [sobreInteractivo, setSobreInteractivo] = useState(false);
  const [presionado, setPresionado] = useState(false);
  const [visible, setVisible] = useState(false);

  const lenteRef = useRef(null);
  const puntoRef = useRef(null);
  const destino = useRef({ x: 0, y: 0 });
  const posicion = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (!activo) return undefined;

    // El cursor del sistema se oculta solo mientras la lente está montada.
    document.documentElement.classList.add("con-lente");

    const alMover = (evento) => {
      destino.current.x = evento.clientX;
      destino.current.y = evento.clientY;

      // Se llama sin comprobar el valor actual a propósito: React descarta el
      // renderizado si el estado no cambia, y así `visible` no tiene que
      // entrar en las dependencias del efecto. Si entrara, el primer
      // movimiento del ratón desmontaría los escuchadores y reiniciaría el
      // bucle de fotogramas.
      setVisible(true);

      // El punto no se interpola: va exactamente donde está el ratón.
      if (puntoRef.current) {
        puntoRef.current.style.transform =
          `translate3d(${evento.clientX}px, ${evento.clientY}px, 0)`;
      }
    };

    const alEntrar = (evento) => {
      if (evento.target?.closest?.(INTERACTIVOS)) setSobreInteractivo(true);
    };

    const alSalir = (evento) => {
      if (evento.target?.closest?.(INTERACTIVOS)) setSobreInteractivo(false);
    };

    const alPulsar = () => setPresionado(true);
    const alSoltar = () => setPresionado(false);
    const alAbandonar = () => setVisible(false);

    document.addEventListener("pointermove", alMover, { passive: true });
    document.addEventListener("pointerover", alEntrar, { passive: true });
    document.addEventListener("pointerout", alSalir, { passive: true });
    document.addEventListener("pointerdown", alPulsar, { passive: true });
    document.addEventListener("pointerup", alSoltar, { passive: true });
    document.addEventListener("pointerleave", alAbandonar, { passive: true });

    /*
     * La lente se mueve en su propio bucle de fotogramas, no en el evento de
     * ratón: así el rezago es suave y constante aunque los eventos lleguen a
     * ráfagas, y solo se toca el DOM una vez por fotograma.
     */
    let fotograma = window.requestAnimationFrame(function paso() {
      posicion.current.x += (destino.current.x - posicion.current.x) * SEGUIMIENTO;
      posicion.current.y += (destino.current.y - posicion.current.y) * SEGUIMIENTO;

      if (lenteRef.current) {
        lenteRef.current.style.transform =
          `translate3d(${posicion.current.x}px, ${posicion.current.y}px, 0)`;
      }

      fotograma = window.requestAnimationFrame(paso);
    });

    return () => {
      document.documentElement.classList.remove("con-lente");
      document.removeEventListener("pointermove", alMover);
      document.removeEventListener("pointerover", alEntrar);
      document.removeEventListener("pointerout", alSalir);
      document.removeEventListener("pointerdown", alPulsar);
      document.removeEventListener("pointerup", alSoltar);
      document.removeEventListener("pointerleave", alAbandonar);
      window.cancelAnimationFrame(fotograma);
    };
  }, [activo]);

  if (!activo) return null;

  const estado = [
    "lente",
    sobreInteractivo ? "lente-activa" : "",
    presionado ? "lente-pulsada" : "",
    visible ? "" : "lente-oculta",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <>
      {/*
        Mapa de desplazamiento. La turbulencia hace de imperfección del vidrio:
        curva ligeramente lo que se ve a través de la lente en lugar de solo
        desenfocarlo.
      */}
      <svg className="lente-filtro" aria-hidden="true" focusable="false">
        <filter id="lente-refraccion" colorInterpolationFilters="sRGB">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.014"
            numOctaves="2"
            seed="7"
            result="ruido"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="ruido"
            scale="14"
            xChannelSelector="R"
            yChannelSelector="G"
          />
        </filter>
      </svg>

      {/*
        Dos capas: el ancla la mueve el JS y la lente de dentro cambia de
        tamaño con `scale`. Separarlas evita que el JS pise la escala al
        escribir la traslación en el mismo `transform`.
      */}
      <div ref={lenteRef} className="lente-ancla" aria-hidden="true">
        <div className={estado} />
      </div>
      <div
        ref={puntoRef}
        className={`lente-punto ${visible ? "" : "lente-oculta"}`}
        aria-hidden="true"
      />
    </>
  );
}

export default CursorLente;
