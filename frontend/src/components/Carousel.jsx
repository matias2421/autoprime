import { useCallback, useEffect, useState } from "react";
import Button from "./ui/Button";
import Icono from "./ui/Icono";
import { formatearPrecio, vehiculos } from "../data/vehiculos";

const INTERVALO = 6000;
const HEXAGONO = "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)";

/** Botón hexagonal de navegación (contorno fino, relleno al pasar el mouse). */
function BotonHex({ hacia, alPulsar, etiqueta, className }) {
  return (
    <button
      type="button"
      onClick={alPulsar}
      aria-label={etiqueta}
      className={`group absolute top-1/2 z-20 h-16 w-14 -translate-y-1/2 cursor-pointer
                  sm:h-20 sm:w-16 ${className}`}
    >
      <span
        className="absolute inset-0 bg-negro/25 transition-colors duration-200 group-hover:bg-accion-fondo"
        style={{ clipPath: HEXAGONO }}
      />
      <span
        className="absolute inset-[1.5px] bg-pizarra/80 backdrop-blur-md transition-colors
                   duration-200 group-hover:bg-accion-fondo"
        style={{ clipPath: HEXAGONO }}
      />
      <Icono
        nombre={hacia}
        className="relative mx-auto h-5 w-5 text-hueso transition-colors duration-200"
      />
    </button>
  );
}

/**
 * Carrusel del catálogo: 10 vehículos, cada uno con imagen, título y
 * descripción. Los modelos se desplazan hacia la izquierda, avanzan solos, se
 * pausan al pasar el mouse o al enfocar con el teclado, y respetan la
 * preferencia de movimiento reducido del sistema.
 */
function Carousel() {
  const [actual, setActual] = useState(0);
  const [pausado, setPausado] = useState(false);
  const [movimientoReducido, setMovimientoReducido] = useState(false);

  const total = vehiculos.length;

  const ir = useCallback(
    (indice) => setActual(((indice % total) + total) % total),
    [total]
  );
  const siguiente = useCallback(() => ir(actual + 1), [actual, ir]);
  const anterior = useCallback(() => ir(actual - 1), [actual, ir]);

  useEffect(() => {
    const consulta = window.matchMedia("(prefers-reduced-motion: reduce)");
    const actualizar = () => setMovimientoReducido(consulta.matches);
    actualizar();
    consulta.addEventListener("change", actualizar);
    return () => consulta.removeEventListener("change", actualizar);
  }, []);

  useEffect(() => {
    if (pausado || movimientoReducido) return undefined;
    const temporizador = window.setInterval(() => {
      setActual((previo) => (previo + 1) % total);
    }, INTERVALO);
    return () => window.clearInterval(temporizador);
  }, [pausado, movimientoReducido, total]);

  const manejarTeclado = (evento) => {
    if (evento.key === "ArrowRight") {
      evento.preventDefault();
      siguiente();
    } else if (evento.key === "ArrowLeft") {
      evento.preventDefault();
      anterior();
    }
  };

  const vehiculo = vehiculos[actual];

  return (
    <section
      aria-roledescription="carrusel"
      aria-label="Vehículos destacados del catálogo"
      onMouseEnter={() => setPausado(true)}
      onMouseLeave={() => setPausado(false)}
      onFocus={() => setPausado(true)}
      onBlur={() => setPausado(false)}
      onKeyDown={manejarTeclado}
      className="cristal cristal-vivo reflejo alza text-hueso"
    >
      <div className="relative overflow-hidden">
        {/* -------- Pista: todos los modelos se desplazan a la izquierda -------- */}
        <div
          className="flex transition-transform duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]"
          style={{
            width: `${total * 100}%`,
            transform: `translateX(-${(actual * 100) / total}%)`,
          }}
        >
          {vehiculos.map((item, indice) => (
            <article
              key={item.id}
              className="relative shrink-0 px-14 pb-6 pt-10 sm:px-20 sm:pt-14"
              style={{ width: `${100 / total}%` }}
              aria-hidden={indice !== actual}
            >
              {/* Marca y modelo */}
              <p className="etiqueta text-center text-ceniza">{item.marca}</p>
              <h3 className="display mt-2 text-center text-3xl text-hueso sm:text-5xl lg:text-6xl">
                {item.modelo}
              </h3>

              {/* Lema en grande, detrás del vehículo */}
              <p
                aria-hidden="true"
                className="display pointer-events-none absolute inset-x-0 top-[26%] z-0
                           select-none text-center text-3xl text-hueso/8 sm:text-6xl lg:text-7xl"
              >
                {item.lema}
              </p>

              {/* Vehículo de perfil */}
              <img
                src={item.imagen}
                alt={`${item.titulo}: ${item.descripcion}`}
                width={1600}
                height={900}
                loading={indice === 0 ? "eager" : "lazy"}
                decoding="async"
                className="relative z-10 mx-auto mt-4 w-full max-w-4xl object-contain"
              />

              {/* Descripción */}
              <p className="relative z-10 mx-auto mt-5 max-w-2xl text-center text-sm leading-relaxed text-ceniza">
                {item.descripcion}
              </p>
            </article>
          ))}
        </div>

        <BotonHex
          hacia="izquierda"
          alPulsar={anterior}
          etiqueta="Vehículo anterior"
          className="left-3 sm:left-5"
        />
        <BotonHex
          hacia="derecha"
          alPulsar={siguiente}
          etiqueta="Vehículo siguiente"
          className="right-3 sm:right-5"
        />
      </div>

      {/* ------------------- Datos del modelo activo ------------------- */}
      <div
        className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4
                   border-t border-linea px-6 py-6"
        aria-live="polite"
        aria-atomic="true"
      >
        {[
          ["Potencia", vehiculo.specs.potencia],
          ["0–100 km/h", vehiculo.specs.aceleracion],
          ["Desde", formatearPrecio(vehiculo.precio)],
        ].map(([titulo, dato]) => (
          <div key={titulo} className="text-center">
            <p className="etiqueta text-ceniza">{titulo}</p>
            <p className="mt-1 font-sans text-base uppercase tracking-[0.08em] text-hueso">
              {dato}
            </p>
          </div>
        ))}

        <div className="flex gap-3">
          <Button to={`/modelos/${vehiculo.slug}`} tamano="sm" variante="primario">
            Ver el modelo
          </Button>
          <Button
            to={`/agendar?modelo=${vehiculo.slug}&servicio=prueba`}
            tamano="sm"
            variante="claro"
            className="border border-hueso/30 bg-transparent text-hueso hover:bg-hueso/10"
          >
            Agendar prueba
          </Button>
        </div>
      </div>

      {/* --------------- Pestañas con los nombres (10) --------------- */}
      <div className="border-t border-linea">
        <ul className="flex overflow-x-auto">
          {vehiculos.map((item, indice) => (
            <li key={item.id} className="shrink-0">
              <button
                type="button"
                onClick={() => ir(indice)}
                aria-current={indice === actual}
                className={[
                  "relative flex min-h-14 cursor-pointer items-center whitespace-nowrap px-6",
                  "font-sans text-xs uppercase tracking-[0.14em] transition-colors duration-200",
                  indice === actual
                    ? "text-hueso after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-accion"
                    : "text-plomo hover:text-hueso",
                ].join(" ")}
              >
                {item.titulo}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export default Carousel;
