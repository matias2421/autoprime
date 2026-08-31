import Revelar from "./Revelar";
import LineasKv from "./LineasKv";
import { useIdioma } from "../hooks/useIdioma";
import fondo from "../assets/images/mansory-bentley-34-frontal-alto.webp";

/**
 * Testimonios de clientes.
 *
 * Son casos de muestra de un trabajo académico: ni las personas ni las
 * compras existen. Van sobre una fotografía atenuada con paneles de cristal
 * encima, que es donde el desenfoque de fondo luce de verdad.
 */
const TESTIMONIOS = [
  {
    id: "elena",
    texto:
      "Llegué con la idea de mirar y salí con fecha de entrega. Lo que más me sorprendió fue el informe: 120 puntos, con fotos de cada uno.",
    nombre: "Elena Restrepo",
    cargo: "Propietaria de un Bentley GT",
    inicial: "E",
  },
  {
    id: "mateo",
    texto:
      "Pedí ver el Elongation un sábado y me lo tuvieron listo el mismo día. El acabado en carbono se nota mucho más en persona que en foto.",
    nombre: "Mateo Villamizar",
    cargo: "Propietario de un Elongation EVO",
    inicial: "M",
  },
  {
    id: "carolina",
    texto:
      "Agendé la cita desde el móvil en dos minutos y me confirmaron la franja al instante. Sin llamadas ni esperas, que era justo lo que quería.",
    nombre: "Carolina Ospina",
    cargo: "Clienta desde 2024",
    inicial: "C",
  },
];

function Testimonios() {
  const { t } = useIdioma();

  return (
    <section className="resplandor relative overflow-hidden border-t border-linea bg-negro px-5 py-20 sm:px-8 lg:py-28">
      {/* La fotografía se queda muy por detrás: es textura, no contenido. */}
      <img
        src={fondo}
        alt=""
        aria-hidden="true"
        loading="lazy"
        decoding="async"
        width={1600}
        height={1067}
        className="absolute inset-0 h-full w-full object-cover opacity-20"
      />
      <div className="absolute inset-0 bg-negro/70" />
      <LineasKv className="absolute inset-y-0 right-0 h-full w-2/5 scale-x-[-1]" opacidad={0.25} />

      <div className="relative mx-auto max-w-[1600px]">
        <Revelar>
          <p className="etiqueta text-accion">{t("sec.testimonios")}</p>
          <h2 className="display mt-3 max-w-3xl text-4xl text-hueso sm:text-6xl">
            {t("sec.loQueDicen")}
          </h2>
        </Revelar>

        <div className="mt-12 grid gap-6 lg:grid-cols-3">
          {TESTIMONIOS.map(({ id, texto, nombre, cargo, inicial }, i) => (
            <Revelar key={id} retraso={i * 100}>
              <figure className="cristal flex h-full flex-col p-8 lg:p-10">
                {/* Comilla decorativa: no aporta nada que leer en voz alta. */}
                <span
                  aria-hidden="true"
                  className="display select-none text-6xl leading-none text-accion"
                >
                  &ldquo;
                </span>

                <blockquote className="mt-4 flex-1 text-base leading-relaxed text-hueso">
                  {texto}
                </blockquote>

                <figcaption className="mt-8 flex items-center gap-4 border-t border-hueso/15 pt-6">
                  <span
                    aria-hidden="true"
                    className="flex h-11 w-11 shrink-0 items-center justify-center
                               bg-accion-fondo font-sans text-sm font-medium text-hueso"
                  >
                    {inicial}
                  </span>
                  <span>
                    <span className="block font-sans text-sm text-hueso">{nombre}</span>
                    <span className="etiqueta mt-1 block text-ceniza">{cargo}</span>
                  </span>
                </figcaption>
              </figure>
            </Revelar>
          ))}
        </div>
      </div>
    </section>
  );
}

export default Testimonios;
