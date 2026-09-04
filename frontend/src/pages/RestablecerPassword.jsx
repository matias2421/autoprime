import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Icono from "../components/ui/Icono";
import { useFormulario } from "../hooks/useFormulario";
import {
  LIMITES,
  sinEspacios,
  validarConfirmacion,
  validarPassword,
} from "../utils/validaciones";
import { authApi } from "../api/cliente";

const VALORES_INICIALES = { password: "", confirmarPassword: "" };
const REGLAS = {
  password: validarPassword,
  confirmarPassword: validarConfirmacion,
};
const SANITIZADORES = {
  password: sinEspacios,
  confirmarPassword: sinEspacios,
};

/**
 * Segundo paso de la recuperación: la página que abre el enlace del correo.
 *
 * Es una ruta propia y no un estado más del formulario de acceso porque se
 * llega a ella desde fuera del sitio, pulsando en el correo. El token viaja en
 * la dirección —es lo único que un enlace puede transportar— y por eso mismo
 * vive treinta minutos y sirve una sola vez.
 *
 * Aquí no se comprueba si el token es válido antes de enseñar el formulario:
 * eso solo lo sabe el backend, y preguntárselo de antemano daría una forma de
 * ir probando tokens. Se envía y se muestra lo que conteste.
 */
function RestablecerPassword() {
  const [parametros] = useSearchParams();
  const navegar = useNavigate();
  const token = parametros.get("token") ?? "";

  const [listo, setListo] = useState(false);
  const [errorGeneral, setErrorGeneral] = useState("");

  const { propsCampo, manejarEnvio, enviando, estado } = useFormulario({
    valoresIniciales: VALORES_INICIALES,
    reglas: REGLAS,
    sanitizadores: SANITIZADORES,
    alEnviar: async (valores) => {
      setErrorGeneral("");
      try {
        await authApi.restablecer({
          token,
          password: valores.password,
          confirmarPassword: valores.confirmarPassword,
        });
        setListo(true);
      } catch (error) {
        setErrorGeneral(error.message);
        throw error;
      }
    },
  });

  const marco = (contenido) => (
    <section className="flex min-h-screen items-center justify-center px-5 pb-16 pt-28 sm:px-12">
      <div className="w-full max-w-lg">{contenido}</div>
    </section>
  );

  /* -------------------------------------------------------------------- */
  /* Enlace incompleto: se llegó aquí sin token                            */
  /* -------------------------------------------------------------------- */
  if (!token) {
    return marco(
      <div className="cristal reflejo p-8 text-center sm:p-10">
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center border border-accion/40 text-accion">
          <Icono nombre="alerta" className="h-7 w-7" />
        </div>

        <h1 className="display text-3xl text-hueso">Enlace incompleto</h1>
        <p className="mt-3 text-sm leading-relaxed text-ceniza">
          Esta dirección no trae el código de recuperación. Ábrela desde el
          enlace del correo, o pide uno nuevo desde el inicio de sesión.
        </p>

        <Button variante="contorno" ancho className="mt-8" to="/login">
          <Icono nombre="izquierda" className="h-4 w-4" />
          Ir al inicio de sesión
        </Button>
      </div>
    );
  }

  /* -------------------------------------------------------------------- */
  /* Contraseña cambiada                                                   */
  /* -------------------------------------------------------------------- */
  if (listo) {
    return marco(
      <div className="cristal reflejo p-8 text-center sm:p-10">
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center border border-exito/40 text-exito">
          <Icono nombre="check" className="h-7 w-7" />
        </div>

        <h1 className="display text-3xl text-hueso">Contraseña actualizada</h1>
        <p className="mt-3 text-sm leading-relaxed text-ceniza">
          Ya puedes entrar con tu contraseña nueva. El enlace que acabas de usar
          quedó anulado.
        </p>

        <Button
          variante="primario"
          ancho
          className="mt-8"
          onClick={() => navegar("/login", { replace: true })}
        >
          Iniciar sesión
        </Button>
      </div>
    );
  }

  /* -------------------------------------------------------------------- */
  /* Formulario                                                            */
  /* -------------------------------------------------------------------- */
  return marco(
    <div>
      <div className="mb-8">
        <p className="etiqueta text-accion-claro">Recuperación</p>
        <h1 className="display mt-3 text-4xl text-hueso">Nueva contraseña</h1>
        <p className="mt-3 text-sm leading-relaxed text-ceniza">
          Escribe la contraseña con la que quieres entrar a partir de ahora. El
          enlace del correo sirve una sola vez.
        </p>
      </div>

      <form
        onSubmit={manejarEnvio}
        noValidate
        className="cristal reflejo space-y-6 p-6 sm:p-8"
      >
        <Input
          label="Contraseña nueva"
          type="password"
          icono="candado"
          autoComplete="new-password"
          placeholder="Mínimo 8 caracteres"
          maxLength={LIMITES.password}
          {...propsCampo("password")}
        />

        <Input
          label="Repite la contraseña"
          type="password"
          icono="candado"
          autoComplete="new-password"
          placeholder="La misma de arriba"
          maxLength={LIMITES.password}
          {...propsCampo("confirmarPassword")}
        />

        {estado === "error" && (
          <div
            role="alert"
            className="flex items-start gap-3 border border-accion/40 bg-accion/10 p-4
                       text-sm font-medium text-accion-claro"
          >
            <Icono nombre="alerta" className="mt-0.5 h-5 w-5 shrink-0" />
            {errorGeneral || "Revisa los datos antes de continuar."}
          </div>
        )}

        <Button type="submit" ancho tamano="lg" cargando={enviando}>
          {enviando ? "Guardando..." : "Cambiar contraseña"}
        </Button>

        <Link
          to="/login"
          className="flex items-center justify-center gap-2 py-2 font-sans text-sm
                     text-plomo transition-colors hover:text-hueso"
        >
          <Icono nombre="izquierda" className="h-4 w-4" />
          Volver al inicio de sesión
        </Link>
      </form>
    </div>
  );
}

export default RestablecerPassword;
