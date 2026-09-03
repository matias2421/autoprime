const { Router } = require("express");
const ctrl = require("../controllers/cita.controller");
const { verificarToken, permitirRoles } = require("../middlewares/auth.middleware");

const router = Router();

// Publica: para pintar el calendario antes de iniciar sesion.
router.get("/disponibilidad", ctrl.disponibilidad);

// El resto exige sesion.
router.get("/", verificarToken, ctrl.listar);
router.get("/resumen", verificarToken, ctrl.resumen);
router.post("/", verificarToken, ctrl.crear);
router.patch("/:id/estado", verificarToken, ctrl.cambiarEstado);
router.delete("/:id", verificarToken, permitirRoles("administrador"), ctrl.eliminar);

module.exports = router;
