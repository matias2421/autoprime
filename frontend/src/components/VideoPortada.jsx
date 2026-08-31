import { useCallback, useEffect, useRef, useState } from "react";
import respaldo from "../assets/images/mansory-vivere-perfil.webp";

/* Los tres clips se encadenan y vuelven a empezar: 51 s de bucle. */
const CLIPS = [
  { src: "/video/portada-1.mp4", segundos: 20.9 },
  { src: "/video/portada-2.mp4", segundos: 14.5 },
  { src: "/video/portada-3.mp4", segundos: 16.0 },
];

function movimientoReducido() {
  if (typeof window === "undefined") return false;
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
}

/**
 * Fondo de vídeo de la portada.
 *
 * Los tres clips se montan a la vez, superpuestos, y solo uno está visible.
 * Cuando termina, cede el turno al siguiente con un fundido cruzado; al
 * acabar el tercero se vuelve al primero. Montarlos todos evita el parpadeo
 * negro que deja cambiar el `src` de un único elemento.
 *
 * Si el visitante pidió menos movimiento no se carga ningún vídeo: en su
 * lugar queda una fotografía fija.
 */
function VideoPortada() {
  const [reducido] = useState(movimientoReducido);
  const [actual, setActual] = useState(0);
  const refs = useRef([]);

  const siguiente = useCallback(() => {
    setActual((i) => (i + 1) % CLIPS.length);
  }, []);

  /**
   * Arranca el clip activo.
   *
   * Se llama desde dos sitios: al cambiar de turno y cuando el vídeo avisa de
   * que ya tiene datos. Hace falta lo segundo porque en el primer montaje el
   * elemento todavía puede estar vacío, y una llamada a `play()` sobre un
   * vídeo sin datos se queda sin efecto.
   */
  const arrancar = useCallback(
    (i) => {
      if (reducido || i !== actual) return;

      const video = refs.current[i];
      if (!video || !video.paused) return;

      const promesa = video.play();

      // El navegador puede rechazar la reproducción automática (ahorro de
      // batería, ajustes del usuario). No es un fallo: el fondo se queda
      // simplemente en el primer fotograma.
      if (promesa) promesa.catch(() => {});
    },
    [actual, reducido]
  );

  useEffect(() => {
    if (reducido) return;

    const video = refs.current[actual];
    if (!video) return;

    video.currentTime = 0;
    arrancar(actual);
  }, [actual, reducido, arrancar]);

  if (reducido) {
    return (
      <img
        src={respaldo}
        alt=""
        aria-hidden="true"
        width={1600}
        height={1067}
        className="absolute inset-0 h-full w-full object-cover"
      />
    );
  }

  return (
    <div className="absolute inset-0 overflow-hidden" aria-hidden="true">
      {CLIPS.map(({ src }, i) => (
        <video
          key={src}
          ref={(nodo) => {
            refs.current[i] = nodo;
          }}
          src={src}
          muted
          playsInline
          // `autoPlay` en el clip de turno: deja que el propio navegador lo
          // arranque en cuanto pueda, sin depender de nuestro efecto.
          autoPlay={i === actual}
          // El siguiente se precarga para que el relevo no tenga espera.
          preload={i === actual || i === (actual + 1) % CLIPS.length ? "auto" : "none"}
          onCanPlay={() => arrancar(i)}
          onEnded={siguiente}
          // Si un clip falla, se salta en lugar de dejar el fondo congelado.
          onError={siguiente}
          className={`absolute inset-0 h-full w-full object-cover transition-opacity
                      duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] ${
                        i === actual ? "opacity-100" : "opacity-0"
                      }`}
        />
      ))}
    </div>
  );
}

export default VideoPortada;
