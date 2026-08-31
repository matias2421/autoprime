import { useEffect } from "react";

/**
 * Registro de quién está pidiendo bloquear el desplazamiento.
 *
 * Varias cosas pueden pedirlo a la vez —la cortina de entrada, la portada, un
 * diálogo—, y ese solapamiento es justo lo que rompe el patrón de "guardo el
 * valor anterior y lo restauro al salir":
 *
 *   1. la cortina llega, guarda "" y bloquea;
 *   2. la portada llega, guarda "hidden" (¡el de la cortina!) y bloquea;
 *   3. la cortina se retira y devuelve "";
 *   4. la portada se retira y devuelve "hidden", que ya no era de nadie.
 *
 * Resultado: el desplazamiento quedaba bloqueado en todo el sitio. Con un
 * conjunto de motivos no hay valor que restaurar: el bloqueo está puesto
 * mientras quede algún motivo y se levanta cuando no queda ninguno.
 */
const motivos = new Set();

function aplicar() {
  const bloquear = motivos.size > 0;
  const valor = bloquear ? "hidden" : "";

  document.documentElement.style.overflow = valor;
  document.body.style.overflow = valor;
}

/**
 * Bloquea el desplazamiento de la página mientras el componente esté montado.
 *
 * @param {string}  motivo  Identificador de quién pide el bloqueo.
 * @param {boolean} activo  Permite pedirlo de forma condicional.
 */
export function useBloqueoScroll(motivo, activo = true) {
  useEffect(() => {
    if (!activo) return undefined;

    motivos.add(motivo);
    aplicar();

    return () => {
      motivos.delete(motivo);
      aplicar();
    };
  }, [motivo, activo]);
}
