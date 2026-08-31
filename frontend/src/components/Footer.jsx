import { Link } from "react-router-dom";
import Icono from "./ui/Icono";
import RedesSociales from "./RedesSociales";

const COLUMNAS = [
  {
    titulo: "Modelos",
    enlaces: [
      { texto: "Gama completa", a: "/modelos?familia=gama" },
      { texto: "Edición limitada", a: "/modelos?familia=edicion" },
      { texto: "Colección", a: "/modelos?familia=coleccion" },
      { texto: "Ver todos", a: "/modelos" },
    ],
  },
  {
    titulo: "Concesionario",
    enlaces: [
      { texto: "Quiénes somos", a: "/quienes-somos" },
      { texto: "Contacto", a: "/contacto" },
      { texto: "Mi cuenta", a: "/login" },
    ],
  },
  {
    titulo: "Servicios",
    enlaces: [
      { texto: "Prueba de manejo", a: "/login" },
      { texto: "Financiación", a: "/contacto" },
      { texto: "Taller certificado", a: "/contacto" },
      { texto: "Garantía extendida", a: "/contacto" },
    ],
  },
];

const CONTACTO = [
  { icono: "ubicacion", texto: "Av. Las Américas #45-12, Pereira" },
  { icono: "telefono", texto: "(606) 340 1290" },
  { icono: "correo", texto: "ventas@autoprime.com.co" },
  { icono: "reloj", texto: "Lun a Sáb · 8:00 a.m. – 6:00 p.m." },
];

function Footer() {
  return (
    <footer className="mt-auto border-t border-linea bg-negro">
      <div className="mx-auto max-w-[1600px] px-5 py-16 sm:px-8 lg:py-20">
        <div className="grid gap-12 lg:grid-cols-[1.4fr_repeat(3,1fr)]">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center bg-accion-fondo">
                <Icono nombre="auto" className="h-4 w-4 text-negro" />
              </span>
              <span className="font-sans text-lg font-medium uppercase tracking-[0.3em] text-hueso">
                AutoPrime
              </span>
            </div>

            <p className="mt-5 max-w-sm text-sm leading-relaxed text-ceniza">
              Concesionario de altas prestaciones en el Eje Cafetero. Cada
              vehículo pasa por un peritaje de 120 puntos antes de entrar al
              catálogo.
            </p>

            <ul className="mt-8 space-y-3">
              {CONTACTO.map((item) => (
                <li key={item.texto} className="flex items-start gap-3 text-sm text-ceniza">
                  <span className="mt-0.5 shrink-0 text-accion">
                    <Icono nombre={item.icono} className="h-4 w-4" />
                  </span>
                  {item.texto}
                </li>
              ))}
            </ul>

            <h2 className="etiqueta mt-8 text-plomo">Síguenos</h2>
            <RedesSociales className="mt-4" titulo="AutoPrime" />
          </div>

          {COLUMNAS.map((columna) => (
            <nav key={columna.titulo} aria-label={columna.titulo}>
              <h2 className="etiqueta text-plomo">{columna.titulo}</h2>
              <ul className="mt-5 space-y-1">
                {columna.enlaces.map((enlace) => (
                  <li key={enlace.texto}>
                    <Link
                      to={enlace.a}
                      className="flex min-h-11 items-center text-sm text-ceniza
                                 transition-colors duration-200 hover:text-hueso"
                    >
                      {enlace.texto}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        <div className="mt-16 flex flex-col gap-3 border-t border-linea pt-8 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-sans text-xs uppercase tracking-[0.18em] text-plomo">
            © 2026 AutoPrime · Proyecto formativo SENA
          </p>
          <p className="font-sans text-xs uppercase tracking-[0.18em] text-plomo">
            Jose Matías Agudelo Bolívar · ADSO · Ficha 3406211
          </p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
