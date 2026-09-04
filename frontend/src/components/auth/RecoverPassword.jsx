import { useState } from "react";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Icono from "../ui/Icono";
import { useFormulario } from "../../hooks/useFormulario";
import {
  LIMITES,
  sinEspacios,
  validarConfirmacion,
  validarCorreo,
  validarPassword,
} from "../../utils/validaciones";
import { authApi } from "../../api/cliente";

const REGLAS_CORREO = { correo: validarCorreo };
const SANITIZADORES_CORREO = { correo: sinEspacios };

const VALORES_CLAVE = { password: "", confirmarPassword: "" };
const REGLAS_CLAVE = {
  password: validarPassword,
  confirmarPassword: validarConfirmacion,
};
const SANITIZADORES_CLAVE = {
  password: sinEspacios,
  confirmarPassword: sinEspacios,
};

/**
 * Recuperación de la contraseña olvidada.
 *
 * Son dos pasos contra la API y no uno: `POST /api/auth/recuperar` comprueba
 * quién pide el cambio y emite un permiso temporal, y `POST
 * /api/auth/restablecer` lo canjea por la contraseña nueva. Separarlos es lo
 * que evita que baste con saber un correo para cambiarle la clave a alguien.
 *
 * El backend responde igual exista o no la cuenta, así que este componente
 * tampoco puede —ni debe— decir si el correo estaba registrado.
 *
 * Componente independiente y reutilizable: no depende de Login, recibe
 * `alVolver` para regresar.
 */
function RecoverPassword({ alVolver, correoInicial = "" }) {
  // correo -> clave -> listo   |   correo -> avisoCorreo (cuando hay email)
  const [paso, setPaso] = useState("correo");
  const [correo, setCorreo] = useState("");
  const [token, setToken] = useState("");
  const [minutos, setMinutos] = useState(30);
  const [errorGeneral, setErrorGeneral] = useState("");

  /* ------------------------------------------------------------------ */
  /* Paso 1: pedir el enlace                                             */
  /* ------------------------------------------------------------------ */
  const formCorreo = useFormulario({
    valoresIniciales: { correo: correoInicial },
    reglas: REGLAS_CORREO,
    sanitizadores: SANITIZADORES_CORREO,
    alEnviar: async (valores) => {
      setErrorGeneral("");
      const limpio = valores.correo.trim().toLowerCase();

      try {
        const aviso = await authApi.recuperar(limpio);
        setCorreo(limpio);
        setMinutos(aviso.expiraEnMinutos ?? 30);

        /*
         * La API solo devuelve el token en desarrollo, porque el proyecto no
         * tiene servidor de correo. En producción llegaría por email y quien
         * lo recibiera volvería con el enlace; por eso aquí se distingue:
         * con token se continúa, sin él solo se avisa.
         */
        if (aviso.token) {
          setToken(aviso.token);
          setPaso("clave");
        } else {
          setPaso("avisoCorreo");
        }
      } catch (error) {
        setErrorGeneral(error.message);
        throw error;
      }
    },
  });

  /* ------------------------------------------------------------------ */
  /* Paso 2: escribir la contraseña nueva                                */
  /* ------------------------------------------------------------------ */
  const formClave = useFormulario({
    valoresIniciales: VALORES_CLAVE,
    reglas: REGLAS_CLAVE,
    sanitizadores: SANITIZADORES_CLAVE,
    alEnviar: async (valores) => {
      setErrorGeneral("");
      try {
        await authApi.restablecer({
          token,
          password: valores.password,
          confirmarPassword: valores.confirmarPassword,
        });
        setPaso("listo");
      } catch (error) {
        setErrorGeneral(error.message);
        throw error;
      }
    },
  });

  const avisoError = (formulario) =>
    formulario.estado === "error" && (
      <div
        role="alert"
        className="flex items-start gap-3 border border-accion/40 bg-accion/10 p-4
                   text-sm font-medium text-accion-claro"
      >
        <Icono nombre="alerta" className="mt-0.5 h-5 w-5 shrink-0" />
        {errorGeneral || "Revisa los datos antes de continuar."}
      </div>
    );

  /* ------------------------------------------------------------------ */
  /* Contraseña cambiada                                                 */
  /* ------------------------------------------------------------------ */
  if (paso === "listo") {
    return (
      <div className="text-center">
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center border border-exito/40 text-exito">
          <Icono nombre="check" className="h-7 w-7" />
        </div>

        <h2 className="display text-3xl text-hueso">Contraseña actualizada</h2>
        <p className="mt-3 text-sm leading-relaxed text-ceniza">
          Ya puedes entrar con tu contraseña nueva. El enlace que usaste quedó
          anulado.
        </p>

        <Button variante="primario" ancho className="mt-8" onClick={alVolver}>
          Iniciar sesión
        </Button>
      </div>
    );
  }

  /* ------------------------------------------------------------------ */
  /* Con servidor de correo el flujo termina aquí hasta abrir el enlace  */
  /* ------------------------------------------------------------------ */
  if (paso === "avisoCorreo") {
    return (
      <div className="text-center">
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center border border-exito/40 text-exito">
          <Icono nombre="correo" className="h-7 w-7" />
        </div>

        <h2 className="display text-3xl text-hueso">Revisa tu correo</h2>
        <p className="mt-3 text-sm leading-relaxed text-ceniza">
          Si <span className="font-semibold text-hueso">{correo}</span>{" "}
          corresponde a una cuenta activa, allí están las instrucciones para
          restablecer la contraseña. El enlace es válido durante {minutos}{" "}
          minutos.
        </p>

        <Button variante="contorno" ancho className="mt-8" onClick={alVolver}>
          <Icono nombre="izquierda" className="h-4 w-4" />
          Volver al inicio de sesión
        </Button>
      </div>
    );
  }

  /* ------------------------------------------------------------------ */
  /* Paso 2 en pantalla                                                  */
  /* ------------------------------------------------------------------ */
  if (paso === "clave") {
    return (
      <div>
        <div className="mb-8">
          <p className="etiqueta text-accion-claro">Recuperación</p>
          <h2 className="display mt-3 text-4xl text-hueso">Nueva contraseña</h2>
          <p className="mt-3 text-sm leading-relaxed text-ceniza">
            Estás cambiando la contraseña de{" "}
            <span className="font-semibold text-hueso">{correo}</span>. El
            enlace caduca en {minutos} minutos y sirve una sola vez.
          </p>
        </div>

        <form
          onSubmit={formClave.manejarEnvio}
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
            {...formClave.propsCampo("password")}
          />

          <Input
            label="Repite la contraseña"
            type="password"
            icono="candado"
            autoComplete="new-password"
            placeholder="La misma de arriba"
            maxLength={LIMITES.password}
            {...formClave.propsCampo("confirmarPassword")}
          />

          {avisoError(formClave)}

          <Button type="submit" ancho tamano="lg" cargando={formClave.enviando}>
            {formClave.enviando ? "Guardando..." : "Cambiar contraseña"}
          </Button>

          <Button
            variante="texto"
            ancho
            onClick={alVolver}
            disabled={formClave.enviando}
          >
            <Icono nombre="izquierda" className="h-4 w-4" />
            Volver al inicio de sesión
          </Button>
        </form>
      </div>
    );
  }

  /* ------------------------------------------------------------------ */
  /* Paso 1 en pantalla                                                  */
  /* ------------------------------------------------------------------ */
  return (
    <div>
      <div className="mb-8">
        <p className="etiqueta text-accion-claro">Recuperación</p>
        <h2 className="display mt-3 text-4xl text-hueso">
          Recuperar contraseña
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-ceniza">
          Escribe el correo con el que te registraste y te daremos un enlace
          temporal para crear una contraseña nueva.
        </p>
      </div>

      <form
        onSubmit={formCorreo.manejarEnvio}
        noValidate
        className="cristal reflejo space-y-6 p-6 sm:p-8"
      >
        <Input
          label="Correo electrónico"
          type="email"
          icono="correo"
          autoComplete="email"
          inputMode="email"
          placeholder="nombre@correo.com"
          maxLength={LIMITES.correo}
          {...formCorreo.propsCampo("correo")}
        />

        {avisoError(formCorreo)}

        <Button type="submit" ancho tamano="lg" cargando={formCorreo.enviando}>
          {formCorreo.enviando ? "Comprobando..." : "Recuperar contraseña"}
        </Button>

        <Button
          variante="texto"
          ancho
          onClick={alVolver}
          disabled={formCorreo.enviando}
        >
          <Icono nombre="izquierda" className="h-4 w-4" />
          Volver al inicio de sesión
        </Button>
      </form>
    </div>
  );
}

export default RecoverPassword;
