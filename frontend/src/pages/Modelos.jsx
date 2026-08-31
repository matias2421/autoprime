import { Link, useSearchParams } from "react-router-dom";
import Button from "../components/ui/Button";
import Icono from "../components/ui/Icono";
import { FAMILIAS, formatearPrecio, vehiculos } from "../data/vehiculos";

const FILTROS = [{ valor: "todos", etiqueta: "Todos" }, ...FAMILIAS];

/**
 * Ficha del modelo dentro del listado.
 *
 * Cada vehículo ocupa una banda a lo ancho, sobre fondo claro y alternando
 * dos tonos. La fotografía va enmarcada en su proporción nativa 3:2, de modo
 * que se ve entera: ni un solo coche queda recortado.
 */
function TarjetaModelo({ vehiculo, indice }) {
  const alterno = indice % 2 === 1;

  return (
    <article
      className={`resplandor relative overflow-hidden border-b border-linea ${
        alterno ? "bg-carbon" : "bg-negro"
      } text-hueso`}
    >
      <div className="mx-auto max-w-[1600px] px-5 py-16 sm:px-10 lg:py-24">
        <p className="etiqueta text-center text-ceniza">Sobre {vehiculo.base}</p>

        <h2 className="display mt-3 text-center text-4xl text-hueso sm:text-6xl lg:text-7xl">
          {vehiculo.modelo}
        </h2>

        <p className="mx-auto mt-4 max-w-2xl text-center text-base leading-relaxed text-ceniza">
          {vehiculo.lema}
        </p>

        <Link
          to={`/modelos/${vehiculo.slug}`}
          className="group mt-10 block"
          tabIndex={-1}
          aria-hidden="true"
        >
          {/* Proporción nativa de las fotografías: entran completas. */}
          <div className="cristal cristal-vivo reflejo alza mx-auto aspect-[3/2] w-full max-w-5xl overflow-hidden">
            <img
              src={vehiculo.imagen}
              alt={`${vehiculo.titulo}: ${vehiculo.descripcion}`}
              width={1600}
              height={1067}
              loading={indice < 2 ? "eager" : "lazy"}
              decoding="async"
              className="h-full w-full object-cover transition-transform duration-700
                         ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-[1.03]"
            />
          </div>
        </Link>

        <p className="mx-auto mt-10 max-w-2xl text-center leading-relaxed text-ceniza">
          {vehiculo.descripcion}
        </p>

        {/* Datos clave */}
        <dl className="mx-auto mt-10 flex max-w-4xl flex-wrap justify-center gap-x-14 gap-y-6
                       border-t border-linea pt-8">
          {[
            ["Motor", vehiculo.specs.motor],
            ["Potencia", vehiculo.specs.potencia],
            ["0–100 km/h", vehiculo.specs.aceleracion],
            ["Desde", formatearPrecio(vehiculo.precio)],
          ].map(([titulo, dato]) => (
            <div key={titulo} className="text-center">
              <dt className="etiqueta text-ceniza">{titulo}</dt>
              <dd className="mt-1.5 font-sans text-base uppercase tracking-[0.08em] text-hueso">
                {dato}
              </dd>
            </div>
          ))}
        </dl>

        <div className="mt-10 flex flex-wrap justify-center gap-3">
          <Button to={`/modelos/${vehiculo.slug}`} tamano="lg">
            Explorar el modelo
          </Button>
          <Button
            to={`/agendar?modelo=${vehiculo.slug}&servicio=prueba`}
            tamano="lg"
            className="cristal cristal-vivo reflejo alza bg-transparent text-hueso"
          >
            Agendar prueba
          </Button>
          <Button
            to={`/agendar?modelo=${vehiculo.slug}&servicio=cotizacion`}
            tamano="lg"
            className="bg-transparent text-accion underline-offset-8 hover:text-accion-claro hover:underline"
          >
            Cotizar
          </Button>
        </div>
      </div>
    </article>
  );
}

function Modelos() {
  const [parametros, setParametros] = useSearchParams();
  const familia = parametros.get("familia") ?? "todos";

  const listado =
    familia === "todos"
      ? vehiculos
      : vehiculos.filter((vehiculo) => vehiculo.familia === familia);

  const cambiarFiltro = (valor) => {
    if (valor === "todos") setParametros({});
    else setParametros({ familia: valor });
  };

  return (
    <>
      {/* --------------------- Cabecera del listado --------------------- */}
      <section className="border-b border-linea bg-negro px-5 pb-8 pt-28 sm:px-8 lg:pt-32">
        <div className="mx-auto max-w-[1600px]">
          <nav aria-label="Ruta de navegación">
            <ol className="flex items-center gap-2 font-sans text-xs uppercase tracking-[0.18em] text-plomo">
              <li>
                <Link to="/" className="transition-colors duration-200 hover:text-hueso">
                  Inicio
                </Link>
              </li>
              <li aria-hidden="true">/</li>
              <li className="text-hueso">Modelos</li>
            </ol>
          </nav>

          <h1 className="display mt-6 text-5xl text-hueso sm:text-7xl lg:text-8xl">
            AutoPrime
            <br />
            <span className="text-ceniza">Modelos</span>
          </h1>

          {/* ----------------------- Filtros ----------------------- */}
          <div className="mt-10 flex flex-wrap items-center justify-between gap-6">
            <div
              role="tablist"
              aria-label="Filtrar modelos por familia"
              className="flex flex-wrap gap-x-8 gap-y-2"
            >
              {FILTROS.map((filtro) => {
                const activo = filtro.valor === familia;
                return (
                  <button
                    key={filtro.valor}
                    type="button"
                    role="tab"
                    aria-selected={activo}
                    onClick={() => cambiarFiltro(filtro.valor)}
                    className={[
                      "relative flex min-h-11 cursor-pointer items-center font-sans text-sm",
                      "uppercase tracking-[0.18em] transition-colors duration-200 hover:text-hueso",
                      activo
                        ? "text-hueso after:absolute after:inset-x-0 after:bottom-1 after:h-0.5 after:bg-accion"
                        : "text-plomo",
                    ].join(" ")}
                  >
                    {filtro.etiqueta}
                  </button>
                );
              })}
            </div>

            <p className="font-sans text-xs uppercase tracking-[0.18em] text-plomo">
              {listado.length} {listado.length === 1 ? "modelo" : "modelos"}
            </p>
          </div>
        </div>
      </section>

      {/* ------------------------- Listado ------------------------- */}
      {listado.length > 0 ? (
        <div>
          {listado.map((vehiculo, indice) => (
            <TarjetaModelo key={vehiculo.id} vehiculo={vehiculo} indice={indice} />
          ))}
        </div>
      ) : (
        <div className="bg-negro px-5 py-32 text-center sm:px-8">
          <p className="display text-3xl text-ceniza">
            No hay modelos en esta familia
          </p>
          <Button className="mt-8" onClick={() => cambiarFiltro("todos")}>
            Ver todos los modelos
          </Button>
        </div>
      )}

      {/* --------------------------- CTA --------------------------- */}
      <section className="bg-negro px-5 py-24 sm:px-8 lg:py-32">
        <div className="mx-auto max-w-[1600px] text-center">
          <p className="etiqueta text-accion">Hazlo tuyo</p>
          <h2 className="display mx-auto mt-4 max-w-3xl text-4xl text-hueso sm:text-6xl">
            Configura tu unidad con nuestro equipo
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-ceniza">
            Pintura, llantas, frenos, tapicería y detalles en fibra vista. Un
            asesor te acompaña en cada decisión.
          </p>
          <div className="mt-10 flex flex-wrap justify-center gap-3">
            <Button to="/contacto" tamano="lg">
              Hablar con un asesor
              <Icono nombre="flecha" className="h-4 w-4" />
            </Button>
            <Button to="/login" variante="contorno" tamano="lg">
              Crear cuenta
            </Button>
          </div>
        </div>
      </section>
    </>
  );
}

export default Modelos;
