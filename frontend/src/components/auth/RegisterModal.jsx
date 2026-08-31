import { useState } from "react";
import Button from "../ui/Button";
import Checkbox from "../ui/Checkbox";
import Icono from "../ui/Icono";
import Input from "../ui/Input";
import Modal from "../ui/Modal";
import Select from "../ui/Select";
import { useFormulario } from "../../hooks/useFormulario";
import {
  LIMITES,
  TIPOS_DOCUMENTO,
  nivelPassword,
  sinEspacios,
  soloAlfanumerico,
  soloDigitos,
  soloLetras,
  textoDireccion,
  validarApellido,
  validarConfirmacion,
  validarCorreo,
  validarDireccion,
  validarDocumento,
  validarNombre,
  validarPassword,
  validarTelefono,
  validarTipoDocumento,
} from "../../utils/validaciones";
import { useAuth } from "../../hooks/useAuth";

const VALORES_INICIALES = {
  nombre: "",
  apellido: "",
  tipoDocumento: "",
  numeroDocumento: "",
  direccion: "",
  telefono: "",
  correo: "",
  password: "",
  confirmarPassword: "",
  terminos: false,
};

const REGLAS = {
  nombre: validarNombre,
  apellido: validarApellido,
  tipoDocumento: validarTipoDocumento,
  numeroDocumento: validarDocumento,
  direccion: validarDireccion,
  telefono: validarTelefono,
  correo: validarCorreo,
  password: validarPassword,
  confirmarPassword: validarConfirmacion,
  terminos: (valor) =>
    valor ? "" : "Debes aceptar los términos para crear la cuenta.",
};

const SANITIZADORES = {
  nombre: soloLetras,
  apellido: soloLetras,
  numeroDocumento: soloAlfanumerico,
  direccion: textoDireccion,
  telefono: soloDigitos,
  correo: sinEspacios,
  password: sinEspacios,
  confirmarPassword: sinEspacios,
};

const ETIQUETAS_NIVEL = ["Muy débil", "Débil", "Aceptable", "Buena", "Excelente"];
const COLORES_NIVEL = [
  "bg-accion",
  "bg-accion",
  "bg-amber-500",
  "bg-emerald-500",
  "bg-exito",
];

/** Medidor visual de seguridad de la contraseña. */
function MedidorPassword({ valor }) {
  if (!valor) return null;
  const nivel = nivelPassword(valor);

  return (
    <div className="mt-3">
      <div className="flex gap-1.5" aria-hidden="true">
        {[0, 1, 2, 3].map((indice) => (
          <span
            key={indice}
            className={`h-1 flex-1 transition-colors duration-200 ${
              indice < nivel ? COLORES_NIVEL[nivel] : "bg-linea"
            }`}
          />
        ))}
      </div>
      <p className="mt-2 font-sans text-xs uppercase tracking-[0.14em] text-plomo">
        Seguridad: <span className="text-ceniza">{ETIQUETAS_NIVEL[nivel]}</span>
      </p>
    </div>
  );
}

/**
 * Formulario de registro de clientes dentro de una ventana Modal.
 * Se abre desde el inicio de sesión y puede cerrarse sin completar el registro.
 */
function RegisterModal({ abierto, alCerrar, alRegistrar }) {
  const [errorGeneral, setErrorGeneral] = useState("");
  const [erroresServidor, setErroresServidor] = useState({});
  const [cliente, setCliente] = useState(null);

  const { registrar } = useAuth();

  const formulario = useFormulario({
    valoresIniciales: VALORES_INICIALES,
    reglas: REGLAS,
    sanitizadores: SANITIZADORES,
    alEnviar: async (valores) => {
      setErrorGeneral("");
      setErroresServidor({});
      try {
        // Los datos viajan al backend, que vuelve a validarlos, hashea la
        // contrasena con bcrypt y los guarda en MySQL.
        setCliente(await registrar(valores));
      } catch (error) {
        setErrorGeneral(error.message);
        // El backend puede senalar campos concretos (correo o documento ya
        // registrados); se muestran junto al campo correspondiente.
        setErroresServidor(error.errores || {});
        throw error;
      }
    },
  });

  const { propsCampo, manejarEnvio, enviando, estado, valores, reiniciar } =
    formulario;

  /** Combina la validacion local con la que devolvio el servidor. */
  const campo = (nombre) => {
    const props = propsCampo(nombre);
    return { ...props, error: props.error || erroresServidor[nombre] || "" };
  };

  const cerrarYReiniciar = () => {
    alCerrar();
    // Deja el formulario limpio para la próxima apertura.
    window.setTimeout(() => {
      reiniciar();
      setCliente(null);
      setErrorGeneral("");
      setErroresServidor({});
    }, 200);
  };

  const registroExitoso = estado === "exito" && cliente;

  return (
    <Modal
      abierto={abierto}
      alCerrar={cerrarYReiniciar}
      titulo={registroExitoso ? "Registro confirmado" : "Crear una cuenta"}
      descripcion={
        registroExitoso
          ? undefined
          : "Completa tus datos para acceder a tu perfil de cliente."
      }
      ancho="max-w-3xl"
    >
      {registroExitoso ? (
        <div className="text-center">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center border border-exito/40 text-exito">
            <Icono nombre="check" className="h-8 w-8" />
          </div>

          <p className="text-lg text-hueso">
            Bienvenido a AutoPrime,{" "}
            <span className="font-bold">
              {cliente.nombre} {cliente.apellido}
            </span>
            .
          </p>
          <p className="mt-3 text-sm leading-relaxed text-ceniza">
            Tu cuenta quedó registrada con el correo{" "}
            <span className="font-semibold text-hueso">{cliente.correo}</span>.
            Ya puedes iniciar sesión para agendar pruebas de manejo y guardar
            tus modelos favoritos.
          </p>

          <dl className="mt-8 grid gap-5 border border-linea p-6 text-left sm:grid-cols-2">
            {[
              ["Documento", `${cliente.tipoDocumento} ${cliente.numeroDocumento}`],
              ["Teléfono", cliente.telefono],
              ["Dirección", cliente.direccion],
              ["Correo", cliente.correo],
            ].map(([titulo, dato]) => (
              <div key={titulo}>
                <dt className="etiqueta text-plomo">{titulo}</dt>
                <dd className="mt-1 break-words text-sm text-hueso">{dato}</dd>
              </div>
            ))}
          </dl>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row-reverse">
            <Button
              ancho
              tamano="lg"
              onClick={() => {
                alRegistrar?.(cliente);
                cerrarYReiniciar();
              }}
            >
              Ir a iniciar sesión
              <Icono nombre="flecha" className="h-4 w-4" />
            </Button>
            <Button variante="contorno" ancho tamano="lg" onClick={cerrarYReiniciar}>
              Cerrar
            </Button>
          </div>
        </div>
      ) : (
        <form onSubmit={manejarEnvio} noValidate className="space-y-6">
          <div className="grid gap-6 sm:grid-cols-2">
            <Input
              label="Nombre"
              icono="usuario"
              autoComplete="given-name"
              placeholder="Jose Matías"
              maxLength={LIMITES.nombre}
              {...campo("nombre")}
            />
            <Input
              label="Apellido"
              icono="usuario"
              autoComplete="family-name"
              placeholder="Agudelo Bolívar"
              maxLength={LIMITES.apellido}
              {...campo("apellido")}
            />
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            <Select
              label="Tipo de documento"
              opciones={TIPOS_DOCUMENTO}
              {...campo("tipoDocumento")}
            />
            <Input
              label="Número de documento"
              icono="documento"
              inputMode={valores.tipoDocumento === "PA" ? "text" : "numeric"}
              placeholder={
                valores.tipoDocumento === "PA" ? "AB123456" : "1012345678"
              }
              maxLength={LIMITES.documento}
              ayuda={
                valores.tipoDocumento === "PA"
                  ? "Entre 6 y 15 caracteres alfanuméricos."
                  : "Solo números, entre 6 y 11 dígitos."
              }
              {...campo("numeroDocumento")}
            />
          </div>

          <Input
            label="Dirección"
            icono="ubicacion"
            autoComplete="street-address"
            placeholder="Calle 45 # 12-30, Barrio Centro"
            maxLength={LIMITES.direccion}
            mostrarContador
            {...campo("direccion")}
          />

          <div className="grid gap-6 sm:grid-cols-2">
            <Input
              label="Teléfono"
              icono="telefono"
              type="tel"
              inputMode="numeric"
              autoComplete="tel"
              placeholder="3001234567"
              maxLength={LIMITES.telefono}
              ayuda="Celular colombiano de 10 dígitos."
              {...campo("telefono")}
            />
            <Input
              label="Correo electrónico"
              icono="correo"
              type="email"
              inputMode="email"
              autoComplete="email"
              placeholder="nombre@correo.com"
              maxLength={LIMITES.correo}
              {...campo("correo")}
            />
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <Input
                label="Contraseña"
                type="password"
                autoComplete="new-password"
                placeholder="Mínimo 8 caracteres"
                maxLength={LIMITES.password}
                {...campo("password")}
              />
              <MedidorPassword valor={valores.password} />
            </div>
            <Input
              label="Confirmar contraseña"
              type="password"
              autoComplete="new-password"
              placeholder="Repite la contraseña"
              maxLength={LIMITES.password}
              {...campo("confirmarPassword")}
            />
          </div>

          <div>
            <Checkbox
              name="terminos"
              label="Acepto los términos y el tratamiento de mis datos personales."
              checked={valores.terminos}
              onChange={formulario.manejarCambio}
              onBlur={formulario.manejarBlur}
            />
            {propsCampo("terminos").error && (
              <p
                role="alert"
                className="mt-2 flex items-start gap-2 text-sm font-medium text-accion-claro"
              >
                <Icono nombre="alerta" className="mt-0.5 h-4 w-4 shrink-0" />
                {propsCampo("terminos").error}
              </p>
            )}
          </div>

          {estado === "error" && (
            <div
              role="alert"
              className="flex items-start gap-3 border border-accion/40 bg-accion/10 p-4
                         text-sm font-medium text-accion-claro"
            >
              <Icono nombre="alerta" className="mt-0.5 h-5 w-5 shrink-0" />
              {errorGeneral ||
                "Revisa los campos marcados en rojo antes de continuar."}
            </div>
          )}

          <div className="flex flex-col gap-3 border-t border-linea pt-6 sm:flex-row-reverse">
            <Button type="submit" ancho tamano="lg" cargando={enviando}>
              {enviando ? "Creando cuenta..." : "Crear cuenta"}
            </Button>
            <Button
              variante="contorno"
              ancho
              tamano="lg"
              onClick={cerrarYReiniciar}
              disabled={enviando}
            >
              Cancelar
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}

export default RegisterModal;
