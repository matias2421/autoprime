import { createContext, useCallback, useEffect, useMemo, useState } from "react";
import { TEXTOS } from "../data/traducciones";

const CLAVE = "autoprime:idioma";

const IdiomaContext = createContext(null);

/** Idioma inicial: el guardado, si no el del navegador y por defecto español. */
function idiomaInicial() {
  if (typeof window === "undefined") return "es";

  try {
    const guardado = window.localStorage.getItem(CLAVE);
    if (guardado === "es" || guardado === "en") return guardado;
  } catch {
    // Almacenamiento bloqueado: se sigue con el idioma del navegador.
  }

  return String(navigator.language || "es").toLowerCase().startsWith("en")
    ? "en"
    : "es";
}

function IdiomaProvider({ children }) {
  const [idioma, setIdioma] = useState(idiomaInicial);

  useEffect(() => {
    // El atributo `lang` guía a los lectores de pantalla y al corrector.
    document.documentElement.lang = idioma;

    try {
      window.localStorage.setItem(CLAVE, idioma);
    } catch {
      // Sin almacenamiento no se recuerda; no es motivo para fallar.
    }
  }, [idioma]);

  /**
   * Traduce una clave. Si falta la entrada devuelve la clave misma, que en
   * pantalla canta lo suficiente como para detectar el hueco enseguida.
   */
  const t = useCallback(
    (clave) => TEXTOS[idioma]?.[clave] ?? TEXTOS.es[clave] ?? clave,
    [idioma]
  );

  const valor = useMemo(() => ({ idioma, setIdioma, t }), [idioma, t]);

  return <IdiomaContext.Provider value={valor}>{children}</IdiomaContext.Provider>;
}

export { IdiomaContext, IdiomaProvider };
