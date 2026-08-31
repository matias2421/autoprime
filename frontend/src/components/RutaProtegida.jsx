import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

/**
 * Envuelve las rutas que exigen sesion y, opcionalmente, un rol concreto.
 *
 * - Sin sesion  -> manda al login y recuerda a donde queria ir.
 * - Rol erroneo -> manda al panel que si le corresponde.
 */
function RutaProtegida({ children, roles }) {
  const { autenticado, cargando, rol } = useAuth();
  const ubicacion = useLocation();

  // Mientras se reconstruye la sesion desde el token no se decide nada, para
  // no expulsar al usuario en cada recarga.
  if (cargando) {
    return (
      <div className="flex min-h-screen items-center justify-center px-5">
        <p className="etiqueta text-plomo">Verificando sesion...</p>
      </div>
    );
  }

  if (!autenticado) {
    return <Navigate to="/login" state={{ desde: ubicacion.pathname }} replace />;
  }

  if (roles && roles.length > 0 && !roles.includes(rol)) {
    const destino =
      rol === "administrador"
        ? "/panel/admin"
        : rol === "empleado"
          ? "/panel/empleado"
          : "/panel/cliente";
    return <Navigate to={destino} replace />;
  }

  return children;
}

export default RutaProtegida;
