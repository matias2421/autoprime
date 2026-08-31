import Login from "../components/auth/Login";
import Icono from "../components/ui/Icono";
import fondo from "../assets/images/seccion-login.webp";

const VENTAJAS = [
  {
    icono: "estrella",
    titulo: "Guarda tus favoritos",
    texto: "Compara modelos y recibe alertas cuando cambie el precio.",
  },
  {
    icono: "reloj",
    titulo: "Agenda pruebas de manejo",
    texto: "Elige el día y la hora sin llamadas ni filas.",
  },
  {
    icono: "tarjeta",
    titulo: "Simula tu financiación",
    texto: "Calcula la cuota mensual antes de venir al concesionario.",
  },
];

function IniciarSesion() {
  return (
    <section className="grid min-h-screen lg:grid-cols-2">
      {/* -------------------- Panel de presentación -------------------- */}
      <aside className="relative order-2 min-h-[60vh] overflow-hidden lg:order-1 lg:min-h-screen">
        <img
          src={fondo}
          alt="Zaga de un deportivo negro con alerón, iluminada a contraluz"
          width={1600}
          height={900}
          loading="lazy"
          decoding="async"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="velo absolute inset-0" />

        <div className="relative flex min-h-[60vh] flex-col justify-end p-8 sm:p-12 lg:min-h-screen lg:p-16">
          <p className="etiqueta text-accion-claro">Cuenta de cliente</p>
          <h2 className="display mt-4 text-4xl text-hueso sm:text-6xl">
            Una sola cuenta
            <br />
            <span className="text-ceniza">para todo el proceso</span>
          </h2>

          <ul className="mt-10 space-y-6 border-t border-hueso/20 pt-8">
            {VENTAJAS.map((ventaja) => (
              <li key={ventaja.titulo} className="flex gap-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center border border-accion/50 text-accion">
                  <Icono nombre={ventaja.icono} className="h-4 w-4" />
                </span>
                <div>
                  <h3 className="font-sans text-sm uppercase tracking-[0.14em] text-hueso">
                    {ventaja.titulo}
                  </h3>
                  <p className="mt-1 text-sm text-ceniza">{ventaja.texto}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </aside>

      {/* ------------------------ Módulo de login ---------------------- */}
      <div className="order-1 flex items-center justify-center px-5 pb-16 pt-28 sm:px-12 lg:order-2 lg:px-16 lg:py-28">
        <div className="w-full max-w-lg">
          <Login />
        </div>
      </div>
    </section>
  );
}

export default IniciarSesion;
