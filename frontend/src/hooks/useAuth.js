import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";

/** Acceso al contexto de autenticacion desde cualquier componente. */
export function useAuth() {
  const contexto = useContext(AuthContext);

  if (!contexto) {
    throw new Error("useAuth debe usarse dentro de <AuthProvider>.");
  }
  return contexto;
}
