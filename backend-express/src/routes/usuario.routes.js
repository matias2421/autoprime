const { Router } = require("express");
const ctrl = require("../controllers/usuario.controller");
const { verificarToken, permitirRoles } = require("../middlewares/auth.middleware");

const router = Router();

// Todo el modulo exige sesion iniciada.
router.use(verificarToken);

// Consultar: administrador y empleado
router.get("/", permitirRoles("administrador", "empleado"), ctrl.listar);
router.get("/:id", permitirRoles("administrador", "empleado"), ctrl.obtener);

// Gestionar: solo administrador
router.post("/", permitirRoles("administrador"), ctrl.crear);
router.put("/:id", permitirRoles("administrador"), ctrl.actualizar);
router.patch("/:id/estado", permitirRoles("administrador"), ctrl.cambiarEstado);
router.delete("/:id", permitirRoles("administrador"), ctrl.eliminar);

module.exports = router;
