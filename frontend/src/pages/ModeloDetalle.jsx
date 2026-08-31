import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import LineasKv from "../components/LineasKv";
import Revelar from "../components/Revelar";
import Visor3D from "../components/Visor3D";
import Button from "../components/ui/Button";
import Icono from "../components/ui/Icono";
import NoEncontrado from "./NoEncontrado";
import {
  FAMILIAS,
  buscarVehiculo,
  formatearKilometraje,
  formatearPrecio,
  vehiculos,
} from "../data/vehiculos";

/*
 * Secciones del submenú pegajoso, en orden de lectura. La de "En 3D" solo
 * aparece en los vehículos que tienen malla tridimensional.
 */
function apartadosDe(vehiculo) {
  return [
    { id: "introduccion", texto: "Introducción" },
    ...(vehiculo?.modelo3d ? [{ id: "tresd", texto: "En 3D" }] : []),
    { id: "ficha", texto: "Ficha técnica" },
    { id: "galeria", texto: "Galería" },
    { id: "alternativas", texto: "Alternativas" },
  ];
}

/* Alto del encabezado fijo (76 px) más el del propio submenú. */
const DESPLAZAMIENTO = "scroll-mt-[136px]";

/**
 * Marca en el submenú el apartado que se está leyendo.
 *
 * La franja de observación se ciñe al tercio superior de la ventana para que
 * el apartado activo cambie cuando su título cruza esa zona, y no cuando
 * asoma por abajo.
 */
function useApartadoActivo(ids) {
  const [activo, setActivo] = useState(ids[0]);
  const idsRef = useRef(ids);

  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return undefined;

    const observador = new IntersectionObserver(
      (entradas) => {
        const visibles = entradas
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);

        if (visibles[0]) setActivo(visibles[0].target.id);
      },
      { rootMargin: "-136px 0px -66% 0px", threshold: 0 }
    );

    idsRef.current.forEach((id) => {
      const nodo = document.getElementById(id);
      if (nodo) observador.observe(nodo);
    });

    return () => observador.disconnect();
  }, []);

  return activo;
}

function ModeloDetalle() {
  const { slug } = useParams();
  const vehiculo = buscarVehiculo(slug);
  const apartados = apartadosDe(vehiculo);
  const activo = useApartadoActivo(apartados.map((a) => a.id));

  if (!vehiculo) return <NoEncontrado />;

  const familia = FAMILIAS.find((f) => f.valor === vehiculo.familia);

  const relacionados = vehiculos
    .filter((item) => item.slug !== vehiculo.slug && item.familia === vehiculo.familia)
    .concat(vehiculos.filter((item) => item.slug !== vehiculo.slug))
    .filter((item, i, lista) => lista.findIndex((x) => x.slug === item.slug) === i)
    .slice(0, 3);

  const fichaTecnica = [
    ["Vehículo base", vehiculo.base],
    ["Motor", vehiculo.specs.motor],
    ["Potencia máxima", vehiculo.specs.potencia],
    ["0–100 km/h", vehiculo.specs.aceleracion],
    ["Velocidad máxima", vehiculo.specs.velocidad],
    ["Transmisión", vehiculo.specs.transmision],
    ["Tracción", vehiculo.specs.traccion],
    ["Año", String(vehiculo.anio)],
    ["Kilometraje", formatearKilometraje(vehiculo.kilometraje)],
    [
      "Unidades",
      vehiculo.unidades === null
        ? "Serie no limitada"
        : `${vehiculo.unidades} ${vehiculo.unidades === 1 ? "unidad" : "unidades"}`,
    ],
  ];

  return (
    <>
      {/* ------------------------------- Portada ------------------------------ */}
      <section className="relative flex min-h-[88vh] items-end overflow-hidden bg-negro">
        <img
          src={vehiculo.imagen}
          alt={vehiculo.titulo}
          width={1600}
          height={1067}
          decoding="async"
          className="absolute inset-0 h-full w-full object-cover"
          fetchPriority="high"
        />
        <div className="velo absolute inset-0" />
        <LineasKv className="absolute inset-y-0 left-0 h-full w-1/2" opacidad={0.3} />

        <div className="relative z-10 w-full px-5 pb-14 sm:px-12 lg:px-16 lg:pb-20">
          <nav aria-label="Ruta de navegación" className="mb-6">
            <ol className="flex flex-wrap items-center gap-2 font-sans text-xs text-ceniza">
              <li>
                <Link to="/modelos" className="subrayado transition-colors hover:text-accion">
                  Modelos
                </Link>
              </li>
              <li aria-hidden="true" className="text-plomo">/</li>
              <li className="text-plomo">{familia?.etiqueta}</li>
            </ol>
          </nav>

          <div className="flex flex-wrap gap-2">
            <span className="etiqueta border border-accion/60 px-3 py-1.5 text-accion">
              {familia?.etiqueta}
            </span>
            <span className="etiqueta border border-hueso/25 px-3 py-1.5 text-ceniza">
              {vehiculo.base}
            </span>
          </div>

          <h1 className="display mt-5 max-w-4xl text-[clamp(2.5rem,7vw,5.5rem)] text-hueso">
            {vehiculo.titulo}
          </h1>

          <p className="mt-4 max-w-xl text-base leading-relaxed text-ceniza">{vehiculo.lema}</p>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Button to="/agendar" variante="primario" tamano="lg">
              Solicitar precio
            </Button>
            <span className="font-sans text-sm uppercase tracking-[0.14em] text-hueso">
              {formatearPrecio(vehiculo.precio)}
            </span>
          </div>
        </div>
      </section>

      {/* ---------------------- Submenú pegajoso del modelo ------------------- */}
      <nav
        aria-label="Apartados de la ficha"
        className="sticky top-[76px] z-30 border-y border-linea bg-negro/95 backdrop-blur-md"
      >
        <ul className="mx-auto flex max-w-[1600px] gap-2 overflow-x-auto px-5 sm:px-8">
          {apartados.map(({ id, texto }) => (
            <li key={id}>
              <a
                href={`#${id}`}
                aria-current={activo === id ? "true" : undefined}
                className={[
                  "relative flex min-h-14 items-center whitespace-nowrap px-4 font-sans",
                  "text-xs uppercase tracking-[0.14em] transition-colors duration-200",
                  activo === id
                    ? "text-accion after:absolute after:inset-x-2 after:bottom-0 after:h-0.5 after:bg-accion"
                    : "text-plomo hover:text-hueso",
                ].join(" ")}
              >
                {texto}
              </a>
            </li>
          ))}
        </ul>
      </nav>

      {/* ----------------------------- Introducción --------------------------- */}
      <section
        id="introduccion"
        className={`border-b border-linea bg-negro px-5 py-20 sm:px-8 lg:py-28 ${DESPLAZAMIENTO}`}
      >
        <div className="mx-auto grid max-w-[1600px] gap-12 lg:grid-cols-[1fr_1fr] lg:gap-20">
          <Revelar>
            <p className="etiqueta text-accion">Introducción</p>
            <h2 className="display mt-3 text-3xl text-hueso sm:text-5xl">
              Qué cambia respecto al original
            </h2>
          </Revelar>

          <Revelar retraso={100}>
            <ul className="grid gap-px bg-linea">
              {vehiculo.puntos.map((punto) => (
                <li key={punto} className="flex items-start gap-4 bg-negro py-5">
                  <Icono nombre="check" className="mt-0.5 h-5 w-5 shrink-0 text-accion" />
                  <span className="text-base leading-relaxed text-hueso">{punto}</span>
                </li>
              ))}
            </ul>

            <p className="mt-8 text-base leading-relaxed text-ceniza">{vehiculo.descripcion}</p>
          </Revelar>
        </div>
      </section>

      {/* -------------------------------- En 3D ------------------------------- */}
      {vehiculo.modelo3d && (
        <section
          id="tresd"
          className={`resplandor border-b border-linea bg-negro px-5 py-20 sm:px-8 lg:py-28 ${DESPLAZAMIENTO}`}
        >
          <div className="mx-auto max-w-[1600px]">
            <Revelar className="mb-12">
              <p className="etiqueta text-accion">En 3D</p>
              <h2 className="display mt-3 text-3xl text-hueso sm:text-5xl">
                Gíralo y míralo por donde quieras
              </h2>
              <p className="mt-4 max-w-xl text-base leading-relaxed text-ceniza">
                Arrastra para rotarlo y usa la rueda para acercarte. En pantalla
                táctil, un dedo gira y dos acercan.
              </p>
            </Revelar>

            <Revelar retraso={100}>
              <Visor3D
                src={vehiculo.modelo3d.archivo}
                peso={vehiculo.modelo3d.peso}
                poster={vehiculo.imagen}
                alt={`Modelo tridimensional del ${vehiculo.titulo}`}
                titulo={vehiculo.modelo}
              />
            </Revelar>
          </div>
        </section>
      )}

      {/* ----------------------------- Ficha técnica -------------------------- */}
      <section
        id="ficha"
        className={`resplandor bg-carbon px-5 py-20 sm:px-8 lg:py-28 ${DESPLAZAMIENTO}`}
      >
        <div className="mx-auto max-w-[1600px]">
          <Revelar>
            <p className="etiqueta text-accion">Ficha técnica</p>
            <h2 className="display mt-3 text-3xl text-hueso sm:text-5xl">Las cifras</h2>
          </Revelar>

          <Revelar retraso={100} className="mt-12">
            <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {fichaTecnica.map(([etiqueta, valor]) => (
                <div key={etiqueta} className="cristal cristal-vivo reflejo alza p-6 sm:p-8">
                  <dt className="etiqueta text-plomo">{etiqueta}</dt>
                  <dd className="display mt-2 text-2xl text-hueso sm:text-3xl">{valor}</dd>
                </div>
              ))}
            </dl>
          </Revelar>
        </div>
      </section>

      {/* -------------------------------- Galería ----------------------------- */}
      <section
        id="galeria"
        className={`border-b border-linea bg-negro px-5 py-20 sm:px-8 lg:py-28 ${DESPLAZAMIENTO}`}
      >
        <div className="mx-auto max-w-[1600px]">
          <Revelar>
            <p className="etiqueta text-accion">Galería</p>
            <h2 className="display mt-3 text-3xl text-hueso sm:text-5xl">
              {vehiculo.galeria.length} vistas del vehículo
            </h2>
          </Revelar>

          {/*
            Todas las fotografías son 3:2, así que el contenedor usa esa misma
            proporción: la imagen entra completa y nunca se recorta el coche.
          */}
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {vehiculo.galeria.map((foto, i) => (
              <Revelar key={foto} retraso={(i % 3) * 90}>
                <figure className="cristal cristal-vivo reflejo alza aspect-[3/2] overflow-hidden">
                  <img
                    src={foto}
                    alt={`${vehiculo.titulo} — vista ${i + 1} de ${vehiculo.galeria.length}`}
                    width={1600}
                    height={1067}
                    loading={i < 3 ? "eager" : "lazy"}
                    decoding="async"
                    className="h-full w-full object-cover transition-transform duration-700
                               ease-[cubic-bezier(0.16,1,0.3,1)] hover:scale-[1.04]"
                  />
                </figure>
              </Revelar>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------ Alternativas -------------------------- */}
      <section
        id="alternativas"
        className={`bg-negro px-5 py-20 sm:px-8 lg:py-28 ${DESPLAZAMIENTO}`}
      >
        <div className="mx-auto max-w-[1600px]">
          <Revelar className="mb-12 flex flex-wrap items-end justify-between gap-6">
            <div>
              <p className="etiqueta text-accion">Alternativas</p>
              <h2 className="display mt-3 text-3xl text-hueso sm:text-5xl">
                Otras piezas del atelier
              </h2>
            </div>

            <Link
              to="/modelos"
              className="avanza flex min-h-11 items-center gap-2 font-sans text-xs uppercase
                         tracking-[0.14em] text-accion transition-colors duration-200
                         hover:text-accion-claro"
            >
              Todo el catálogo
              <Icono nombre="derecha" className="h-4 w-4" />
            </Link>
          </Revelar>

          <div className="grid gap-6 lg:grid-cols-3">
            {relacionados.map((item, i) => (
              <Revelar key={item.slug} retraso={i * 100}>
                <Link
                  to={`/modelos/${item.slug}`}
                  className="cristal cristal-vivo reflejo alza group block"
                >
                  <div className="aspect-[3/2] overflow-hidden bg-negro">
                    <img
                      src={item.imagen}
                      alt={item.titulo}
                      width={1600}
                      height={1067}
                      loading="lazy"
                      decoding="async"
                      className="h-full w-full object-cover transition-transform duration-700
                                 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-[1.03]"
                    />
                  </div>

                  <div className="p-6">
                    <p className="etiqueta text-plomo">{item.base}</p>
                    <h3 className="display mt-2 text-2xl text-hueso">{item.modelo}</h3>
                    <p className="mt-4 font-sans text-xs uppercase tracking-[0.14em] text-accion">
                      {item.specs.potencia}
                    </p>
                  </div>
                </Link>
              </Revelar>
            ))}
          </div>
        </div>
      </section>

      {/* --------------------------- Cierre: atelier -------------------------- */}
      <section className="resplandor resplandor-centro border-t border-linea bg-negro px-5 py-20 sm:px-8 lg:py-28">
        <Revelar className="mx-auto max-w-3xl text-center">
          <p className="etiqueta text-accion">Atelier AutoPrime</p>
          <h2 className="display mt-4 text-3xl text-hueso sm:text-5xl">
            ¿Te interesa esta pieza?
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-ceniza">
            Reserva una franja en el taller y la vemos en persona. Si prefieres otra
            configuración, partimos de ahí.
          </p>

          <div className="mt-9 flex flex-wrap justify-center gap-4">
            <Button to="/agendar" variante="primario" tamano="lg">
              Agendar una cita
            </Button>
            <Button
              to="/contacto"
              variante="contorno"
              tamano="lg"
              className="cristal cristal-vivo reflejo alza text-hueso"
            >
              Escribir al atelier
            </Button>
          </div>
        </Revelar>
      </section>
    </>
  );
}

export default ModeloDetalle;
