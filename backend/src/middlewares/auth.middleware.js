const jwt = require("jsonwebtoken");
const usuarioModel = require("../models/usuario.model");

/**
 * Middlewares de seguridad.
 *
 * `verificarToken` protege los endpoints que exigen sesion.
 * `permitirRoles`  restringe un endpoint a ciertos roles.
 *
 * El token se lee de la cabecera `Authorization: Bearer <token>`.
 */

function firmarToken(usuario) {
  return jwt.sign(
    {
      id: usuario.id,
      correo: usuario.correo,
      rol: usuario.rol,
      rolId: usuario.rolId,
    },
    process.env.JWT_SECRET,
    { expiresIn: process.env.JWT_EXPIRA || "8h" }
  );
}

async function verificarToken(req, res, next) {
  const cabecera = req.headers.authorization || "";

  if (!cabecera.startsWith("Bearer ")) {
    return res.status(401).json({
      ok: false,
      mensaje: "Falta el token de autenticacion.",
    });
  }

  const token = cabecera.slice(7).trim();

  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET);

    // Se relee el usuario: si lo inactivaron o borraron, el token deja de servir
    // aunque todavia no haya expirado.
    const usuario = await usuarioModel.buscarPorId(payload.id);

    if (!usuario) {
      return res.status(401).json({ ok: false, mensaje: "El usuario ya no existe." });
    }
    if (usuario.estado !== "activo") {
      return res.status(403).json({ ok: false, mensaje: "Tu cuenta esta inactiva." });
    }

    req.usuario = usuario;
    return next();
  } catch (error) {
    const expirado = error.name === "TokenExpiredError";
    return res.status(401).json({
      ok: false,
      mensaje: expirado
        ? "La sesion expiro. Inicia sesion de nuevo."
        : "Token invalido.",
    });
  }
}

/** Uso: router.get("/", verificarToken, permitirRoles("administrador"), handler) */
function permitirRoles(...roles) {
  return (req, res, next) => {
    if (!req.usuario) {
      return res.status(401).json({ ok: false, mensaje: "No autenticado." });
    }
    if (!roles.includes(req.usuario.rol)) {
      return res.status(403).json({
        ok: false,
        mensaje: "No tienes permisos para esta accion.",
      });
    }
    return next();
  };
}

module.exports = { firmarToken, verificarToken, permitirRoles };
