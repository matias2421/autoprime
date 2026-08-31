import { useEffect, useRef, useState } from "react";
import Button from "./ui/Button";
import Icono from "./ui/Icono";

/**
 * Visor 3D de un vehículo.
 *
 * No carga nada hasta que se pide. El modelo pesa varios megas y la librería
 * del visor otro tanto, así que arrancarlos con la página castigaría a todo el
 * que solo viene a leer la ficha. Al pulsar "Ver en 3D" se importa la librería
 * y se descarga el `.glb`; hasta entonces solo hay una fotografía y un botón.
 *
 * `model-viewer` es un componente web, no de React: se usa como etiqueta
 * suelta y se le habla por atributos. Por eso el aviso de carga se lee de sus
 * propios eventos y no del estado de React.
 */
function Visor3D({ src, poster, alt, titulo, peso }) {
  const [pedido, setPedido] = useState(false);
  const [listo, setListo] = useState(false);
  const [fallo, setFallo] = useState(false);
  const [progreso, setProgreso] = useState(0);
  const visorRef = useRef(null);

  // La librería se importa solo cuando alguien pide ver el modelo.
  useEffect(() => {
    if (!pedido) return;

    let vigente = true;

    import("@google/model-viewer").catch(() => {
      if (vigente) setFallo(true);
    });

    return () => {
      vigente = false;
    };
  }, [pedido]);

  // Los eventos los emite el componente web, no React.
  useEffect(() => {
    if (!pedido) return undefined;

    const nodo = visorRef.current;
    if (!nodo) return undefined;

    const alProgresar = (evento) => {
      setProgreso(Math.round((evento.detail?.totalProgress ?? 0) * 100));
    };
    /*
     * Corrección del material al terminar de cargar.
     *
     * El modelo viene de un escaneo y su mapa PBR daba metalicidad media 0,53
     * con el factor a 1. En PBR una superficie metálica no tiene componente
     * difusa: su color sale entero de reflejar el entorno. Con un difuso de
     * luminancia mediana 30/255 —el coche es negro carbono— y una iluminación
     * de estudio tenue, el resultado era negro sobre negro.
     *
     * En un escaneo el aspecto ya está horneado en la textura difusa, así que
     * lo correcto es quitar el metal y dejar que sea esa textura la que mande.
     */
    const alCargar = () => {
      setListo(true);

      // Por si el póster interno siguiera puesto: taparía el modelo entero.
      nodo.dismissPoster?.();

      nodo.model?.materials?.forEach((material) => {
        const pbr = material.pbrMetallicRoughness;
        pbr.setMetallicFactor(0);
        pbr.setRoughnessFactor(0.65);
      });
    };
    const alFallar = () => setFallo(true);

    nodo.addEventListener("progress", alProgresar);
    nodo.addEventListener("load", alCargar);
    nodo.addEventListener("error", alFallar);

    return () => {
      nodo.removeEventListener("progress", alProgresar);
      nodo.removeEventListener("load", alCargar);
      nodo.removeEventListener("error", alFallar);
    };
  }, [pedido]);

  return (
    <div className="relative aspect-[3/2] max-h-[760px] w-full overflow-hidden border border-hueso/12">
      {/*
        El cristal va como capa HERMANA por detrás, no envolviendo al visor.
        Un lienzo WebGL dentro de un elemento con `backdrop-filter` no llega a
        componerse en Chromium: el contenedor se ve, pero el modelo no se
        pinta nunca. Poniéndolo al lado se conserva el mismo aspecto sin que
        el lienzo cuelgue de ese filtro.

        Tampoco lleva `reflejo`: su capa va en z-index 1, por encima del
        lienzo, y al pasar el ratón teñiría el modelo justo donde se arrastra
        para girarlo.
      */}
      <div className="cristal absolute inset-0" aria-hidden="true" />
      {/* Fotografía de reposo: lo que se ve antes de pedir el modelo. */}
      {!listo && (
        <img
          src={poster}
          alt={alt}
          width={1600}
          height={1067}
          loading="lazy"
          decoding="async"
          className={`absolute inset-0 z-10 h-full w-full object-cover transition-opacity duration-700 ${
            pedido && !fallo ? "opacity-30" : "opacity-100"
          }`}
        />
      )}

      {pedido && !fallo && (
        <model-viewer
          ref={visorRef}
          src={src}
          alt={alt}
          /*
            `loading="eager"` descarga el modelo sin esperar a que la sección
            entre en pantalla: el visitante ya ha pulsado "Ver en 3D", así que
            la intención está clara.

            `reveal` se deja en "auto" a propósito. Solo admite "auto" y
            "manual"; con cualquier otro valor el póster interno del visor no
            se retira nunca y tapa el modelo con un rectángulo opaco.
          */
          reveal="auto"
          loading="eager"
          camera-controls
          touch-action="pan-y"
          auto-rotate
          auto-rotate-delay="1200"
          rotation-per-second="18deg"
          interaction-prompt="none"
          shadow-intensity="0.85"
          shadow-softness="0.9"
          exposure="2"
          environment-image="neutral"
          camera-orbit="35deg 78deg auto"
          min-camera-orbit="auto auto auto"
          max-camera-orbit="auto 100deg auto"
          /*
            El ancho y el alto explícitos son imprescindibles, no redundantes
            con `inset-0`: `model-viewer` fija `width: 300px; height: 150px`
            en su `:host`, e `inset-0` solo estira el elemento cuando ambas
            medidas son `auto`. Sin esto el lienzo se queda en 300×150 pegado
            a la esquina superior izquierda.
          */
          className="visor-3d absolute inset-0 z-10 h-full w-full"
          style={{ backgroundColor: "transparent", "--poster-color": "transparent" }}
        />
      )}

      {/* Reposo: invitación a cargar el modelo. */}
      {!pedido && (
        <div className="velo absolute inset-0 z-20 flex flex-col items-center justify-center gap-4 p-6 text-center">
          <p className="etiqueta text-accion">Modelo tridimensional</p>
          <p className="max-w-sm text-sm leading-relaxed text-ceniza">
            {titulo} en 3D, para girarlo y verlo desde cualquier ángulo. Son{" "}
            {peso}: se descarga solo si lo pides.
          </p>
          <Button onClick={() => setPedido(true)} variante="primario" tamano="md">
            Ver en 3D
            <Icono nombre="flecha" className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Cargando: barra con el avance real que informa el visor. */}
      {pedido && !listo && !fallo && (
        <div
          role="status"
          aria-live="polite"
          className="absolute inset-x-0 bottom-0 z-20 flex flex-col gap-2 p-6"
        >
          <span className="etiqueta text-ceniza">Cargando modelo… {progreso}%</span>
          <span className="h-px w-full bg-linea">
            <span
              className="block h-px bg-accion transition-[width] duration-300"
              style={{ width: `${progreso}%` }}
            />
          </span>
        </div>
      )}

      {fallo && (
        <div className="velo absolute inset-0 z-20 flex flex-col items-center justify-center gap-3 p-6 text-center">
          <p className="text-sm text-ceniza">
            No se pudo cargar el modelo 3D. La fotografía sigue disponible.
          </p>
          <Button
            onClick={() => {
              setFallo(false);
              setPedido(false);
              setProgreso(0);
            }}
            variante="contorno"
            tamano="sm"
          >
            Reintentar
          </Button>
        </div>
      )}
    </div>
  );
}

export default Visor3D;
