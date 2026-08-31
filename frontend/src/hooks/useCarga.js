import { useCallback, useEffect, useState } from "react";

/**
 * Carga datos de la API para una pantalla.
 *
 * Detalle importante: ningun `setState` se llama en el cuerpo del efecto, sino
 * dentro de los callbacks de la promesa. Es lo que recomienda React para no
 * encadenar renders, y ademas evita el parpadeo al recargar: la tabla conserva
 * los datos anteriores mientras llega la nueva respuesta.
 *
 * `obtener` debe venir memorizado con useCallback en el componente.
 */
export function useCarga(obtener) {
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [ticket, setTicket] = useState(0);

  useEffect(() => {
    let vigente = true;

    obtener()
      .then((resultado) => {
        if (!vigente) return;
        setDatos(resultado);
        setError("");
      })
      .catch((fallo) => {
        if (vigente) setError(fallo.message);
      })
      .finally(() => {
        if (vigente) setCargando(false);
      });

    return () => {
      vigente = false;
    };
  }, [obtener, ticket]);

  /** Vuelve a pedir los datos (tras crear, editar o borrar algo). */
  const recargar = useCallback(() => setTicket((t) => t + 1), []);

  return { datos, cargando, error, setError, recargar };
}
