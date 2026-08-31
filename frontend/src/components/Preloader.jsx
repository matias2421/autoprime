import { useCallback, useEffect, useState } from "react";
import LineasKv from "./LineasKv";
import { useBloqueoScroll } from "../hooks/useBloqueoScroll";
import MarcaLineas from "./MarcaLineas";

/**
 * Decide si la cortina de entrada debe llegar a mostrarse.
 *
 * Se muestra en CADA carga y recarga de la página. Lo único que la salta es
 * que el visitante haya pedido menos movimiento en su sistema.
 *
 * No se muestra al navegar de una página a otra: el componente vive fuera del
 * router y no se vuelve a montar, así que la cortina solo aparece cuando el
 * documento se carga de nuevo.
 */
function debeMostrarse() {
  if (typeof window === "undefined") return false;

  return !window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Cortina de entrada de AutoPrime.
 *
 * El nombre aparece con el tracking cerrado y lo va soltando, mientras las dos
 * marcas de líneas salen de detrás de él hacia los lados. Al fondo entra el haz
 * diagonal de la identidad y, al terminar, la cortina sube.
 *
 * Se puede saltar con un clic o con cualquier tecla.
 */
function Preloader() {
  const [fase, setFase] = useState(() => (debeMostrarse() ? "entrando" : "fuera"));

  // El fondo no debe poder desplazarse mientras la cortina está echada.
  useBloqueoScroll("cortina", fase !== "fuera");

  const saltar = useCallback(() => {
    setFase((actual) => (actual === "entrando" ? "saliendo" : actual));
  }, []);

  useEffect(() => {
    if (fase === "fuera") return undefined;

    const alTeclado = () => saltar();
    document.addEventListener("keydown", alTeclado);

    const aSalir = window.setTimeout(() => setFase("saliendo"), 2100);
    const aFuera = window.setTimeout(() => setFase("fuera"), 2720);

    return () => {
      document.removeEventListener("keydown", alTeclado);
      window.clearTimeout(aSalir);
      window.clearTimeout(aFuera);
    };
    // `fase` solo entra aquí para que la limpieza corra al retirar la cortina.
  }, [fase, saltar]);

  if (fase === "fuera") return null;

  return (
    <div
      className={`pre-velo ${fase === "saliendo" ? "pre-saliendo" : ""}`}
      onClick={saltar}
      role="presentation"
    >
      <LineasKv className="pre-lineas absolute inset-y-0 left-0 h-full w-3/5" opacidad={0.45} />

      <div className="relative flex flex-col items-center px-6">
        <div className="flex items-center justify-center text-hueso">
          <MarcaLineas className="pre-marca pre-marca-izq h-5 w-9 sm:h-6 sm:w-11" />

          {/*
            Versalitas: la "A" y la "P" quedan a caja alta y el resto en
            capitales pequeñas, que es el ritmo del logotipo.
          */}
          <p className="pre-nombre display text-[clamp(1.75rem,6vw,3.75rem)] text-hueso">
            AutoPrime
          </p>

          <MarcaLineas className="pre-marca pre-marca-der h-5 w-9 sm:h-6 sm:w-11" reflejada />
        </div>

        <span className="pre-barra mt-6 h-px w-40 bg-accion sm:w-56" aria-hidden="true" />

        <span className="pre-pie etiqueta mt-5 text-plomo">Atelier automotriz</span>
      </div>
    </div>
  );
}

export default Preloader;
