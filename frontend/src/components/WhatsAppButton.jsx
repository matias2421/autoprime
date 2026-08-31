import Icono from "./ui/Icono";

/**
 * Boton flotante de WhatsApp (requisito 15 del tercer avance).
 *
 * Componente reutilizable: recibe el numero y el mensaje por props, asi puede
 * usarse en cualquier pantalla con un texto distinto.
 */
function WhatsAppButton({
  numero = "573001234567",
  mensaje = "Hola, vengo de la pagina de AutoPrime y quiero informacion.",
  etiqueta = "Escribir por WhatsApp",
}) {
  const enlace = `https://wa.me/${numero}?text=${encodeURIComponent(mensaje)}`;

  return (
    <a
      href={enlace}
      target="_blank"
      rel="noreferrer noopener"
      aria-label={etiqueta}
      title={etiqueta}
      className="group fixed bottom-5 right-5 z-40 flex h-14 w-14 items-center
                 justify-center bg-[#25D366] text-negro shadow-lg transition-transform
                 duration-200 hover:scale-105 focus-visible:outline-2
                 focus-visible:outline-offset-3 focus-visible:outline-hueso
                 sm:bottom-8 sm:right-8 sm:h-16 sm:w-16"
    >
      <Icono nombre="whatsapp" relleno className="h-7 w-7 sm:h-8 sm:w-8" />

      {/* Etiqueta que aparece al pasar el mouse en pantallas grandes */}
      <span
        className="pointer-events-none absolute right-full mr-3 hidden whitespace-nowrap
                   bg-negro px-3 py-2 font-sans text-xs uppercase tracking-[0.14em]
                   text-hueso opacity-0 transition-opacity duration-200
                   group-hover:opacity-100 lg:block"
      >
        {etiqueta}
      </span>
    </a>
  );
}

export default WhatsAppButton;
