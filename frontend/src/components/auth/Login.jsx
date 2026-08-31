import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Button from "../ui/Button";
import Checkbox from "../ui/Checkbox";
import Icono from "../ui/Icono";
import Input from "../ui/Input";
import RecoverPassword from "./RecoverPassword";
import RegisterModal from "./RegisterModal";
import { useFormulario } from "../../hooks/useFormulario";
import { useAuth } from "../../hooks/useAuth";
import {
  LIMITES,
  sinEspacios,
  validarCorreo,
  validarPasswordLogin,
} from "../../utils/validaciones";

const VALORES_INICIALES = { correo: "", password: "", recordarme: false };

const REGLAS = {
  correo: validarCorreo,
  password: validarPasswordLogin,
};

const SANITIZADORES = {
  correo: sinEspacios,
  password: sinEspacios,
};

/** A donde va cada rol despues de iniciar sesion. */
const PANEL_POR_ROL = {
  administrador: "/panel/admin",
  empleado: "/panel/empleado",
  cliente: "/panel/cliente",
};

/**
 * Modulo de inicio de sesion.
 *
 * Desde el tercer avance las credenciales se validan contra el backend:
 * POST /api/auth/login devuelve un JWT que queda guardado por el contexto.
 */
function Login() {
  const [vista, setVista] = useState("login"); // "login" | "recuperar"
  const [modalAbierto, setModalAbierto] = useState(false);
  const [errorGeneral, setErrorGeneral] = useState("");

  const { iniciarSesion } = useAuth();
  const navegar = useNavigate();
  const ubicacion = useLocation();

  const formulario = useFormulario({
    valoresIniciales: VALORES_INICIALES,
    reglas: REGLAS,
    sanitizadores: SANITIZADORES,
    alEnviar: async (valores) => {
      setErrorGeneral("");
      try {
        const usuario = await iniciarSesion(
          valores.correo,
          valores.password,
          valores.recordarme
        );

        // Si llego aqui redirigido desde una ruta protegida, vuelve alli.
        const destino = ubicacion.state?.desde || PANEL_POR_ROL[usuario.rol] || "/";
        navegar(destino, { replace: true });
      } catch (error) {
        setErrorGeneral(error.message);
        throw error;
      }
    },
  });

  const {
    propsCampo,
    manejarEnvio,
    manejarCambio,
    manejarBlur,
    enviando,
    estado,
    valores,
    asignarValor,
  } = formulario;

  /* ------------------------------------------------------------------ */
  /* Recuperacion de contrasena                                          */
  /* ------------------------------------------------------------------ */
  if (vista === "recuperar") {
    return (
      <RecoverPassword
        correoInicial={valores.correo}
        alVolver={() => setVista("login")}
      />
    );
  }

  /* ------------------------------------------------------------------ */
  /* Formulario de inicio de sesion                                      */
  /* ------------------------------------------------------------------ */
  return (
    <div>
      <div className="mb-8">
        <p className="etiqueta text-accion-claro">Area de clientes</p>
        <h2 className="display mt-3 text-4xl text-hueso sm:text-5xl">
          Iniciar sesión
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-ceniza">
          Accede a tu perfil para agendar pruebas de manejo y guardar tus
          modelos favoritos.
        </p>
      </div>

      <form onSubmit={manejarEnvio} noValidate className="cristal reflejo space-y-6 p-6 sm:p-8">
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
          label="Contraseña"
          type="password"
          autoComplete="current-password"
          placeholder="Tu contraseña"
          maxLength={LIMITES.password}
          {...propsCampo("password")}
        />

        <div className="flex flex-wrap items-center justify-between gap-3">
          <Checkbox
            name="recordarme"
            label="No cerrar sesión"
            checked={valores.recordarme}
            onChange={manejarCambio}
            onBlur={manejarBlur}
          />

          <button
            type="button"
            onClick={() => setVista("recuperar")}
            className="min-h-11 cursor-pointer font-sans text-xs uppercase
                       tracking-[0.14em] text-accion-claro underline-offset-8
                       transition-colors duration-200 hover:text-hueso hover:underline"
          >
            ¿Olvidaste tu contraseña?
          </button>
        </div>

        {estado === "error" && (
          <div
            role="alert"
            className="flex items-start gap-3 border border-accion/40 bg-accion/10 p-4
                       text-sm font-medium text-accion-claro"
          >
            <Icono nombre="alerta" className="mt-0.5 h-5 w-5 shrink-0" />
            {errorGeneral ||
              "Revisa los datos ingresados antes de iniciar sesión."}
          </div>
        )}

        <Button type="submit" ancho tamano="lg" cargando={enviando}>
          {enviando ? "Verificando..." : "Iniciar sesión"}
        </Button>
      </form>

      <div className="my-8 flex items-center gap-4">
        <span className="h-px flex-1 bg-linea" />
        <span className="font-sans text-xs uppercase tracking-[0.14em] text-plomo">
          ¿Aún no tienes cuenta?
        </span>
        <span className="h-px flex-1 bg-linea" />
      </div>

      <Button
        variante="contorno"
        ancho
        tamano="lg"
        onClick={() => setModalAbierto(true)}
      >
        <Icono nombre="usuario" className="h-4 w-4" />
        Crear una cuenta
      </Button>

      <RegisterModal
        abierto={modalAbierto}
        alCerrar={() => setModalAbierto(false)}
        alRegistrar={(cliente) => {
          asignarValor("correo", cliente.correo);
          setErrorGeneral("");
        }}
      />
    </div>
  );
}

export default Login;
