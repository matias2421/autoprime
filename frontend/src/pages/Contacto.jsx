import Button from "../components/ui/Button";
import Icono from "../components/ui/Icono";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import { useFormulario } from "../hooks/useFormulario";
import { esperar } from "../utils/clientes";
import {
  LIMITES,
  sinEspacios,
  soloDigitos,
  soloLetras,
  validarAsunto,
  validarCorreo,
  validarMensaje,
  validarNombre,
  validarTelefono,
} from "../utils/validaciones";

const ASUNTOS = [
  { valor: "compra", etiqueta: "Quiero comprar un vehículo" },
  { valor: "prueba", etiqueta: "Agendar una prueba de manejo" },
  { valor: "financiacion", etiqueta: "Información de financiación" },
  { valor: "taller", etiqueta: "Cita en el taller" },
  { valor: "otro", etiqueta: "Otro asunto" },
];

const VALORES_INICIALES = {
  nombre: "",
  correo: "",
  telefono: "",
  asunto: "",
  mensaje: "",
};

const REGLAS = {
  nombre: validarNombre,
  correo: validarCorreo,
  telefono: validarTelefono,
  asunto: validarAsunto,
  mensaje: validarMensaje,
};

const SANITIZADORES = {
  nombre: soloLetras,
  correo: sinEspacios,
  telefono: soloDigitos,
};

const DATOS_CONTACTO = [
  {
    icono: "ubicacion",
    titulo: "Sede principal",
    lineas: ["Av. Las Américas #45-12", "Pereira, Risaralda"],
  },
  {
    icono: "telefono",
    titulo: "Teléfonos",
    lineas: ["(606) 340 1290", "WhatsApp: 300 123 4567"],
  },
  {
    icono: "correo",
    titulo: "Correo",
    lineas: ["ventas@autoprime.com.co", "taller@autoprime.com.co"],
  },
  {
    icono: "reloj",
    titulo: "Horario",
    lineas: ["Lun a Vie: 8:00 a.m. – 6:00 p.m.", "Sáb: 9:00 a.m. – 2:00 p.m."],
  },
];

function Contacto() {
  const formulario = useFormulario({
    valoresIniciales: VALORES_INICIALES,
    reglas: REGLAS,
    sanitizadores: SANITIZADORES,
    alEnviar: async () => {
      await esperar();
    },
  });

  const { propsCampo, manejarEnvio, enviando, estado, valores, reiniciar } =
    formulario;

  return (
    <>
      <section className="border-b border-linea px-5 pb-12 pt-28 sm:px-8 lg:pt-32">
        <div className="mx-auto max-w-[1600px]">
          <p className="etiqueta text-accion-claro">Contacto</p>
          <h1 className="display mt-5 max-w-3xl text-5xl text-hueso sm:text-7xl lg:text-8xl">
            Hablemos de
            <br />
            <span className="text-ceniza">tu próximo vehículo</span>
          </h1>
          <p className="mt-6 max-w-xl leading-relaxed text-ceniza">
            Cuéntanos qué necesitas y un asesor te responde el mismo día hábil.
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-[1600px] px-5 py-16 sm:px-8 lg:py-24">
        <div className="grid gap-12 lg:grid-cols-[1.3fr_1fr] lg:gap-20">
          {/* ------------------------ Formulario ------------------------ */}
          <div>
            {estado === "exito" ? (
              <div className="cristal p-10 text-center lg:p-16">
                <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center border border-exito/40 text-exito">
                  <Icono nombre="check" className="h-8 w-8" />
                </div>
                <h2 className="display text-3xl text-hueso sm:text-4xl">
                  Mensaje enviado
                </h2>
                <p className="mx-auto mt-4 max-w-md text-sm leading-relaxed text-ceniza">
                  Gracias por escribirnos. Un asesor de AutoPrime te contactará
                  al correo{" "}
                  <span className="font-semibold text-hueso">
                    {valores.correo}
                  </span>{" "}
                  dentro del siguiente día hábil.
                </p>
                <Button variante="contorno" className="mt-8" onClick={reiniciar}>
                  Enviar otro mensaje
                </Button>
              </div>
            ) : (
              <>
                <h2 className="display text-3xl text-hueso sm:text-4xl">
                  Escríbenos
                </h2>
                <p className="mt-2 text-sm text-ceniza">
                  Todos los campos son obligatorios.
                </p>

                <form onSubmit={manejarEnvio} noValidate className="cristal reflejo mt-10 space-y-6 p-6 sm:p-8">
                  <Input
                    label="Nombre completo"
                    icono="usuario"
                    autoComplete="name"
                    placeholder="Jose Matías Agudelo"
                    maxLength={LIMITES.nombre}
                    {...propsCampo("nombre")}
                  />

                  <div className="grid gap-6 sm:grid-cols-2">
                    <Input
                      label="Correo electrónico"
                      type="email"
                      icono="correo"
                      inputMode="email"
                      autoComplete="email"
                      placeholder="nombre@correo.com"
                      maxLength={LIMITES.correo}
                      {...propsCampo("correo")}
                    />
                    <Input
                      label="Teléfono"
                      type="tel"
                      icono="telefono"
                      inputMode="numeric"
                      autoComplete="tel"
                      placeholder="3001234567"
                      maxLength={LIMITES.telefono}
                      ayuda="Celular de 10 dígitos."
                      {...propsCampo("telefono")}
                    />
                  </div>

                  <Select
                    label="Asunto"
                    opciones={ASUNTOS}
                    placeholder="¿En qué podemos ayudarte?"
                    {...propsCampo("asunto")}
                  />

                  <Input
                    label="Mensaje"
                    multilinea
                    filas={6}
                    placeholder="Cuéntanos qué modelo te interesa o qué necesitas resolver."
                    maxLength={LIMITES.mensaje}
                    mostrarContador
                    {...propsCampo("mensaje")}
                  />

                  {estado === "error" && (
                    <div
                      role="alert"
                      className="flex items-start gap-3 border border-accion/40 bg-accion/10
                                 p-4 text-sm font-medium text-accion-claro"
                    >
                      <Icono nombre="alerta" className="mt-0.5 h-5 w-5 shrink-0" />
                      Revisa los campos marcados en rojo antes de enviar.
                    </div>
                  )}

                  <Button type="submit" ancho tamano="lg" cargando={enviando}>
                    {enviando ? "Enviando..." : "Enviar mensaje"}
                  </Button>
                </form>
              </>
            )}
          </div>

          {/* ---------------------- Datos de contacto ------------------- */}
          <div>
            <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
              {DATOS_CONTACTO.map((dato) => (
                <li key={dato.titulo} className="cristal cristal-vivo reflejo alza flex gap-4 p-6">
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center border border-accion/40 text-accion">
                    <Icono nombre={dato.icono} className="h-5 w-5" />
                  </span>
                  <div>
                    <h2 className="etiqueta text-plomo">{dato.titulo}</h2>
                    {dato.lineas.map((linea) => (
                      <p key={linea} className="mt-1 text-sm text-ceniza">
                        {linea}
                      </p>
                    ))}
                  </div>
                </li>
              ))}
            </ul>

            <div className="cristal cristal-vivo reflejo alza mt-3 p-6">
              <h2 className="display text-2xl text-hueso">
                ¿Prefieres WhatsApp?
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-ceniza">
                Resolvemos dudas rápidas de lunes a sábado en horario de
                atención.
              </p>
              <Button
                variante="contorno"
                ancho
                className="mt-5"
                href="https://wa.me/573001234567"
                target="_blank"
                rel="noreferrer noopener"
              >
                <Icono nombre="whatsapp" className="h-4 w-4" />
                Escribir por WhatsApp
              </Button>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

export default Contacto;
