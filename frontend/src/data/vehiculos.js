/* ------------------------------ Pugnator ------------------------------ */
import pugnatorPerfil from "../assets/images/mansory-pugnator-perfil.webp";
import pugnator34Frontal from "../assets/images/mansory-pugnator-34-frontal.webp";
import pugnatorFrontal from "../assets/images/mansory-pugnator-frontal.webp";
import pugnator34Trasero from "../assets/images/mansory-pugnator-34-trasero.webp";
import pugnatorTrasero from "../assets/images/mansory-pugnator-trasero.webp";
import pugnatorCenital from "../assets/images/mansory-pugnator-cenital.webp";

/* ------------------------------- Phantom ------------------------------ */
import phantomLateral from "../assets/images/mansory-phantom-lateral.webp";
import phantom34Frontal from "../assets/images/mansory-phantom-34-frontal.webp";
import phantomFrontal from "../assets/images/mansory-phantom-frontal.webp";
import phantom34Trasero from "../assets/images/mansory-phantom-34-trasero.webp";
import phantomTrasero from "../assets/images/mansory-phantom-trasero.webp";
import phantomInterior from "../assets/images/mansory-phantom-interior.webp";

/* -------------------------------- SF90 -------------------------------- */
import sf90Perfil from "../assets/images/mansory-sf90-perfil.webp";
import sf9034Frontal from "../assets/images/mansory-sf90-34-frontal.webp";
import sf90Frontal from "../assets/images/mansory-sf90-frontal.webp";
import sf9034Trasero from "../assets/images/mansory-sf90-34-trasero.webp";
import sf9034TraseroAlto from "../assets/images/mansory-sf90-34-trasero-alto.webp";
import sf90Trasero from "../assets/images/mansory-sf90-trasero.webp";

/* ------------------------------- Vivere ------------------------------- */
import viverePerfil from "../assets/images/mansory-vivere-perfil.webp";
import vivere34Frontal from "../assets/images/mansory-vivere-34-frontal.webp";
import vivere34FrontalBajo from "../assets/images/mansory-vivere-34-frontal-bajo.webp";
import vivereFrontalCenital from "../assets/images/mansory-vivere-frontal-cenital.webp";
import vivere34TraseroAlto from "../assets/images/mansory-vivere-34-trasero-alto.webp";
import vivereTrasero from "../assets/images/mansory-vivere-trasero.webp";

/* -------------------------------- AL3C -------------------------------- */
import al3cPerfil from "../assets/images/mansory-al3c-perfil.webp";
import al3c34Frontal from "../assets/images/mansory-al3c-34-frontal.webp";
import al3c34FrontalAlto from "../assets/images/mansory-al3c-34-frontal-alto.webp";
import al3cFrontal from "../assets/images/mansory-al3c-frontal.webp";
import al3c34TraseroAlto from "../assets/images/mansory-al3c-34-trasero-alto.webp";
import al3cTrasero from "../assets/images/mansory-al3c-trasero.webp";

/* ------------------------------ Carbonado ----------------------------- */
import carbonado34Frontal from "../assets/images/mansory-carbonado-34-frontal.webp";
import carbonado34FrontalAlto from "../assets/images/mansory-carbonado-34-frontal-alto.webp";
import carbonadoFrontal from "../assets/images/mansory-carbonado-frontal.webp";
import carbonado34Trasero from "../assets/images/mansory-carbonado-34-trasero.webp";
import carbonadoAleron from "../assets/images/mansory-carbonado-detalle-aleron.webp";

/* ----------------------------- Elongation ----------------------------- */
import elongationPerfil from "../assets/images/mansory-elongation-perfil.webp";
import elongation34Frontal from "../assets/images/mansory-elongation-34-frontal.webp";
import elongation34FrontalAlto from "../assets/images/mansory-elongation-34-frontal-alto.webp";
import elongationFrontal from "../assets/images/mansory-elongation-frontal.webp";
import elongation34TraseroAlto from "../assets/images/mansory-elongation-34-trasero-alto.webp";
import elongationTrasero from "../assets/images/mansory-elongation-trasero.webp";

/* -------------------------------- Monza ------------------------------- */
import monzaPerfil from "../assets/images/mansory-monza-perfil.webp";
import monza34Frontal from "../assets/images/mansory-monza-34-frontal.webp";
import monzaFrontal from "../assets/images/mansory-monza-frontal.webp";
import monza34Trasero from "../assets/images/mansory-monza-34-trasero.webp";
import monzaTrasero from "../assets/images/mansory-monza-trasero.webp";

/* ------------------------------- Bentley ------------------------------ */
import bentleyPerfil from "../assets/images/mansory-bentley-perfil.webp";
import bentley34Frontal from "../assets/images/mansory-bentley-34-frontal.webp";
import bentley34FrontalAlto from "../assets/images/mansory-bentley-34-frontal-alto.webp";
import bentleyFrontal from "../assets/images/mansory-bentley-frontal.webp";
import bentley34Trasero from "../assets/images/mansory-bentley-34-trasero.webp";
import bentleyTrasero from "../assets/images/mansory-bentley-trasero.webp";

/* -------------------------------- P9LM -------------------------------- */
import p9lmPerfil from "../assets/images/mansory-p9lm-perfil.webp";
import p9lm34Frontal from "../assets/images/mansory-p9lm-34-frontal.webp";
import p9lm34FrontalAlto from "../assets/images/mansory-p9lm-34-frontal-alto.webp";
import p9lm34FrontalTecho from "../assets/images/mansory-p9lm-34-frontal-techo.webp";
import p9lm34TraseroAlto from "../assets/images/mansory-p9lm-34-trasero-alto.webp";
import p9lmTrasero from "../assets/images/mansory-p9lm-trasero.webp";

/**
 * Catálogo de AutoPrime: 10 preparaciones MANSORY.
 *
 * Cada ficha reúne el vehículo donante, las cifras que publica el preparador
 * y la serie de la que forma parte. Todas las fotografías son 3:2, de modo que
 * los contenedores del catálogo pueden mostrarlas completas sin recortar.
 *
 * Los precios en pesos son estimaciones de mercado con fines académicos:
 * MANSORY no publica tarifas. Las piezas únicas quedan en `null` y la interfaz
 * las muestra como "Precio bajo consulta".
 */

export const FAMILIAS = [
  { valor: "gama", etiqueta: "Gama" },
  { valor: "edicion", etiqueta: "Edición limitada" },
  { valor: "coleccion", etiqueta: "Colección" },
];

export const vehiculos = [
  {
    id: 1,
    slug: "pugnator-tricolore",
    marca: "MANSORY",
    modelo: "Pugnator Tricolore",
    titulo: "MANSORY Pugnator Tricolore",
    familia: "edicion",
    base: "Ferrari Purosangue",
    lema: "El SUV que no pide permiso",
    descripcion:
      "Carrocería completa en carbono visible sobre el primer cuatro puertas de Maranello. La bandera italiana recorre el costado en un tricolor pintado a mano que no se repetirá.",
    puntos: [
      "Sobre Ferrari Purosangue",
      "Potencia elevada a 755 hp / 730 Nm",
      "Pieza única — one-off",
    ],
    imagen: pugnatorPerfil,
    galeria: [
      pugnatorPerfil,
      pugnator34Frontal,
      pugnatorFrontal,
      pugnator34Trasero,
      pugnatorTrasero,
      pugnatorCenital,
    ],
    // La ficha muestra el visor 3D solo si este campo existe.
    modelo3d: { archivo: "/modelos3d/pugnator.glb", peso: "1,8 MB" },
    anio: 2024,
    kilometraje: 0,
    precio: null,
    unidades: 1,
    specs: {
      motor: "6.5 L V12 atmosférico",
      potencia: "755 hp",
      aceleracion: "3,1 s",
      velocidad: "312 km/h",
      transmision: "Doble embrague 8 vel.",
      traccion: "Integral",
    },
  },
  {
    id: 2,
    slug: "phantom-viii",
    marca: "MANSORY",
    modelo: "Phantom VIII",
    titulo: "MANSORY Phantom VIII",
    familia: "gama",
    base: "Rolls-Royce Phantom",
    lema: "Silencio, con otra voz",
    descripcion:
      "La berlina más solemne de Goodwood reinterpretada con paragolpes de carbono, llantas forjadas de 24 pulgadas e interior a medida. El lujo intacto; la presencia, nueva.",
    puntos: [
      "Sobre Rolls-Royce Phantom VIII",
      "6.75 L V12 biturbo — 602 hp",
      "Llantas forjadas de 24″",
    ],
    imagen: phantomLateral,
    galeria: [
      phantomLateral,
      phantom34Frontal,
      phantomFrontal,
      phantom34Trasero,
      phantomTrasero,
      phantomInterior,
    ],
    anio: 2024,
    kilometraje: 0,
    precio: 3200000000,
    unidades: null,
    specs: {
      motor: "6.75 L V12 biturbo",
      potencia: "602 hp",
      aceleracion: "5,4 s",
      velocidad: "250 km/h",
      transmision: "Automática 8 vel.",
      traccion: "Trasera",
    },
  },
  {
    id: 3,
    slug: "sf90-soft-kit",
    marca: "MANSORY",
    modelo: "SF90 Soft Kit",
    titulo: "MANSORY SF90 Soft Kit — White",
    familia: "edicion",
    base: "Ferrari SF90 Stradale",
    lema: "Mil cien caballos en blanco",
    descripcion:
      "El híbrido enchufable más potente de Ferrari con kit aerodinámico de carbono y electrónica revisada. Tres motores eléctricos acompañan al V8 biturbo hasta los 1.100 hp.",
    puntos: [
      "Sobre Ferrari SF90 Stradale",
      "Potencia elevada a 1.100 hp",
      "Kit aerodinámico completo en carbono",
    ],
    imagen: sf90Perfil,
    modelo3d: { archivo: "/modelos3d/sf90.glb", peso: "1,4 MB" },
    galeria: [
      sf90Perfil,
      sf9034Frontal,
      sf90Frontal,
      sf9034Trasero,
      sf9034TraseroAlto,
      sf90Trasero,
    ],
    anio: 2024,
    kilometraje: 0,
    precio: 3600000000,
    unidades: null,
    specs: {
      motor: "4.0 L V8 biturbo + 3 eléctricos",
      potencia: "1.100 hp",
      aceleracion: "2,4 s",
      velocidad: "355 km/h",
      transmision: "Doble embrague 8 vel.",
      traccion: "Integral",
    },
  },
  {
    id: 4,
    slug: "vivere",
    marca: "MANSORY",
    modelo: "Vivere",
    titulo: "MANSORY Bugatti Vivere",
    familia: "coleccion",
    base: "Bugatti Chiron",
    lema: "Mil cuatrocientos setenta y nueve",
    descripcion:
      "Reinterpretación integral del Chiron: frontal rediseñado, difusor de carbono y escape central. El W16 de cuatro turbos conserva su cifra íntegra bajo una piel nueva.",
    puntos: [
      "Sobre Bugatti Chiron",
      "8.0 L W16 cuatro turbos — 1.479 hp",
      "Carrocería reinterpretada en carbono",
    ],
    imagen: viverePerfil,
    galeria: [
      viverePerfil,
      vivere34Frontal,
      vivere34FrontalBajo,
      vivereFrontalCenital,
      vivere34TraseroAlto,
      vivereTrasero,
    ],
    anio: 2023,
    kilometraje: 0,
    precio: 16000000000,
    unidades: 10,
    specs: {
      motor: "8.0 L W16 cuatro turbos",
      potencia: "1.479 hp",
      aceleracion: "2,4 s",
      velocidad: "420 km/h",
      transmision: "Doble embrague 7 vel.",
      traccion: "Integral",
    },
  },
  {
    id: 5,
    slug: "art-piece-al3c",
    marca: "MANSORY",
    modelo: "Art Piece AL3C",
    titulo: "MANSORY Art Piece AL3C",
    familia: "coleccion",
    base: "Mercedes-AMG G 63",
    lema: "Un lienzo de dos toneladas",
    descripcion:
      "Colaboración con el artista pop Alec Monopoly: cada panel del todoterreno está intervenido a mano. Ancho de vías ampliado, carbono a la vista y 820 hp bajo el capó.",
    puntos: [
      "Sobre Mercedes-AMG G 63",
      "Potencia elevada a 820 hp / 1.000 Nm",
      "Intervención a mano de Alec Monopoly",
    ],
    imagen: al3cPerfil,
    galeria: [
      al3cPerfil,
      al3c34Frontal,
      al3c34FrontalAlto,
      al3cFrontal,
      al3c34TraseroAlto,
      al3cTrasero,
    ],
    anio: 2024,
    kilometraje: 0,
    precio: null,
    unidades: 1,
    specs: {
      motor: "4.0 L V8 biturbo",
      potencia: "820 hp",
      aceleracion: "3,9 s",
      velocidad: "240 km/h",
      transmision: "Automática 9 vel.",
      traccion: "Integral",
    },
  },
  {
    id: 6,
    slug: "carbonado-evo",
    marca: "MANSORY",
    modelo: "Carbonado EVO",
    titulo: "MANSORY Carbonado EVO",
    familia: "coleccion",
    base: "Lamborghini Aventador SVJ",
    lema: "Carbono de extremo a extremo",
    descripcion:
      "Kit de carrocería completo sobre el último V12 atmosférico de Sant'Agata. Alerón trasero de gran cuerda, capó ventilado y faldones nuevos, todos en fibra vista.",
    puntos: [
      "Sobre Lamborghini Aventador SVJ",
      "6.5 L V12 atmosférico — 770 hp",
      "Kit de carrocería completo — pieza única",
    ],
    imagen: carbonado34Frontal,
    galeria: [
      carbonado34Frontal,
      carbonado34FrontalAlto,
      carbonadoFrontal,
      carbonado34Trasero,
      carbonadoAleron,
    ],
    anio: 2023,
    kilometraje: 0,
    precio: 4800000000,
    unidades: 1,
    specs: {
      motor: "6.5 L V12 atmosférico",
      potencia: "770 hp",
      aceleracion: "2,9 s",
      velocidad: "350 km/h",
      transmision: "Automatizada 7 vel.",
      traccion: "Integral",
    },
  },
  {
    id: 7,
    slug: "elongation-evo",
    marca: "MANSORY",
    modelo: "Elongation EVO",
    titulo: "MANSORY Elongation EVO",
    familia: "gama",
    base: "Tesla Cybertruck",
    lema: "Acero inoxidable, nuevas aristas",
    descripcion:
      "El exoesqueleto de acero del Cybertruck ampliado con paneles de carbono, llantas forjadas y suspensión revisada. La silueta angular se alarga sin perder su geometría.",
    puntos: [
      "Sobre Tesla Cybertruck",
      "Tres motores eléctricos — 845 hp",
      "Paneles de carbono y llantas forjadas",
    ],
    imagen: elongationPerfil,
    galeria: [
      elongationPerfil,
      elongation34Frontal,
      elongation34FrontalAlto,
      elongationFrontal,
      elongation34TraseroAlto,
      elongationTrasero,
    ],
    anio: 2025,
    kilometraje: 0,
    precio: 1200000000,
    unidades: null,
    specs: {
      motor: "Tres motores eléctricos",
      potencia: "845 hp",
      aceleracion: "2,7 s",
      velocidad: "209 km/h",
      transmision: "Reductora directa",
      traccion: "Integral",
    },
  },
  {
    id: 8,
    slug: "monza-sp2",
    marca: "MANSORY",
    modelo: "Monza SP2",
    titulo: "MANSORY Ferrari Monza SP2",
    familia: "coleccion",
    base: "Ferrari Monza SP2",
    lema: "Sin techo, sin parabrisas, sin excusas",
    descripcion:
      "Un barchetta moderno de la serie Icona al que MANSORY añade carbono estructural y un escape específico. Sin techo ni parabrisas: solo el V12 a la espalda.",
    puntos: [
      "Sobre Ferrari Monza SP2",
      "6.5 L V12 atmosférico — 830 hp",
      "Serie Icona — 499 unidades",
    ],
    imagen: monzaPerfil,
    galeria: [
      monzaPerfil,
      monza34Frontal,
      monzaFrontal,
      monza34Trasero,
      monzaTrasero,
    ],
    anio: 2022,
    kilometraje: 0,
    precio: 10000000000,
    unidades: 499,
    specs: {
      motor: "6.5 L V12 atmosférico",
      potencia: "830 hp",
      aceleracion: "2,9 s",
      velocidad: "300 km/h",
      transmision: "Doble embrague 7 vel.",
      traccion: "Trasera",
    },
  },
  {
    id: 9,
    slug: "bentley-gt",
    marca: "MANSORY",
    modelo: "Bentley GT",
    titulo: "MANSORY Bentley Continental GT",
    familia: "gama",
    base: "Bentley Continental GT",
    lema: "Crewe, con más filo",
    descripcion:
      "El gran turismo de Crewe con programa aerodinámico de carbono y llantas forjadas específicas. El V8 híbrido entrega 782 hp sin renunciar al aislamiento de un Bentley.",
    puntos: [
      "Sobre Bentley Continental GT (MY2025)",
      "4.0 L V8 biturbo híbrido — 782 hp",
      "Programa aerodinámico en carbono",
    ],
    imagen: bentleyPerfil,
    galeria: [
      bentleyPerfil,
      bentley34Frontal,
      bentley34FrontalAlto,
      bentleyFrontal,
      bentley34Trasero,
      bentleyTrasero,
    ],
    anio: 2025,
    kilometraje: 0,
    precio: 1800000000,
    unidades: null,
    specs: {
      motor: "4.0 L V8 biturbo híbrido",
      potencia: "782 hp",
      aceleracion: "3,2 s",
      velocidad: "335 km/h",
      transmision: "Doble embrague 8 vel.",
      traccion: "Integral",
    },
  },
  {
    id: 10,
    slug: "p9lm-evo-900",
    marca: "MANSORY",
    modelo: "P9LM EVO 900",
    titulo: "MANSORY P9LM EVO 900 Cabrio",
    familia: "edicion",
    base: "Porsche 911 Turbo S Cabriolet",
    lema: "Novecientos, a cielo abierto",
    descripcion:
      "El 911 Turbo S descapotable llevado a 900 hp, con capó integral de carbono y asientos deportivos ligeros. Siete unidades en el mundo para la versión Cabrio.",
    puntos: [
      "Sobre Porsche 911 Turbo S Cabriolet",
      "Potencia elevada a 900 hp / 1.050 Nm",
      "Limitado a 7 unidades",
    ],
    imagen: p9lmPerfil,
    galeria: [
      p9lmPerfil,
      p9lm34Frontal,
      p9lm34FrontalAlto,
      p9lm34FrontalTecho,
      p9lm34TraseroAlto,
      p9lmTrasero,
    ],
    anio: 2024,
    kilometraje: 0,
    precio: 2000000000,
    unidades: 7,
    specs: {
      motor: "3.8 L bóxer 6 biturbo",
      potencia: "900 hp",
      aceleracion: "2,5 s",
      velocidad: "340 km/h",
      transmision: "Doble embrague 8 vel.",
      traccion: "Integral",
    },
  },
];

export const buscarVehiculo = (slug) =>
  vehiculos.find((vehiculo) => vehiculo.slug === slug);

export const formatearPrecio = (valor) =>
  valor === null
    ? "Precio bajo consulta"
    : new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 0,
      }).format(valor);

export const formatearKilometraje = (valor) =>
  valor === 0
    ? "0 km"
    : `${new Intl.NumberFormat("es-CO").format(valor)} km`;
