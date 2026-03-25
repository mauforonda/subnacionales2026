import maplibregl from "../../_npm/maplibre-gl@5.21.1/13f11ada.js";

export function circleColorExpr(metrica) {
  const { campo, dominio, colores } = metrica;
  const medio = (dominio[0] + dominio[1]) / 2;
  return [
    "interpolate",
    ["linear"],
    ["coalesce", ["to-number", ["get", campo]], dominio[0]],
    dominio[0],
    colores[0],
    medio,
    colores[1],
    dominio[1],
    colores[2],
  ];
}

export function circleRadiusExpr(campo) {
  return [
    "interpolate",
    ["linear"],
    ["zoom"],
    6,
    ["min", 2, ["max", 1, ["*", 0.03, ["to-number", ["get", campo]]]]],
    12,
    ["min", 7, ["max", 2, ["*", 0.02, ["to-number", ["get", campo]]]]],
    16,
    ["min", 21, ["max", 3, ["*", 0.08, ["to-number", ["get", campo]]]]],
  ];
}

export function circleHoverRadiusExpr(campo) {
  return [
    "interpolate",
    ["linear"],
    ["zoom"],
    6,
    [
      "*",
      1.3,
      ["min", 2, ["max", 1, ["*", 0.03, ["to-number", ["get", campo]]]]],
    ],
    12,
    [
      "*",
      1.3,
      ["min", 7, ["max", 2, ["*", 0.02, ["to-number", ["get", campo]]]]],
    ],
    16,
    [
      "*",
      1.3,
      ["min", 21, ["max", 3, ["*", 0.08, ["to-number", ["get", campo]]]]],
    ],
  ];
}

export function crearMapa(selector, mapaInicial) {
  const map = new maplibregl.Map({
    container: document.querySelector(selector),
    style:
      "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json",
    center: mapaInicial.center,
    zoom: mapaInicial.zoom,
    minZoom: 4.2,
    maxZoom: 15,
    scrollZoom: true,
    attributionControl: {
      compact: true,
      customAttribution:
        "<a href='https://mauforonda.github.io/'>Mauricio Foronda</a>",
    },
  });

  map.addControl(new maplibregl.NavigationControl(), "bottom-right");
  return map;
}

export function aplicarMetricaMapa(map, metrica) {
  if (!map.getLayer("recintos")) return;
  map.setPaintProperty("recintos", "circle-color", circleColorExpr(metrica));
  map.triggerRepaint();
}

export function persistirMapa(map, storage, key) {
  map.on("moveend", () => {
    if (!storage) return;
    const center = map.getCenter();
    storage.setItem(
      key,
      JSON.stringify({
        center: [center.lng, center.lat],
        zoom: map.getZoom(),
      }),
    );
  });
}

export function leerMapaInicial(storage, key, fallback) {
  if (!storage) return fallback;
  try {
    const value = JSON.parse(storage.getItem(key));
    if (
      value &&
      Array.isArray(value.center) &&
      value.center.length === 2 &&
      Number.isFinite(value.center[0]) &&
      Number.isFinite(value.center[1]) &&
      Number.isFinite(value.zoom)
    ) {
      return value;
    }
  } catch {}
  return fallback;
}

export function crearCapasBase(map, recintos, metrica) {
  if (!map.getSource("recintos")) {
    map.addSource("recintos", {
      type: "geojson",
      data: recintos,
    });
  }

  if (!map.getLayer("recintos")) {
    map.addLayer({
      id: "recintos",
      type: "circle",
      source: "recintos",
      paint: {
        "circle-radius": circleRadiusExpr("habilitados"),
        "circle-color": circleColorExpr(metrica),
        "circle-opacity": 0.62,
      },
    });
  }

  if (!map.getSource("etiquetas")) {
    map.addSource("etiquetas", {
      type: "raster",
      tiles: [
        "https://a.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}.png",
      ],
      tileSize: 256,
    });
  }

  if (!map.getLayer("etiquetas")) {
    map.addLayer({
      id: "etiquetas",
      type: "raster",
      source: "etiquetas",
      paint: { "raster-opacity": 0.8 },
    });
  }

  if (!map.getLayer("recintos_hover")) {
    map.addLayer({
      id: "recintos_hover",
      type: "circle",
      source: "recintos",
      filter: ["!=", ["get", "municipio_nombre"], null],
      paint: {
        "circle-color": "rgba(0,0,0,0)",
        "circle-radius": circleHoverRadiusExpr("habilitados"),
      },
    });
  }
}
