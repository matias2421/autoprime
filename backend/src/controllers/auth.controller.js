const bcrypt = require("bcrypt");
const usuarioModel = require("../models/usuario.model");
const { firmarToken } = require("../middlewares/auth.middleware");
const { validarRegistro, validarLogin } = require("../utils/validaciones");

const RONDAS = Number(process.env.BCRYPT_ROUNDS) || 10;

/**
 * POST /api/auth/registro
 *
 * Flujo: validar -> comprobar duplicados -> hashear -> guardar -> responder.
 * La contrasena original nunca se guarda ni se devuelve.
 */
async function registro(req, res, next) {
  try {
    const { errores, datos } = validarRegistro(req.body);

    if (Object.keys(errores).length > 0) {
      return res.status(400).json({
        ok: false,
        mensaje: "Revisa los datos enviados.",
        errores,
      });
    }

    if (await usuarioModel.existeCorreo(datos.correo)) {
      return res.status(409).json({
        ok: false,
        mensaje: "Ya existe una cuenta registrada con este correo.",
        errores: { correo: "Este correo ya esta registrado." },
      });
    }

    if (await usuarioModel.existeDocumento(datos.tipoDocumento, datos.numeroDocumento)) {
      return res.status(409).json({
        ok: false,
        mensaje: "Ya existe una cuenta con este documento.",
        errores: { numeroDocumento: "Este documento ya esta registrado." },
      });
    }

    // Hash seguro: bcrypt genera su propia sal en cada llamada.
    const passwordHash = await bcrypt.hash(datos.password, RONDAS);

    const rolCliente = await usuarioModel.idDeRol("cliente");
    const usuario = await usuarioModel.crear(datos, passwordHash, rolCliente);

    const token = firmarToken(usuario);

    return res.status(201).json({
      ok: true,
      mensaje: "Cuenta creada correctamente.",
      usuario,
      token,
    });
  } catch (error) {
    return next(error);
  }
}

/**
 * POST /api/auth/login
 * Valida credenciales y devuelve un JWT.
 */
async function login(req, res, next) {
  try {
    const { errores, datos } = validarLogin(req.body);

    if (Object.keys(errores).length > 0) {
      return res.status(400).json({
        ok: false,
        mensaje: "Revisa los datos enviados.",
        errores,
      });
    }

    const usuario = await usuarioModel.buscarPorCorreoConPassword(datos.correo);

    // Mismo mensaje para correo inexistente y contrasena errada: asi no se
    // revela si un correo esta o no registrado.
    const generico = "Correo o contrasena incorrectos.";

    if (!usuario) {
      return res.status(401).json({ ok: false, mensaje: generico });
    }

    const coincide = await bcrypt.compare(datos.password, usuario.passwordHash);
    if (!coincide) {
      return res.status(401).json({ ok: false, mensaje: generico });
    }

    if (usuario.estado !== "activo") {
      return res.status(403).json({
        ok: false,
        mensaje: "Tu cuenta esta inactiva. Comunicate con el concesionario.",
      });
    }

    delete usuario.passwordHash;
    const token = firmarToken(usuario);

    return res.json({
      ok: true,
      mensaje: `Bienvenido, ${usuario.nombre}.`,
      usuario,
      token,
    });
  } catch (error) {
    return next(error);
  }
}

/**
 * GET /api/auth/perfil  (protegido)
 * Devuelve el usuario del token, con sus permisos.
 */
async function perfil(req, res, next) {
  try {
    const permisos = await usuarioModel.permisosDeRol(req.usuario.rolId);
    return res.json({ ok: true, usuario: req.usuario, permisos });
  } catch (error) {
    return next(error);
  }
}

module.exports = { registro, login, perfil };
