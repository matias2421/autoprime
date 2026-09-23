import { useCallback, useMemo, useRef, useState } from "react";

/**
 * Hook reutilizable para manejar formularios con validación en tiempo real.
 *
 * - `reglas`: objeto { campo: (valor, todosLosValores) => "mensaje de error" | "" }
 * - `sanitizadores`: objeto { campo: (valor) => valorLimpio } para restringir
 *   los caracteres que el usuario puede escribir.
 *
 * La validación se ejecuta en cada pulsación de tecla, pero el error solo se
 * muestra cuando el campo ya fue tocado (escrito o desenfocado) o cuando se
 * intentó enviar el formulario: así se avisa a tiempo sin castigar al usuario
 * antes de que empiece a escribir.
 */
export function useFormulario({
  valoresIniciales,
  reglas,
  sanitizadores = {},
  alEnviar,
}) {
  const [valores, setValores] = useState(valoresIniciales);
  const [tocados, setTocados] = useState({});
  const [enviando, setEnviando] = useState(false);
  const [estado, setEstado] = useState(null); // null | "exito" | "error"

  // Qué campos impidieron el último envío. Hace falta guardarlo aparte de
  // `errores` porque el aviso tiene que poder NOMBRARLOS, y decir «revisa los
  // campos en rojo» no sirve cuando el que falla es una casilla, que no tiene
  // borde que ponerse rojo. Eso pasaba: todo en verde y un aviso señalando un
  // rojo que no existía en ninguna parte.
  const [fallos, setFallos] = useState([]);

  // Para llevar el foco al primer campo que falla en vez de dejar a la gente
  // buscándolo. En un formulario largo el aviso sale abajo, junto al botón, y
  // el campo malo puede estar fuera de la pantalla.
  const refFormulario = useRef(null);

  /** Ejecuta todas las reglas sobre el conjunto de valores actual. */
  const calcularErrores = useCallback(
    (datos) => {
      const resultado = {};
      Object.keys(reglas).forEach((campo) => {
        const mensaje = reglas[campo](datos[campo], datos);
        if (mensaje) resultado[campo] = mensaje;
      });
      return resultado;
    },
    [reglas]
  );

  // Se recalcula en cada render: esto es lo que hace la validación "en vivo".
  const errores = useMemo(
    () => calcularErrores(valores),
    [calcularErrores, valores]
  );

  const esValido = Object.keys(errores).length === 0;

  const manejarCambio = useCallback(
    (evento) => {
      const { name, value, type, checked } = evento.target;
      const bruto = type === "checkbox" ? checked : value;
      const limpio =
        typeof bruto === "string" && sanitizadores[name]
          ? sanitizadores[name](bruto)
          : bruto;

      setValores((previos) => ({ ...previos, [name]: limpio }));
      setTocados((previos) => ({ ...previos, [name]: true }));
      setEstado(null);
      setFallos([]);
    },
    [sanitizadores]
  );

  const manejarBlur = useCallback((evento) => {
    const { name } = evento.target;
    setTocados((previos) => ({ ...previos, [name]: true }));
  }, []);

  /** Props listas para pasar a <Input>, <Select> o <Checkbox>. */
  const propsCampo = useCallback(
    (nombre) => ({
      name: nombre,
      value: valores[nombre] ?? "",
      onChange: manejarCambio,
      onBlur: manejarBlur,
      error: tocados[nombre] ? errores[nombre] : "",
      valido: Boolean(tocados[nombre]) && !errores[nombre],
    }),
    [valores, errores, tocados, manejarCambio, manejarBlur]
  );

  const marcarTodosTocados = useCallback(() => {
    const todos = {};
    Object.keys(reglas).forEach((campo) => {
      todos[campo] = true;
    });
    setTocados(todos);
  }, [reglas]);

  /** Lleva el foco al campo indicado, dentro de este formulario. */
  const enfocar = useCallback((nombre) => {
    const campo = refFormulario.current?.querySelector(`[name="${nombre}"]`);
    if (!campo) return;
    campo.scrollIntoView({ block: "center", behavior: "smooth" });
    // El desplazamiento es suave, así que el foco se da después: hacerlo
    // antes provoca que el navegador salte de golpe y anule la animación.
    window.setTimeout(() => campo.focus({ preventScroll: true }), 180);
  }, []);

  const manejarEnvio = useCallback(
    async (evento) => {
      evento?.preventDefault();
      marcarTodosTocados();

      // Nunca se procesa la información sin validarla antes.
      const problemas = Object.keys(calcularErrores(valores));
      if (problemas.length > 0) {
        setFallos(problemas);
        setEstado("error");
        enfocar(problemas[0]);
        return false;
      }
      setFallos([]);

      setEnviando(true);
      try {
        await alEnviar?.(valores);
        setEstado("exito");
        return true;
      } catch {
        // Aquí el fallo viene del servidor, no de los campos: la lista se
        // deja vacía para que el aviso no invente un campo culpable.
        setFallos([]);
        setEstado("error");
        return false;
      } finally {
        setEnviando(false);
      }
    },
    [alEnviar, calcularErrores, enfocar, marcarTodosTocados, valores]
  );

  const reiniciar = useCallback(() => {
    setValores(valoresIniciales);
    setTocados({});
    setEstado(null);
    setFallos([]);
    setEnviando(false);
  }, [valoresIniciales]);

  const asignarValor = useCallback((nombre, valor) => {
    setValores((previos) => ({ ...previos, [nombre]: valor }));
  }, []);

  return {
    valores,
    errores,
    tocados,
    enviando,
    estado,
    fallos,
    refFormulario,
    esValido,
    propsCampo,
    manejarCambio,
    manejarBlur,
    manejarEnvio,
    reiniciar,
    asignarValor,
    setEstado,
  };
}
