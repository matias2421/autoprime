const bcrypt = require("bcrypt");
const usuarioModel = require("../models/usuario.model");
const {
  validarRegistro,
  validarActualizacionUsuario,
  ESTADOS_USUARIO,
} = require("../utils/validaciones");

const RONDAS = Number(process.env.BCRYPT_ROUNDS) || 10;

/** GET /api/usuarios  — admin y empleado */
async function listar(req, res, next) {
  try {
    const usuarios = await usuarioModel.listar({
      rol: req.query.rol,
      estado: req.query.estado,
      buscar: req.query.buscar,
    });
    return res.json({ ok: true, total: usuarios.length, usuarios });
  } catch (error) {
    return next(error);
  }
}

/** GET /api/usuarios/:id */
async function obtener(req, res, next) {
  try {
    const usuario = await usuarioModel.buscarPorId(req.params.id);
    if (!usuario) {
      return res.status(404).json({ ok: false, mensaje: "Usuario no encontrado." });
    }
    return res.json({ ok: true, usuario });
  } catch (error) {
    return next(error);
  }
}

/** POST /api/usuarios — el admin puede crear con cualquier rol */
async function crear(req, res, next) {
  try {
    const { errores, datos } = validarRegistro(req.body);

    if (Object.keys(errores).length > 0) {
      return res.status(400).json({ ok: false, mensaje: "Revisa los datos.", errores });
    }

    if (await usuarioModel.existeCorreo(datos.correo)) {
      return res.status(409).json({
        ok: false,
        mensaje: "El correo ya esta registrado.",
        errores: { correo: "Este correo ya esta registrado." },
      });
    }

    if (await usuarioModel.existeDocumento(datos.tipoDocumento, datos.numeroDocumento)) {
      return res.status(409).json({
        ok: false,
        mensaje: "El documento ya esta registrado.",
        errores: { numeroDocumento: "Este documento ya esta registrado." },
      });
    }

    let rolId = await usuarioModel.idDeRol("cliente");
    if (req.body.rol) {
      const solicitado = await usuarioModel.idDeRol(req.body.rol);
      if (!solicitado) {
        return res.status(400).json({ ok: false, mensaje: "El rol indicado no existe." });
      }
      rolId = solicitado;
    }

    const passwordHash = await bcrypt.hash(datos.password, RONDAS);
    const usuario = await usuarioModel.crear(datos, passwordHash, rolId);

    return res.status(201).json({ ok: true, mensaje: "Usuario creado.", usuario });
  } catch (error) {
    return next(error);
  }
}

/** PUT /api/usuarios/:id */
async function actualizar(req, res, next) {
  try {
    const existente = await usuarioModel.buscarPorId(req.params.id);
    if (!existente) {
      return res.status(404).json({ ok: false, mensaje: "Usuario no encontrado." });
    }

    const { errores, datos } = validarActualizacionUsuario(req.body);
    if (Object.keys(errores).length > 0) {
      return res.status(400).json({ ok: false, mensaje: "Revisa los datos.", errores });
    }

    if (datos.correo && (await usuarioModel.existeCorreo(datos.correo, existente.id))) {
      return res.status(409).json({
        ok: false,
        mensaje: "El correo ya esta en uso.",
        errores: { correo: "Este correo ya esta registrado." },
      });
    }

    if (datos.numero_documento &&
        (await usuarioModel.existeDocumento(
          datos.tipo_documento, datos.numero_documento, existente.id))) {
      return res.status(409).json({
        ok: false,
        mensaje: "El documento ya esta en uso.",
        errores: { numeroDocumento: "Este documento ya esta registrado." },
      });
    }

    const usuario = await usuarioModel.actualizar(existente.id, datos);
    return res.json({ ok: true, mensaje: "Usuario actualizado.", usuario });
  } catch (error) {
    return next(error);
  }
}

/**
 * PATCH /api/usuarios/:id/estado
 * Se prefiere inactivar antes que borrar, para conservar el historico.
 */
async function cambiarEstado(req, res, next) {
  try {
    const { estado } = req.body;

    if (!ESTADOS_USUARIO.includes(estado)) {
      return res.status(400).json({
        ok: false,
        mensaje: "El estado debe ser activo o inactivo.",
      });
    }

    const existente = await usuarioModel.buscarPorId(req.params.id);
    if (!existente) {
      return res.status(404).json({ ok: false, mensaje: "Usuario no encontrado." });
    }

    if (existente.id === req.usuario.id && estado === "inactivo") {
      return res.status(400).json({
        ok: false,
        mensaje: "No puedes inactivar tu propia cuenta.",
      });
    }

    const usuario = await usuarioModel.cambiarEstado(existente.id, estado);
    return res.json({ ok: true, mensaje: `Usuario ${estado}.`, usuario });
  } catch (error) {
    return next(error);
  }
}

/** DELETE /api/usuarios/:id */
async function eliminar(req, res, next) {
  try {
    const existente = await usuarioModel.buscarPorId(req.params.id);
    if (!existente) {
      return res.status(404).json({ ok: false, mensaje: "Usuario no encontrado." });
    }

    if (existente.id === req.usuario.id) {
      return res.status(400).json({
        ok: false,
        mensaje: "No puedes eliminar tu propia cuenta.",
      });
    }

    await usuarioModel.eliminar(existente.id);
    return res.json({ ok: true, mensaje: "Usuario eliminado." });
  } catch (error) {
    return next(error);
  }
}

module.exports = { listar, obtener, crear, actualizar, cambiarEstado, eliminar };
