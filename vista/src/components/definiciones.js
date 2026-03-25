import * as d3 from "npm:d3";

export const DATA_BASE =
  "https://gist.githubusercontent.com/mauforonda/fe1f4882f415754529262ccedab31399/raw/23c7fe807ff92ddb8b1ecd22dfcbe6224633960d/";

export const STORAGE_KEY = "subnacionales2026_metrica";
export const STORAGE_MAP_KEY = "subnacionales2026_mapa";
export const STORAGE_ELECCION_KEY = "subnacionales2026_eleccion";

export const MAPA_FALLBACK = {
  center: [-64.8, -16.8],
  zoom: 4.8,
};

export const metricas = {
  invalido: {
    nombre: "¿Dónde votaron en blanco o nulo?",
    descripcion: "Porcentaje de votos blancos o nulos entre votos emitidos",
    campo: "invalido",
    dominio: [0.05, 0.4],
    ticks: [0.05, 0.15, 0.25, 0.4],
    colores: ["#ccedd2ba", "#6796b5", "#19149f"],
    format: d3.format(".0%"),
  },
  ganador: {
    nombre: "¿Dónde ganaron con mayor ventaja?",
    descripcion: "Porcentaje de votos válidos al partido ganador",
    campo: "ganador",
    dominio: [0.2, 0.65],
    ticks: [0.2, 0.35, 0.5, 0.65],
    colores: ["#e0dca9", "#dda234", "#e83d16"],
    format: d3.format(".0%"),
  },
};

export const elecciones = {
  gobernador: {
    nombre: "gobernador",
    archivo: "resultados_gobernador.json",
  },
  alcalde: {
    nombre: "alcalde",
    archivo: "resultados_alcalde.json",
  },
};

export function getStorage() {
  return typeof window !== "undefined" && window.localStorage
    ? window.localStorage
    : null;
}
