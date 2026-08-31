import { Link } from "react-router-dom";
import Carousel from "../components/Carousel";
import Revelar from "../components/Revelar";
import SeccionInmersiva from "../components/SeccionInmersiva";
import Testimonios from "../components/Testimonios";
import Button from "../components/ui/Button";
import Icono from "../components/ui/Icono";
import showroom from "../assets/images/seccion-showroom.webp";
import pista from "../assets/images/seccion-pista.webp";
import interior from "../assets/images/detalle-interior.webp";
import rueda from "../assets/images/detalle-rueda.webp";
import { useIdioma } from "../hooks/useIdioma";
import { FAMILIAS, buscarVehiculo, formatearPrecio, vehiculos } from "../data/vehiculos";

/* --- Contenido que antes vivia en la portada --- */

const enPortada = ["pugnator-tricolore", "art-piece-al3c", "p9lm-evo-900"]
  .map(buscarVehiculo)
  .filter(Boolean);

const CIFRAS = [
  { dato: "10", texto: "Preparaciones en catálogo" },
  { dato: "1.479", texto: "Caballos del más potente" },
  { dato: "8", texto: "Marcas base intervenidas" },
  { dato: "2,4 s", texto: "Mejor aceleración a 100" },
];

const NOTICIAS = [
  {
    etiqueta: "Atelier",
    fecha: "2026-07-14",
    fechaTexto: "14 de julio de 2026",
    titulo: "El Pugnator Tricolore sale del taller",
    resumen:
      "Cuatro meses de trabajo sobre el primer cuatro puertas de Maranello. El tricolor del costado se pintó a mano, capa por capa, sin plantillas.",
  },
  {
    etiqueta: "Colaboración",
    fecha: "2026-05-30",
    fechaTexto: "30 de mayo de 2026",
    titulo: "Alec Monopoly interviene un G 63",
    resumen:
      "El artista neoyorquino trabajó tres semanas sobre la carrocería. Ninguna cara del vehículo se repite y el resultado es irrepetible por definición.",
  },
  {
    etiqueta: "Técnica",
    fecha: "2026-03-08",
    fechaTexto: "8 de marzo de 2026",
    titulo: "Novecientos caballos a cielo abierto",
    resumen:
      "El P9LM EVO 900 Cabrio pasa de 650 a 900 hp con turbos nuevos y admisión revisada. Siete unidades en el mundo, ninguna igual a otra.",
  },
];

const PASOS = [
  {
    titulo: "Elige la preparación",
    texto: "Diez piezas en catálogo, de la berlina más silenciosa al W16 de cuatro turbos.",
  },
  {
    titulo: "Agenda tu cita",
    texto: "Escoges día y hora en el calendario; el taller confirma la franja al instante.",
  },
  {
    titulo: "Recíbela a medida",
    texto: "Cada unidad se documenta pieza a pieza antes de salir del atelier.",
  },
];

const VALORES = [
  {
    icono: "escudo",
    titulo: "Transparencia",
    texto:
      "Publicamos el peritaje completo de cada vehículo, con fotos reales y el historial de mantenimiento a la vista.",
  },
  {
    icono: "usuario",
    titulo: "Cercanía",
    texto:
      "Un asesor acompaña todo el proceso, desde la primera visita hasta la entrega de la tarjeta de propiedad.",
  },
  {
    icono: "herramienta",
    titulo: "Respaldo",
    texto:
      "Taller propio, repuestos originales y garantía escrita de dos años en motor y caja de cambios.",
  },
];

const HITOS = [
  ["2008", "Abrimos el primer patio de venta en Pereira con 12 vehículos."],
  ["2014", "Inauguramos el taller de mantenimiento y el área de peritaje técnico."],
  ["2019", "Sumamos la línea de altas prestaciones al catálogo."],
  ["2023", "Nuestro equipo debuta en el campeonato nacional de resistencia."],
  ["2026", "Lanzamos la plataforma en línea para agendar pruebas de manejo."],
];

function QuienesSomos() {
  const { t } = useIdioma();

  return (
    <>
      {/* ---------------------------- Hero ---------------------------- */}
      <section className="relative min-h-[80vh] w-full overflow-hidden">
        <img
          src={showroom}
          alt="Sala de exhibición de AutoPrime en Pereira"
          width={1600}
          height={900}
          loading="eager"
          fetchPriority="high"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="velo absolute inset-0" />

        <div className="relative flex min-h-[80vh] flex-col justify-end px-5 pb-16 pt-28 sm:px-12 lg:px-16">
          <p className="etiqueta text-accion-claro">El concesionario</p>
          <h1 className="display mt-5 max-w-4xl text-5xl text-hueso sm:text-7xl lg:text-8xl">
            Respondemos
            <br />
            después de la venta
          </h1>
          <p className="mt-6 max-w-xl leading-relaxed text-ceniza">
            AutoPrime nació en 2008 en Pereira como un patio familiar de doce
            vehículos. Hoy somos un concesionario de altas prestaciones con
            taller propio, área de peritaje y más de 4.200 entregas.
          </p>
        </div>
      </section>

      {/* ------------------------ Misión / visión ---------------------- */}
      <section className="mx-auto max-w-[1600px] px-5 py-20 sm:px-8 lg:py-28">
        <div className="grid gap-12 lg:grid-cols-2 lg:gap-20">
          <div>
            <p className="etiqueta text-accion-claro">Misión</p>
            <h2 className="display mt-4 text-4xl text-hueso sm:text-5xl">
              Comprar sin saltar al vacío
            </h2>
            <p className="mt-6 leading-relaxed text-ceniza">
              Verificamos cada vehículo que entra a nuestro inventario,
              explicamos con claridad el estado real en el que se encuentra y
              respaldamos por escrito lo que prometemos.
            </p>

            <p className="etiqueta mt-14 text-accion-claro">Visión</p>
            <h2 className="display mt-4 text-4xl text-hueso sm:text-5xl">
              La mejor posventa del Eje
            </h2>
            <p className="mt-6 leading-relaxed text-ceniza">
              Ser en 2030 el concesionario con mejor reputación de servicio
              posventa del Eje Cafetero, con una plataforma digital que permita
              completar toda la compra en línea.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <img
              src={interior}
              alt="Habitáculo de uno de los vehículos del catálogo"
              width={1600}
              height={900}
              loading="lazy"
              decoding="async"
              className="aspect-[4/5] w-full object-cover sm:col-span-2"
            />
            <img
              src={rueda}
              alt="Llanta forjada y pinza de freno"
              width={1200}
              height={675}
              loading="lazy"
              decoding="async"
              className="aspect-square w-full object-cover"
            />
            <img
              src={pista}
              alt="Vehículo de competición del equipo AutoPrime"
              width={1800}
              height={1012}
              loading="lazy"
              decoding="async"
              className="aspect-square w-full object-cover"
            />
          </div>
        </div>
      </section>

      {/* --------------------------- Valores --------------------------- */}
      <section className="border-t border-linea px-5 py-20 sm:px-8 lg:py-28">
        <div className="mx-auto max-w-[1600px]">
          <p className="etiqueta text-accion-claro">Lo que nos define</p>
          <h2 className="display mt-4 text-4xl text-hueso sm:text-6xl">
            Tres compromisos
          </h2>

          <ul className="mt-12 grid gap-4 md:grid-cols-3">
            {VALORES.map((valor) => (
              <li key={valor.titulo} className="cristal cristal-vivo reflejo alza p-8 lg:p-10">
                <span className="flex h-12 w-12 items-center justify-center border border-accion/40 text-accion">
                  <Icono nombre={valor.icono} className="h-5 w-5" />
                </span>
                <h3 className="display mt-6 text-2xl text-hueso">
                  {valor.titulo}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-ceniza">
                  {valor.texto}
                </p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* ------------------------- Trayectoria ------------------------- */}
      <section className="border-t border-linea px-5 py-20 sm:px-8 lg:py-28">
        <div className="mx-auto max-w-[1600px]">
          <p className="etiqueta text-accion-claro">Trayectoria</p>
          <h2 className="display mt-4 text-4xl text-hueso sm:text-6xl">
            Dieciocho años
          </h2>

          <ol className="mt-12">
            {HITOS.map(([anio, texto]) => (
              <li
                key={anio}
                className="flex flex-col gap-2 border-b border-linea py-7 sm:flex-row sm:gap-12"
              >
                <span className="display shrink-0 text-3xl text-accion sm:w-32">
                  {anio}
                </span>
                <p className="leading-relaxed text-ceniza">{texto}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* ----------------------------- CTA ----------------------------- */}
      {/* ------------------------ Accesos rápidos por serie ------------------- */}
      <section className="border-y border-linea bg-negro">
        <div className="mx-auto max-w-[1600px] px-5 py-10 sm:px-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <p className="etiqueta text-plomo">{t("sec.explorar")}</p>

            <div className="flex flex-wrap gap-3">
              {FAMILIAS.map(({ valor, etiqueta }) => (
                <Link
                  key={valor}
                  to={`/modelos?familia=${valor}`}
                  className="cristal cristal-vivo reflejo alza pulsable flex min-h-11 items-center gap-3 px-5
                             font-sans text-xs uppercase tracking-[0.14em] text-ceniza
                             hover:text-accion"
                >
                  {etiqueta}
                  <span className="text-plomo">
                    {vehiculos.filter((v) => v.familia === valor).length}
                  </span>
                </Link>
              ))}

              <Link
                to="/modelos"
                className="avanza flex min-h-11 items-center gap-2 px-5 font-sans text-xs uppercase
                           tracking-[0.14em] text-accion transition-colors duration-200
                           hover:text-accion-claro"
              >
                {t("acc.verDiez")}
                <Icono nombre="derecha" className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* -------------------------------- Cifras ------------------------------ */}
      <section className="resplandor border-b border-linea bg-negro">
        <div className="mx-auto grid max-w-[1600px] grid-cols-2 gap-4 px-5 py-12 sm:px-8 lg:grid-cols-4">
          {CIFRAS.map(({ dato, texto }, i) => (
            <Revelar key={dato} retraso={i * 80} className="cristal-sutil px-6 py-10 text-center">
              <span className="display block text-5xl text-hueso sm:text-6xl">{dato}</span>
              <span className="etiqueta mt-3 block text-plomo">{texto}</span>
            </Revelar>
          ))}
        </div>
      </section>

      {/* -------------------- Atelier: el carrusel --------------------------- */}
      <section className="resplandor bg-carbon px-5 py-20 sm:px-8 lg:py-28">
        <div className="mx-auto max-w-[1600px]">
          <Revelar className="mb-12 flex flex-wrap items-end justify-between gap-6">
            <div>
              <p className="etiqueta text-ceniza">{t("sec.atelier")}</p>
              <h2 className="display mt-3 text-4xl text-hueso sm:text-6xl">
                {t("sec.ultimas")}
              </h2>
            </div>

            <Link
              to="/modelos"
              className="avanza flex min-h-11 items-center gap-2 font-sans text-xs uppercase
                         tracking-[0.14em] text-accion transition-colors duration-200
                         hover:text-accion-claro"
            >
              {t("acc.catalogo")}
              <Icono nombre="derecha" className="h-4 w-4" />
            </Link>
          </Revelar>

          <Carousel />
        </div>
      </section>

      {/* ------------------------------ Actualidad ---------------------------- */}
      <section className="resplandor border-t border-linea bg-negro px-5 py-20 sm:px-8 lg:py-28">
        <div className="mx-auto max-w-[1600px]">
          <Revelar>
            <p className="etiqueta text-accion">{t("sec.actualidad")}</p>
            <h2 className="display mt-3 text-4xl text-hueso sm:text-6xl">{t("sec.taller")}</h2>
          </Revelar>

          <div className="mt-12 grid gap-4 lg:grid-cols-3">
            {NOTICIAS.map(({ etiqueta, fecha, fechaTexto, titulo, resumen }, i) => (
              <Revelar
                key={titulo}
                retraso={i * 100}
                as="article"
                className="cristal cristal-vivo reflejo alza p-8 lg:p-10"
              >
                <p className="etiqueta text-accion">{etiqueta}</p>
                <time dateTime={fecha} className="mt-3 block font-sans text-xs text-plomo">
                  {fechaTexto}
                </time>
                <h3 className="display mt-5 text-2xl text-hueso sm:text-3xl">{titulo}</h3>
                <p className="mt-4 text-sm leading-relaxed text-ceniza">{resumen}</p>
              </Revelar>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------- Recorrido inmersivo con scroll ------------------- */}
      <SeccionInmersiva />

      {/* --------------------------- Piezas de autor -------------------------- */}
      <section className="resplandor border-t border-linea bg-carbon px-5 py-20 sm:px-8 lg:py-28">
        <div className="mx-auto max-w-[1600px]">
          <Revelar>
            <p className="etiqueta text-accion">{t("sec.seleccion")}</p>
            <h2 className="display mt-3 text-4xl text-hueso sm:text-6xl">{t("sec.piezas")}</h2>
          </Revelar>

          <div className="mt-12 grid gap-6 lg:grid-cols-3">
            {enPortada.map((vehiculo, i) => (
              <Revelar key={vehiculo.slug} retraso={i * 100}>
                <Link
                  to={`/modelos/${vehiculo.slug}`}
                  className="cristal cristal-vivo reflejo alza group block"
                >
                  {/* 3:2 exacto: las fotografías caben enteras, sin recorte. */}
                  <div className="relative aspect-[3/2] overflow-hidden bg-negro">
                    <img
                      src={vehiculo.imagen}
                      alt={vehiculo.titulo}
                      width={1600}
                      height={1067}
                      loading="lazy"
                      decoding="async"
                      className="h-full w-full object-cover transition-transform duration-700
                                 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-[1.03]"
                    />
                  </div>

                  <div className="p-6 sm:p-8">
                    <p className="etiqueta text-plomo">{vehiculo.base}</p>
                    <h3 className="display mt-2 text-2xl text-hueso sm:text-3xl">
                      {vehiculo.modelo}
                    </h3>
                    <p className="mt-4 text-sm leading-relaxed text-ceniza">{vehiculo.lema}</p>

                    <div className="mt-6 flex items-center justify-between border-t border-linea pt-5">
                      <span className="font-sans text-xs uppercase tracking-[0.14em] text-plomo">
                        {formatearPrecio(vehiculo.precio)}
                      </span>
                      <span
                        className="flex items-center gap-2 font-sans text-xs uppercase
                                   tracking-[0.14em] text-accion"
                      >
                        {t("acc.verFicha")}
                        <Icono nombre="derecha" className="h-4 w-4" />
                      </span>
                    </div>
                  </div>
                </Link>
              </Revelar>
            ))}
          </div>
        </div>
      </section>

      {/* --------------------------- Cómo funciona ---------------------------- */}
      <section className="border-t border-linea bg-negro px-5 py-20 sm:px-8 lg:py-28">
        <div className="mx-auto grid max-w-[1600px] gap-14 lg:grid-cols-[0.9fr_1.1fr] lg:gap-20">
          <Revelar>
            <p className="etiqueta text-accion">{t("sec.comoFunciona")}</p>
            <h2 className="display mt-3 text-4xl text-hueso sm:text-5xl">
              {t("sec.tresPasos")}
            </h2>
            <p className="mt-6 max-w-md text-base leading-relaxed text-ceniza">
              Ninguna de estas piezas se compra por catálogo. El proceso empieza con una
              conversación y termina con una entrega documentada.
            </p>
            <Button to="/agendar" variante="primario" tamano="lg" className="mt-9">
              {t("acc.agendar")}
            </Button>
          </Revelar>

          <ol className="grid gap-4">
            {PASOS.map(({ titulo, texto }, i) => (
              <Revelar
                key={titulo}
                as="li"
                retraso={i * 100}
                className="cristal-sutil flex gap-6 p-8 sm:gap-8 sm:p-10"
              >
                <span className="display shrink-0 text-4xl text-accion">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <h3 className="font-sans text-base uppercase tracking-[0.1em] text-hueso">
                    {titulo}
                  </h3>
                  <p className="mt-3 text-sm leading-relaxed text-ceniza">{texto}</p>
                </div>
              </Revelar>
            ))}
          </ol>
        </div>
      </section>

      {/* ----------------------------- Testimonios ---------------------------- */}
      <Testimonios />

      <section className="border-t border-linea px-5 py-24 sm:px-8 lg:py-32">
        <div className="mx-auto max-w-[1600px] text-center">
          <h2 className="display mx-auto max-w-3xl text-4xl text-hueso sm:text-6xl">
            ¿Quieres conocernos en persona?
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-ceniza">
            Visítanos en la Av. Las Américas #45-12, Pereira, o escríbenos y un
            asesor te contacta el mismo día hábil.
          </p>
          <div className="mt-10 flex flex-wrap justify-center gap-3">
            <Button to="/contacto" tamano="lg">
              Escríbenos
              <Icono nombre="flecha" className="h-4 w-4" />
            </Button>
            <Button to="/modelos" variante="contorno" tamano="lg">
              Ver los modelos
            </Button>
          </div>
        </div>
      </section>
    </>
  );
}

export default QuienesSomos;
