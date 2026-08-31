import { useState } from "react";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Icono from "../ui/Icono";
import { useFormulario } from "../../hooks/useFormulario";
import { LIMITES, sinEspacios, validarCorreo } from "../../utils/validaciones";
import { esperar } from "../../utils/clientes";

const VALORES_INICIALES = { correo: "" };
const REGLAS = { correo: validarCorreo };
const SANITIZADORES = { correo: sinEspacios };

/**
 * Componente independiente y reutilizable para recuperar la contraseña.
 * No depende del componente Login: recibe `alVolver` para regresar.
 */
function RecoverPassword({ alVolver, correoInicial = "" }) {
  const [correoEnviado, setCorreoEnviado] = useState("");

  const formulario = useFormulario({
    valoresIniciales: correoInicial
      ? { correo: correoInicial }
      : VALORES_INICIALES,
    reglas: REGLAS,
    sanitizadores: SANITIZADORES,
    alEnviar: async (valores) => {
      await esperar();
      setCorreoEnviado(valores.correo.trim().toLowerCase());
    },
  });

  const { propsCampo, manejarEnvio, enviando, estado } = formulario;

  if (estado === "exito") {
    return (
      <div className="text-center">
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center border border-exito/40 text-exito">
          <Icono nombre="correo" className="h-7 w-7" />
        </div>

        <h2 className="display text-3xl text-hueso">Revisa tu correo</h2>
        <p className="mt-3 text-sm leading-relaxed text-ceniza">
          Enviamos las instrucciones para restablecer tu contraseña a{" "}
          <span className="font-semibold text-hueso">{correoEnviado}</span>. El
          enlace es válido durante 30 minutos.
        </p>

        <Button variante="contorno" ancho className="mt-8" onClick={alVolver}>
          <Icono nombre="izquierda" className="h-4 w-4" />
          Volver al inicio de sesión
        </Button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <p className="etiqueta text-accion-claro">Recuperación</p>
        <h2 className="display mt-3 text-4xl text-hueso">
          Recuperar contraseña
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-ceniza">
          Escribe el correo con el que te registraste y te enviaremos un enlace
          para crear una contraseña nueva.
        </p>
      </div>

      <form onSubmit={manejarEnvio} noValidate className="space-y-6">
        <Input
          label="Correo electrónico"
          type="email"
          icono="correo"
          autoComplete="email"
          inputMode="email"
          placeholder="nombre@correo.com"
          maxLength={LIMITES.correo}
          {...propsCampo("correo")}
        />

        <Button type="submit" ancho tamano="lg" cargando={enviando}>
          {enviando ? "Enviando..." : "Recuperar contraseña"}
        </Button>

        <Button variante="texto" ancho onClick={alVolver} disabled={enviando}>
          <Icono nombre="izquierda" className="h-4 w-4" />
          Volver al inicio de sesión
        </Button>
      </form>
    </div>
  );
}

export default RecoverPassword;
