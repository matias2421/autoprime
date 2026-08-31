import { useRef } from "react";
import Button from "./ui/Button";
import Icono from "./ui/Icono";
import { useMovimientoReducido, useProgresoScroll } from "../hooks/useScroll";

const CAPITULOS = [
  {
    etiqueta: "01 · Diseño",
    titulo: "Cada panel se talla en fibra de carbono",
    texto:
      "El kit completo sustituye la carrocería original pieza a pieza. Capó ventilado, faldones y un alerón de gran cuerda, todos en fibra vista.",
  },
  {
    etiqueta: "02 · Motor",
    titulo: "Doce cilindros, sin turbos de por medio",
    texto:
      "6.5 litros atmosféricos que giran hasta 8.500 rpm. 770 caballos que responden en el instante en que pisas, no cuando el turbo despierta.",
  },
  {
    etiqueta: "03 · Entrega",
    titulo: "Peritaje de 120 puntos antes de la entrega",
    texto:
      "Revisamos carrocería, mecánica, electrónica y documentos. Te entregamos el informe completo junto con las llaves.",
  },
];

/**
 * Opacidad de un capítulo según el avance del scroll (0 a 1).
 *
 * Los centros se reparten en los extremos (0, 0.5, 1 para tres capítulos) y
 * cada uno se desvanece justo cuando el siguiente aparece. Así el primero ya
 * está visible al entrar en la sección y el último sigue visible al salir:
 * nunca queda un tramo en blanco.
 */
function opacidadCapitulo(progreso, indice, total) {
  if (total < 2) return 1;
  const centro = indice / (total - 1);
  const ancho = 1 / (total - 1);
  return Math.min(1, Math.max(0, 1 - Math.abs(progreso - centro) / ancho));
}

/**
 * Recorrido inmersivo, solo tipográfico.
 *
 * Mientras se hace scroll, la pantalla queda fijada y los capítulos de texto
 * se relevan uno a otro. No hay fotografía: el peso visual lo llevan el
 * titular en serif, el panel de cristal y el resplandor del acento, que se
 * intensifica conforme avanza el recorrido.
 *
 * El fijado se logra con `position: sticky` dentro de un contenedor alto, sin
 * librerías externas.
 */
function SeccionInmersiva() {
  const contenedorRef = useRef(null);
  const progreso = useProgresoScroll(contenedorRef);
  const reducido = useMovimientoReducido();

  /* --- Alternativa sin movimiento: los tres capítulos, uno al lado del otro --- */
  if (reducido) {
    return (
      <section className="border-t border-linea bg-negro px-5 py-20 sm:px-8">
        <div className="mx-auto max-w-[1600px]">
          <ul className="grid gap-6 md:grid-cols-3">
            {CAPITULOS.map((cap) => (
              <li key={cap.etiqueta} className="cristal p-8">
                <p className="etiqueta text-accion">{cap.etiqueta}</p>
                <h3 className="display mt-3 text-2xl text-hueso">{cap.titulo}</h3>
                <p className="mt-3 text-sm leading-relaxed text-ceniza">{cap.texto}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>
    );
  }

  return (
    <section
      ref={contenedorRef}
      className="relative h-[340vh] border-t border-linea bg-negro"
      aria-label="Recorrido por el MANSORY Carbonado EVO"
    >
      <div className="sticky top-0 flex h-screen items-center justify-center overflow-hidden">
        {/* Resplandor del acento, que se intensifica con el avance. */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(58% 46% at 50% 50%, rgb(130 159 176 / 0.22), transparent 72%)",
            opacity: 0.3 + progreso * 0.7,
          }}
        />

        {/* Nombre en marca de agua, con parallax. Es la única capa de fondo. */}
        <p
          aria-hidden="true"
          className="display pointer-events-none absolute inset-x-0 top-[14%] select-none
                     text-center text-[18vw] leading-none text-hueso/6"
          style={{ transform: `translateX(${(0.5 - progreso) * 120}px)` }}
        >
          Carbonado
        </p>

        {/* Capítulos superpuestos, centrados: sin imagen que los desplace. */}
        <div className="relative mx-auto w-full max-w-3xl px-5 sm:px-10">
          <div className="relative h-[22rem] sm:h-72">
            {CAPITULOS.map((cap, indice) => {
              const opacidad = opacidadCapitulo(progreso, indice, CAPITULOS.length);
              return (
                <article
                  key={cap.etiqueta}
                  aria-hidden={opacidad < 0.5}
                  className="cristal absolute inset-x-0 top-0 p-8 text-center sm:p-10"
                  style={{
                    opacity: opacidad,
                    transform: `translateY(${(1 - opacidad) * 24}px)`,
                    pointerEvents: opacidad > 0.5 ? "auto" : "none",
                  }}
                >
                  <p className="etiqueta text-accion">{cap.etiqueta}</p>
                  <h3 className="display mt-3 text-3xl text-hueso sm:text-5xl">
                    {cap.titulo}
                  </h3>
                  <p className="mt-4 text-sm leading-relaxed text-ceniza sm:text-base">
                    {cap.texto}
                  </p>
                  {indice === CAPITULOS.length - 1 && (
                    <div className="mt-7 flex flex-wrap justify-center gap-3">
                      <Button to="/modelos/carbonado-evo">
                        Ver la ficha
                        <Icono nombre="flecha" className="h-4 w-4" />
                      </Button>
                      <Button to="/agendar" variante="contorno">
                        Agendar prueba
                      </Button>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        </div>

        {/* Indicador de avance */}
        <div
          aria-hidden="true"
          className="absolute right-5 top-1/2 hidden -translate-y-1/2 flex-col gap-3 sm:flex"
        >
          {CAPITULOS.map((cap, indice) => {
            const activo =
              opacidadCapitulo(progreso, indice, CAPITULOS.length) > 0.5;
            return (
              <span
                key={cap.etiqueta}
                className={`h-10 w-0.5 transition-colors duration-300 ${
                  activo ? "bg-accion" : "bg-hueso/20"
                }`}
              />
            );
          })}
        </div>
      </div>
    </section>
  );
}

export default SeccionInmersiva;
