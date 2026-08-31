import { createContext, useCallback, useEffect, useMemo, useState } from "react";
import {
  authApi,
  borrarToken,
  guardarToken,
  obtenerToken,
} from "../api/cliente";

/**
 * Contexto de autenticacion.
 *
 * Guarda el usuario del JWT y lo comparte con toda la aplicacion: el Navbar lo
 * usa para mostrar el nombre, y los paneles para saber que rol tiene.
 */
const AuthContext = createContext(null);

function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [cargando, setCargando] = useState(() => Boolean(obtenerToken()));

  // Si hay token guardado, se pide el perfil al backend para reconstruir la
  // sesion tras recargar. Si el token caduco, se descarta.
  useEffect(() => {
    const token = obtenerToken();
    if (!token) return undefined;

    let vigente = true;

    authApi
      .perfil()
      .then((datos) => {
        if (vigente) setUsuario(datos.usuario);
      })
      .catch(() => {
        borrarToken();
        if (vigente) setUsuario(null);
      })
      .finally(() => {
        if (vigente) setCargando(false);
      });

    return () => {
      vigente = false;
    };
  }, []);

  const iniciarSesion = useCallback(async (correo, password, recordar) => {
    const datos = await authApi.login(correo, password);
    guardarToken(datos.token, recordar);
    setUsuario(datos.usuario);
    return datos.usuario;
  }, []);

  const registrar = useCallback(async (formulario) => {
    const datos = await authApi.registro(formulario);
    guardarToken(datos.token, false);
    setUsuario(datos.usuario);
    return datos.usuario;
  }, []);

  const cerrarSesion = useCallback(() => {
    borrarToken();
    setUsuario(null);
  }, []);

  const valor = useMemo(
    () => ({
      usuario,
      cargando,
      autenticado: Boolean(usuario),
      rol: usuario?.rol ?? null,
      esAdmin: usuario?.rol === "administrador",
      esEmpleado: usuario?.rol === "empleado",
      esCliente: usuario?.rol === "cliente",
      iniciarSesion,
      registrar,
      cerrarSesion,
    }),
    [usuario, cargando, iniciarSesion, registrar, cerrarSesion]
  );

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

export { AuthContext, AuthProvider };
