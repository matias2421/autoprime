import { useCallback, useMemo, useState } from "react";

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

  const manejarEnvio = useCallback(
    async (evento) => {
      evento?.preventDefault();
      marcarTodosTocados();

      // Nunca se procesa la información sin validarla antes.
      if (Object.keys(calcularErrores(valores)).length > 0) {
        setEstado("error");
        return false;
      }

      setEnviando(true);
      try {
        await alEnviar?.(valores);
        setEstado("exito");
        return true;
      } catch {
        setEstado("error");
        return false;
      } finally {
        setEnviando(false);
      }
    },
    [alEnviar, calcularErrores, marcarTodosTocados, valores]
  );

  const reiniciar = useCallback(() => {
    setValores(valoresIniciales);
    setTocados({});
    setEstado(null);
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
