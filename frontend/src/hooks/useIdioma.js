import { useContext } from "react";
import { IdiomaContext } from "../context/IdiomaContext";

/** Devuelve el idioma activo, su conmutador y la función de traducción `t`. */
export function useIdioma() {
  const contexto = useContext(IdiomaContext);

  if (!contexto) {
    throw new Error("useIdioma debe usarse dentro de <IdiomaProvider>.");
  }

  return contexto;
}
