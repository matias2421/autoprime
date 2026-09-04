import { useState } from "react";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Icono from "../ui/Icono";
import { useFormulario } from "../../hooks/useFormulario";
import { LIMITES, sinEspacios, validarCorreo } from "../../utils/validaciones";
import { authApi } from "../../api/cliente";

const REGLAS = { correo: validarCorreo };
const SANITIZADORES = { correo: sinEspacios };

/**
 * Primer paso de la recuperación: pedir el enlace.
 *
 * Aquí termina lo que se puede hacer sin salir del sitio. La contraseña no se
 * cambia en esta pantalla a propósito: el enlace llega al correo de la cuenta
 * y se abre desde allí, en `/restablecer`. Ese rodeo es justamente lo que
 * demuestra que quien pide el cambio controla el buzón; sin él, bastaría con
 * saber una dirección ajena para dejar a alguien fuera de su cuenta.
 *
 * El backend contesta lo mismo exista o no la cuenta, así que esta pantalla
 * tampoco puede —ni debe— dar a entender si el correo estaba registrado.
 *
 * Componente independiente y reutilizable: no depende de Login, recibe
 * `alVolver` para regresar.
 */
function RecoverPassword({ alVolver, correoInicial = "" }) {
  const [enviado, setEnviado] = useState(false);
  const [correo, setCorreo] = useState("");
  const [minutos, setMinutos] = useState(30);
  const [errorGeneral, setErrorGeneral] = useState("");

  const { propsCampo, manejarEnvio, enviando, estado } = useFormulario({
    valoresIniciales: { correo: correoInicial },
    reglas: REGLAS,
    sanitizadores: SANITIZADORES,
    alEnviar: async (valores) => {
      setErrorGeneral("");
      const limpio = valores.correo.trim().toLowerCase();

      try {
        const aviso = await authApi.recuperar(limpio);
        setCorreo(limpio);
        setMinutos(aviso.expiraEnMinutos ?? 30);
        setEnviado(true);
      } catch (error) {
        setErrorGeneral(error.message);
        throw error;
      }
    },
  });

  /* ------------------------------------------------------------------ */
  /* Solicitud aceptada                                                  */
  /* ------------------------------------------------------------------ */
  if (enviado) {
    return (
      <div className="text-center">
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center border border-exito/40 text-exito">
          <Icono nombre="correo" className="h-7 w-7" />
        </div>

        <h2 className="display text-3xl text-hueso">Revisa tu correo</h2>
        <p className="mt-3 text-sm leading-relaxed text-ceniza">
          Si <span className="font-semibold text-hueso">{correo}</span>{" "}
          corresponde a una cuenta activa, allí encontrarás el enlace para crear
          una contraseña nueva. Caduca en {minutos} minutos y sirve una sola vez.
        </p>
        <p className="mt-4 text-xs leading-relaxed text-plomo">
          Si no aparece en unos minutos, mira en la carpeta de correo no
          deseado.
        </p>

        <Button variante="contorno" ancho className="mt-8" onClick={alVolver}>
          <Icono nombre="izquierda" className="h-4 w-4" />
          Volver al inicio de sesión
        </Button>
      </div>
    );
  }

  /* ------------------------------------------------------------------ */
  /* Formulario                                                          */
  /* ------------------------------------------------------------------ */
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

      <form
        onSubmit={manejarEnvio}
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
          {...propsCampo("correo")}
        />

        {estado === "error" && (
          <div
            role="alert"
            className="flex items-start gap-3 border border-accion/40 bg-accion/10 p-4
                       text-sm font-medium text-accion-claro"
          >
            <Icono nombre="alerta" className="mt-0.5 h-5 w-5 shrink-0" />
            {errorGeneral || "Revisa el correo antes de continuar."}
          </div>
        )}

        <Button type="submit" ancho tamano="lg" cargando={enviando}>
          {enviando ? "Enviando..." : "Enviar enlace"}
        </Button>

        <Button
          variante="texto"
          ancho
          onClick={alVolver}
          disabled={enviando}
        >
          <Icono nombre="izquierda" className="h-4 w-4" />
          Volver al inicio de sesión
        </Button>
      </form>
    </div>
  );
}

export default RecoverPassword;
