/**
 * Utilidades compartidas por los formularios.
 *
 * NOTA: en el segundo avance este archivo simulaba la base de datos con
 * localStorage. Desde el tercer avance los clientes se guardan de verdad en
 * MySQL a traves de la API (ver src/api/cliente.js y el contexto de sesion en
 * src/context/AuthContext.jsx), asi que aqui solo queda el retardo que usa el
 * formulario de contacto para mostrar su estado de "enviando".
 */

/** Simula la latencia de una peticion, para el formulario de contacto. */
export const esperar = (ms = 700) =>
  new Promise((resolver) => {
    window.setTimeout(resolver, ms);
  });
