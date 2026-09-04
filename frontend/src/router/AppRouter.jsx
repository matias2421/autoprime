import { useEffect } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";

import Header from "../components/Header";
import Footer from "../components/Footer";
import WhatsAppButton from "../components/WhatsAppButton";
import BotonArriba from "../components/BotonArriba";
import CursorLente from "../components/CursorLente";
import TransicionPagina from "../components/TransicionPagina";
import RutaProtegida from "../components/RutaProtegida";
import { AuthProvider } from "../context/AuthContext";
import { useReflejoPuntero } from "../hooks/useReflejoPuntero";

import Index from "../pages/Index";
import Modelos from "../pages/Modelos";
import ModeloDetalle from "../pages/ModeloDetalle";
import QuienesSomos from "../pages/QuienesSomos";
import Contacto from "../pages/Contacto";
import IniciarSesion from "../pages/IniciarSesion";
import RestablecerPassword from "../pages/RestablecerPassword";
import AgendarCita from "../pages/AgendarCita";
import PanelAdmin from "../pages/panel/PanelAdmin";
import PanelEmpleado from "../pages/panel/PanelEmpleado";
import PanelCliente from "../pages/panel/PanelCliente";
import NoEncontrado from "../pages/NoEncontrado";

/**
 * El pie no se muestra en la portada.
 *
 * Esa página ocupa exactamente una pantalla y bloquea el desplazamiento, así
 * que un pie debajo sería inalcanzable y además reintroduciría el scroll.
 */
function PieCondicional() {
  const { pathname } = useLocation();
  // Mismo margen que `main`: el pie queda fuera de <main> y hay que
  // apartarlo del rail por separado.
  return pathname === "/" ? null : (
    <div className="lg:pl-[72px]">
      <Footer />
    </div>
  );
}

/** Lleva la vista al inicio en cada cambio de ruta. */
function IrArriba() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [pathname]);

  return null;
}

function AppRouter() {
  // Un solo escuchador de puntero para todas las piezas con reflejo.
  useReflejoPuntero();

  return (
    <BrowserRouter>
      {/* El proveedor va dentro del router porque el Header navega al salir. */}
      <AuthProvider>
        <IrArriba />
        <Header />

        <main id="contenido" className="flex-1 lg:pl-[72px]">
          {/* Anima la entrada de cada pagina; se reinicia al cambiar de ruta. */}
          <TransicionPagina>
            <Routes>
              {/* ------------------------- Publicas ------------------------- */}
              <Route path="/" element={<Index />} />
              <Route path="/modelos" element={<Modelos />} />
              <Route path="/modelos/:slug" element={<ModeloDetalle />} />
              <Route path="/quienes-somos" element={<QuienesSomos />} />
              <Route path="/contacto" element={<Contacto />} />
              <Route path="/login" element={<IniciarSesion />} />

              {/* Se llega desde el enlace del correo, con ?token= */}
              <Route path="/restablecer" element={<RestablecerPassword />} />

              {/* Se puede ver sin sesion; al confirmar pide iniciar sesion. */}
              <Route path="/agendar" element={<AgendarCita />} />

              {/* --------------------- Paneles por rol --------------------- */}
              <Route
                path="/panel/admin"
                element={
                  <RutaProtegida roles={["administrador"]}>
                    <PanelAdmin />
                  </RutaProtegida>
                }
              />
              <Route
                path="/panel/empleado"
                element={
                  <RutaProtegida roles={["administrador", "empleado"]}>
                    <PanelEmpleado />
                  </RutaProtegida>
                }
              />
              <Route
                path="/panel/cliente"
                element={
                  <RutaProtegida roles={["cliente", "administrador", "empleado"]}>
                    <PanelCliente />
                  </RutaProtegida>
                }
              />

              <Route path="*" element={<NoEncontrado />} />
            </Routes>
          </TransicionPagina>
        </main>

        <PieCondicional />

        {/* Botones flotantes, visibles en toda la app. */}
        <CursorLente />
        <BotonArriba />
        <WhatsAppButton />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default AppRouter;
