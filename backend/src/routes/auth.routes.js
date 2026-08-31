const { Router } = require("express");
const { registro, login, perfil } = require("../controllers/auth.controller");
const { verificarToken } = require("../middlewares/auth.middleware");

const router = Router();

// Publicas
router.post("/registro", registro);
router.post("/login", login);

// Protegida: devuelve el usuario del token
router.get("/perfil", verificarToken, perfil);

module.exports = router;
