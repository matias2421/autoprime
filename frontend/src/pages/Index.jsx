import LineasKv from "../components/LineasKv";
import VideoPortada from "../components/VideoPortada";
import Button from "../components/ui/Button";
import { useBloqueoScroll } from "../hooks/useBloqueoScroll";
import { useIdioma } from "../hooks/useIdioma";

/**
 * Portada.
 *
 * Ocupa exactamente una pantalla y no se desplaza: solo el vídeo de fondo y
 * lo justo para entrar al sitio. Todo lo que antes colgaba de aquí —catálogo,
 * cifras, actualidad, testimonios— vive ahora en "Quiénes somos".
 */
function Index() {
  const { t } = useIdioma();

  // Esta página cabe en una pantalla y no debe desplazarse. El resto del
  // sitio sí: el bloqueo se levanta solo al salir de aquí.
  useBloqueoScroll("portada");

  return (
    /*
     * `100svh` y no `100vh`: en móvil la barra del navegador se contrae al
     * desplazar y `100vh` deja la sección más alta que la ventana, lo que
     * reintroduce el desplazamiento que aquí no debe existir.
     */
    <section className="relative h-[100svh] w-full overflow-hidden bg-negro">
      <VideoPortada />

      {/* El velo mantiene legible el titular sobre cualquier fotograma. */}
      <div className="velo absolute inset-0" />
      <LineasKv className="absolute inset-y-0 left-0 h-full w-3/5" opacidad={0.3} />

      <div className="relative z-10 flex h-full flex-col justify-end px-5 pb-16 sm:px-12 lg:px-16 lg:pb-24">
        <p className="etiqueta text-accion">{t("portada.kicker")}</p>

        <h1 className="display mt-4 max-w-4xl text-[clamp(2.75rem,8vw,6.5rem)] text-hueso">
          {t("portada.titulo")}
        </h1>

        <p className="mt-5 max-w-xl text-base leading-relaxed text-ceniza">
          {t("portada.entrada")}
        </p>

        <div className="mt-9 flex flex-wrap gap-4">
          <Button to="/modelos" variante="primario" tamano="lg">
            {t("acc.verModelos")}
          </Button>
          <Button to="/agendar" variante="contorno" tamano="lg">
            {t("acc.agendar")}
          </Button>
        </div>
      </div>
    </section>
  );
}

export default Index;
