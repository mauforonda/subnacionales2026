---
theme: dashboard
title: Segunda Vuelta 2026
toc: false
sidebar: false
---

<link
  rel="stylesheet"
  type="text/css"
  href="https://unpkg.com/maplibre-gl@4.0.2/dist/maplibre-gl.css"
>

<link
  rel="stylesheet"
  type="text/css"
  href="index.css"
>

<link
  rel="stylesheet"
  type="text/css"
  href="gobernaciones.css"
>

```js
import * as d3 from "npm:d3";
import * as Plot from "npm:@observablehq/plot";
import maplibregl from "npm:maplibre-gl";
import { feature as topojsonFeature } from "npm:topojson-client";
import { getStorage } from "./components/definiciones.js";
import { obtenerDefinicionesDepartamento } from "./components/gobernaciones_definiciones.js";
import {
  circleHoverRadiusExpr,
  circleRadiusExpr,
  crearMapa,
  leerMapaInicial,
  limpiarResaltado,
  persistirMapa,
  resaltarFeature,
} from "./components/mapa.js";
```

```js
const DATA_BASE =
  "https://raw.githubusercontent.com/mauforonda/subnacionales2026/refs/heads/main/mapas/artefactos/segunda_vuelta/gobernaciones/";
const MUNICIPIOS_URL =
  "https://raw.githubusercontent.com/mauforonda/subnacionales2026/refs/heads/main/mapas/artefactos/segunda_vuelta/municipios.json";
const MUNICIPIOS_TOPO_URL =
  "https://raw.githubusercontent.com/mauforonda/subnacionales2026/refs/heads/main/mapas/artefactos/primera_vuelta/municipios.topo.json";
const TIMESTAMP_URL =
  "https://raw.githubusercontent.com/mauforonda/subnacionales2026/refs/heads/main/mapas/artefactos/segunda_vuelta/timestamp";
const STORAGE_DEPARTAMENTO_KEY = "subnacionales2026_segunda_vuelta_departamento";
const STORAGE_MAP_KEY = "subnacionales2026_segunda_vuelta_mapa";
const MAPA_FALLBACK = {
  center: [-63.2, -17.82],
  zoom: 6.4,
};
const DEPARTAMENTOS = {
  1: "Chuquisaca",
  4: "Oruro",
  6: "Tarija",
  7: "Santa Cruz",
  8: "Beni",
};
const storage = getStorage();
const manifiesto = await d3.json(`${DATA_BASE}manifiesto.json`);
const municipiosRaw = await d3.json(MUNICIPIOS_URL);
const municipiosTopo = await d3.json(MUNICIPIOS_TOPO_URL);
const municipiosGeo = topojsonAFeatureCollection(municipiosTopo);
const timestampRaw = await d3.text(TIMESTAMP_URL).catch(() => "");
const timestamp = formatearTimestamp(timestampRaw);
const departamentoGuardado = storage?.getItem(STORAGE_DEPARTAMENTO_KEY);
const departamentoPreferido = manifiesto?.["7"] ? "7" : null;
const primerDepartamentoDisponible = Object.keys(manifiesto ?? {})[0] ?? "7";
const departamentoInicial =
  departamentoGuardado && manifiesto[departamentoGuardado]
    ? departamentoGuardado
    : (departamentoPreferido ?? primerDepartamentoDisponible);
const departamentoInput = Inputs.select(Object.keys(DEPARTAMENTOS), {
  value: departamentoInicial,
  format: (d) => DEPARTAMENTOS[d] ?? d,
  label: null,
});
const mapaInicial = leerMapaInicial(storage, STORAGE_MAP_KEY, MAPA_FALLBACK);
const datasetsCache = new Map();
const MUNICIPIOS_FADE_START = 10.6;
const MUNICIPIOS_FADE_END = 11;

function formatearTimestamp(value) {
  const timestamp = value?.trim();
  if (!timestamp) return null;
  const [fecha, hora] = timestamp.split(" ");
  if (!fecha || !hora) return null;
  const [year, month, day] = fecha.split("-");
  const [hours, minutes] = hora.split(":");
  return {
    fecha: `${day}/${month}/${year}`,
    hora: `${hours}:${minutes}`,
  };
}

function topojsonAFeatureCollection(topology) {
  const objectName = Object.keys(topology?.objects ?? {})[0];
  if (!objectName) return { type: "FeatureCollection", features: [] };
  return topojsonFeature(topology, topology.objects[objectName]);
}

function normalizarMunicipioCodigo(value) {
  return `${value ?? ""}`.replace(/^0+/, "");
}
```

<div class="app">
  <header class="header header--gobernaciones">
    <div class="header__eyebrow">Elecciones subnacionales 2026</div>
    <div class="header__subtitle">Resultados para gobernador en segunda vuelta</div>
    <div class="header__timestamp" id="timestamp-container"></div>
    <button
      class="header__toggle"
      id="header-toggle"
      type="button"
      aria-expanded="true"
      aria-label="Ocultar panel"
    ><span class="header__toggle_icon" aria-hidden="true"></span></button>
    <div class="header__collapsible" id="header-collapsible">
      <div class="header__selector">
        <div class="header__selector_label">Selecciona un departamento</div>
        ${departamentoInput}
      </div>
      <div class="header__summary" id="resumen-departamento"></div>
    </div>
  </header>

  <div id="mapa"></div>
  <div class="credito">
    <img
      class="credito__logo"
      src="https://mauforonda.github.io/images/icon.svg"
      alt=""
    >
    <span class="credito__text">Creado por Mauricio Foronda</span>
  </div>
</div>

```js
{
  const container = document.querySelector("#timestamp-container");
  container.textContent = timestamp
    ? `actualizado el ${timestamp.fecha} a las ${timestamp.hora}`
    : "";
}
```

```js
{
  const header = document.querySelector(".header--gobernaciones");
  const scrollContainer = document.querySelector("#header-collapsible");
  const toggle = document.querySelector("#header-toggle");
  if (header) {
    const actualizarIndicadorScroll = () => {
      if (!scrollContainer) return;
      const scrollable =
        scrollContainer.scrollHeight - scrollContainer.clientHeight > 12;
      const atBottom =
        scrollContainer.scrollTop + scrollContainer.clientHeight >=
        scrollContainer.scrollHeight - 4;
      header.classList.toggle("header--scrollable", scrollable);
      header.classList.toggle("header--at-bottom", !scrollable || atBottom);
    };

    const rafActualizar = () => requestAnimationFrame(actualizarIndicadorScroll);
    header.__updateScrollIndicator = rafActualizar;

    scrollContainer?.addEventListener("scroll", actualizarIndicadorScroll);
    window.addEventListener("resize", rafActualizar);

    const actualizarColapso = () => {
      if (!toggle) return;
      const collapsed = header.classList.contains("header--collapsed");
      toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
      toggle.setAttribute(
        "aria-label",
        collapsed ? "Expandir panel" : "Ocultar panel",
      );
      rafActualizar();
    };

    const alternarColapso = () => {
      if (window.innerWidth > 720) return;
      header.classList.toggle("header--collapsed");
      actualizarColapso();
    };

    toggle?.addEventListener("click", alternarColapso);
    rafActualizar();
    actualizarColapso();

    invalidation.then(() => {
      scrollContainer?.removeEventListener("scroll", actualizarIndicadorScroll);
      window.removeEventListener("resize", rafActualizar);
      toggle?.removeEventListener("click", alternarColapso);
      delete header.__updateScrollIndicator;
    });
  }
}
```

```js
const map = crearMapa("#mapa", mapaInicial);
const popup = new maplibregl.Popup({
  closeButton: true,
  closeOnClick: false,
});
persistirMapa(map, storage, STORAGE_MAP_KEY);

invalidation.then(() => {
  popup.remove();
  map.remove();
});
```

```js
function fotoPartido(meta, id) {
  const foto = meta?.[id]?.foto;
  if (typeof foto === "string" && foto) return foto;
  const color = meta?.[id]?.color ?? "#b8b8b8";
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><circle cx="50" cy="50" r="49" fill="${color}" fill-opacity="0.22" stroke="${color}" stroke-opacity="0.38" stroke-width="1.5"/></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

function ordenarResultados(resultado, meta) {
  const total = Object.values(resultado ?? {}).reduce(
    (acc, value) => acc + value,
    0,
  );
  const partidos = Object.entries(resultado ?? {})
    .map(([id, votos]) => ({
      id,
      votos,
      porcentaje: total ? votos / total : 0,
      ...(meta[id] ?? {
        nombre: id,
        color: "#b8b8b8",
        candidato: "",
        foto: null,
      }),
    }))
    .sort((a, b) => {
      if (a.id === "otros") return 1;
      if (b.id === "otros") return -1;
      return b.votos - a.votos;
    });
  return { total, partidos };
}

function plotResultado(resultado, meta, { fontSizeMultiplier = 1 } = {}) {
  const { partidos } = ordenarResultados(resultado, meta);
  if (!partidos.length) return document.createElement("div");
  const data = partidos.map((partido) => ({
    ...partido,
    foto: fotoPartido(meta, partido.id),
  }));
  const chart = Plot.plot({
    className: "resultado-chart",
    margin: 0,
    marginLeft: 78,
    marginRight: 10,
    height: data.length * 70,
    x: { axis: null, domain: [0, 1] },
    y: { axis: null, domain: data.map((d) => d.id) },
    marks: [
      Plot.image(data, {
        x: 0,
        y: "id",
        src: "foto",
        dx: -42,
        dy: 5,
        r: 22,
        width: 56,
      }),
      Plot.barX(data, {
        x: 1,
        y: "id",
        fill: "var(--chart-bar-bg)",
        insetTop: 30,
        insetBottom: 8,
        r: 12,
      }),
      Plot.barX(data, {
        x: "porcentaje",
        y: "id",
        fill: (d) => d.color ?? "#b8b8b8",
        fillOpacity: (d) => (d.id === "otros" ? .5 : 0.82),
        insetTop: 30,
        insetBottom: 8,
        r: 12,
      }),
      Plot.barX(data, {
        x: 1,
        y: "id",
        fill: null,
        stroke: "rgba(17,17,17,0.16)",
        strokeWidth: 1,
        insetTop: 30,
        insetBottom: 8,
        r: 12,
      }),
      Plot.text(data, {
        x: 0,
        y: "id",
        text: (d) => d.candidato ?? d.id,
        fill: "var(--text-soft)",
        fontSize: 17 * fontSizeMultiplier,
        fontWeight: 600,
        fillOpacity: 0.9,
        textAnchor: "start",
        lineAnchor: "bottom",
        dx: 6,
        dy: -12,
      }),
      Plot.text(data, {
        x: 1,
        y: "id",
        text: (d) => d3.format(".2%")(d.porcentaje),
        fill: "var(--text-soft)",
        fontSize: 15 * fontSizeMultiplier,
        fontWeight: 500,
        textAnchor: "end",
        lineAnchor: "bottom",
        dx: -6,
        dy: -12,
      }),
    ],
  });
  chart.removeAttribute("height");
  chart.style.width = "100%";
  chart.style.height = "auto";
  return chart;
}

function popupNode(recinto, meta, departamentoNombre) {
  const node = document.createElement("div");
  node.className = "popup popup--gobernaciones";
  const votosValidos = Object.values(recinto.resultados ?? {}).reduce(
    (acc, value) => acc + value,
    0,
  );

  const title = document.createElement("div");
  title.className = "popup__title";
  title.textContent = recinto.recinto ?? "Recinto sin nombre";

  const subtitle = document.createElement("div");
  subtitle.className = "popup__subtitle";
  subtitle.textContent = recinto.municipio ?? departamentoNombre ?? "";

  const info = document.createElement("div");
  info.className = "popup__meta";
  info.textContent = `${d3.format(",")(votosValidos)} votos válidos contados`;

  const ganador = document.createElement("div");
  ganador.className = "popup__meta";
  ganador.textContent = `Ganó: ${meta?.[recinto.ganador]?.nombre ?? recinto.ganador ?? "s/d"}`;

  const chartWrap = document.createElement("div");
  chartWrap.className = "popup__chart";
  chartWrap.append(
    plotResultado(recinto.resultados, meta, { fontSizeMultiplier: 1.2 }),
  );

  node.append(title, subtitle, info, chartWrap);
  return node;
}

function popupNodeMunicipio(municipio, meta, departamentoNombre) {
  const node = document.createElement("div");
  node.className = "popup popup--gobernaciones";
  const votosValidos = Object.values(municipio.resultados ?? {}).reduce(
    (acc, value) => acc + value,
    0,
  );

  const title = document.createElement("div");
  title.className = "popup__title";
  title.textContent = municipio.nombre_municipio ?? "Municipio sin nombre";

  const subtitle = document.createElement("div");
  subtitle.className = "popup__subtitle";
  subtitle.textContent = departamentoNombre ?? municipio.departamento ?? "";

  const info = document.createElement("div");
  info.className = "popup__meta";
  info.textContent = `${d3.format(",")(votosValidos)} votos válidos contados`;

  const ganador = document.createElement("div");
  ganador.className = "popup__meta";
  // ganador.textContent = `Ganó: ${meta?.[municipio.nombre]?.nombre ?? municipio.nombre ?? "s/d"}`;

  const chartWrap = document.createElement("div");
  chartWrap.className = "popup__chart";
  chartWrap.append(
    plotResultado(municipio.resultados, meta, { fontSizeMultiplier: 1.2 }),
  );

  node.append(title, subtitle, info, ganador, chartWrap);
  return node;
}

function resumenNode(metaDepartamento) {
  const container = document.createElement("div");
  const definiciones = obtenerDefinicionesDepartamento(
    metaDepartamento.codigo,
    metaDepartamento.partidos,
  );
  const chart = plotResultado(metaDepartamento.partidos, definiciones, {
    fontSizeMultiplier: 1.1,
  });
  container.append(
    chart,
  );

  if (metaDepartamento.completo != null) {
    const completo = document.createElement("div");
    completo.className = "popup__meta";
    completo.textContent = `${d3.format(".0%")(metaDepartamento.completo)} de actas contadas`;
    container.append(completo);
  }

  return container;
}

function boundsFromRecintos(recintos) {
  const bounds = new maplibregl.LngLatBounds();
  Object.values(recintos).forEach((recinto) => {
    bounds.extend([+recinto.x, +recinto.y]);
  });
  return bounds;
}

async function cargarDepartamento(codigo) {
  if (datasetsCache.has(codigo)) return datasetsCache.get(codigo);
  const recintos = await d3.json(`${DATA_BASE}${codigo}.json`);
  const departamentoNombre =
    manifiesto[codigo]?.nombre ?? DEPARTAMENTOS[codigo] ?? codigo;
  const municipios = Object.fromEntries(
    Object.entries(municipiosRaw ?? {})
      .filter(([, value]) => value?.departamento === departamentoNombre)
      .map(([municipioCodigo, value]) => [
        municipioCodigo,
        {
          codigo: municipioCodigo,
          nombre_municipio: value.nombre_municipio,
          departamento: value.departamento,
          ...(value.gobernador ?? {}),
        },
      ]),
  );
  const features = Object.entries(recintos).map(([codigoRecinto, recinto]) => ({
    type: "Feature",
    geometry: {
      type: "Point",
      coordinates: [+recinto.x, +recinto.y],
    },
    properties: {
      codigo: codigoRecinto,
      codigo_hover: codigoRecinto,
      recinto: recinto.recinto,
      municipio: recinto.municipio,
      departamento: departamentoNombre,
      habilitados: +recinto.habilitados || 0,
      ganador: recinto.ganador,
      ...(recinto.resultados ?? {}),
    },
  }));
  const municipiosFeatures = municipiosGeo.features
    .filter((feature) => `${feature.properties?.departamento ?? ""}` === codigo)
    .map((feature, index) => {
      const municipioCodigo = normalizarMunicipioCodigo(
        feature.properties?.municipio,
      );
      const municipio = municipios[municipioCodigo];
      if (!municipio) return null;
      return {
        type: "Feature",
        id: `municipio-${municipioCodigo || index}`,
        geometry: feature.geometry,
        properties: {
          feature_id: `municipio-${municipioCodigo || index}`,
          codigo_hover: municipioCodigo,
          nivel: "municipio",
          municipio_codigo: municipioCodigo,
          departamento_codigo: codigo,
          nombre_territorio: municipio.nombre_municipio,
          municipio_nombre: municipio.nombre_municipio,
          departamento: municipio.departamento,
          habilitados: +municipio.habilitados || 0,
          ganador: +municipio.ganador || 0,
          partido_ganador_scope: municipio.nombre ?? null,
          ...(municipio.resultados ?? {}),
        },
      };
    })
    .filter(Boolean);
  const data = {
    codigo,
    recintos,
    municipios,
    featureCollection: {
      type: "FeatureCollection",
      features,
    },
    municipiosCollection: {
      type: "FeatureCollection",
      features: municipiosFeatures,
    },
    bounds: boundsFromRecintos(recintos),
  };
  datasetsCache.set(codigo, data);
  return data;
}

function colorExpr(partidos) {
  const candidaturas = Object.entries(partidos)
    .filter(([id]) => id !== "otros")
    .slice(0, 2);

  if (candidaturas.length !== 2) return "#b8b8b8";

  const [[idA, metaA], [idB, metaB]] = candidaturas;
  const colorA = metaA?.color ?? "#b8b8b8";
  const colorB = metaB?.color ?? "#b8b8b8";
  const colorCentro = "#dbd4c6";

  return [
    "case",
    ["<=", ["+", ["coalesce", ["get", idA], 0], ["coalesce", ["get", idB], 0]], 0],
    "#b8b8b8",
    [
      "interpolate",
      ["linear"],
      [
        "/",
        ["coalesce", ["get", idA], 0],
        ["+", ["coalesce", ["get", idA], 0], ["coalesce", ["get", idB], 0]],
      ],
      .3,
      colorB,
      0.5,
      colorCentro,
      .7,
      colorA,
    ],
  ];
}
```

```js
const ready = new Promise((resolve) => {
  map.on("load", () => {
    map.addSource("municipios", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
      promoteId: "codigo_hover",
    });
    map.addSource("recintos", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
      promoteId: "codigo_hover",
    });
    map.addSource("etiquetas", {
      type: "raster",
      tiles: [
        "https://a.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}.png",
      ],
      tileSize: 256,
    });
    map.addLayer({
      id: "municipios_fill",
      type: "fill",
      source: "municipios",
      paint: {
        "fill-color": "#b8b8b8",
        "fill-opacity": [
          "interpolate",
          ["linear"],
          ["zoom"],
          MUNICIPIOS_FADE_START,
          0.36,
          MUNICIPIOS_FADE_END,
          0,
        ],
      },
    });
    map.addLayer({
      id: "municipios_line",
      type: "line",
      source: "municipios",
      paint: {
        "line-color": "rgba(245, 242, 235, 0.34)",
        "line-width": 0.7,
        "line-opacity": [
          "interpolate",
          ["linear"],
          ["zoom"],
          MUNICIPIOS_FADE_START,
          1,
          MUNICIPIOS_FADE_END,
          0,
        ],
      },
    });
    map.addLayer({
      id: "municipios_selected",
      type: "line",
      source: "municipios",
      paint: {
        "line-color": "rgba(255, 255, 255, 0.95)",
        "line-width": [
          "case",
          ["boolean", ["feature-state", "hover"], false],
          1.8,
          0,
        ],
        "line-opacity": [
          "interpolate",
          ["linear"],
          ["zoom"],
          MUNICIPIOS_FADE_START,
          1,
          MUNICIPIOS_FADE_END,
          0,
        ],
      },
    });
    map.addLayer({
      id: "municipios_hover",
      type: "fill",
      source: "municipios",
      maxzoom: MUNICIPIOS_FADE_END,
      paint: {
        "fill-color": "rgba(0,0,0,0)",
        "fill-opacity": 0.01,
      },
    });
    map.addLayer({
      id: "recintos",
      type: "circle",
      source: "recintos",
      paint: {
        "circle-radius": circleRadiusExpr("habilitados"),
        "circle-color": "#b8b8b8",
        "circle-opacity": 0.98,
      },
    });
    map.addLayer({
      id: "recintos_selected",
      type: "circle",
      source: "recintos",
      paint: {
        "circle-radius": circleHoverRadiusExpr("habilitados"),
        "circle-color": "rgba(0,0,0,0)",
        "circle-stroke-color": "rgba(68, 67, 66, 0.5)",
        "circle-stroke-width": [
          "case",
          ["boolean", ["feature-state", "hover"], false],
          1,
          0,
        ],
      },
    });
    map.addLayer({
      id: "etiquetas",
      type: "raster",
      source: "etiquetas",
      paint: { "raster-opacity": 0.8 },
    });
    map.addLayer({
      id: "recintos_hover",
      type: "circle",
      source: "recintos",
      minzoom: MUNICIPIOS_FADE_END,
      paint: {
        "circle-color": "rgba(0,0,0,0)",
        "circle-radius": circleHoverRadiusExpr("habilitados"),
      },
    });
    resolve();
  });
});
```

```js
{
  await ready;
  let locked = false;
  let suppressPopupClose = false;
  let currentCodigo = null;
  let currentData = null;
  let requestId = 0;

  const actualizarInteractividadPopup = () => {
    const el = popup.getElement();
    if (!el) return;
    el.classList.toggle("popup--interactive", locked);
  };

  const limpiarInteraccion = () => {
    locked = false;
    map.__activePopupFeature = null;
    map.__activePopupSource = null;
    limpiarResaltado(map);
    popup.remove();
  };

  const renderResumen = (codigo) => {
    const container = document.querySelector("#resumen-departamento");
    if (!container) return;
    container.replaceChildren(resumenNode({ codigo, ...manifiesto[codigo] }));
    document.querySelector(".header--gobernaciones")
      ?.__updateScrollIndicator?.();
  };

  const aplicarDepartamento = async (codigo, { ajustarVista = false } = {}) => {
    requestId += 1;
    const currentRequestId = requestId;
    const data = await cargarDepartamento(codigo);
    if (currentRequestId !== requestId) return;
    currentCodigo = codigo;
    currentData = data;
    map.getSource("municipios")?.setData(data.municipiosCollection);
    map.getSource("recintos")?.setData(data.featureCollection);
    map.setPaintProperty(
      "municipios_fill",
      "fill-color",
      colorExpr(
        obtenerDefinicionesDepartamento(codigo, manifiesto[codigo].partidos),
      ),
    );
    map.setPaintProperty(
      "recintos",
      "circle-color",
      colorExpr(
        obtenerDefinicionesDepartamento(codigo, manifiesto[codigo].partidos),
      ),
    );
    renderResumen(codigo);
    if (storage) storage.setItem(STORAGE_DEPARTAMENTO_KEY, codigo);
    if (ajustarVista && !data.bounds.isEmpty()) {
      map.fitBounds(data.bounds, {
        padding: { top: 120, right: 40, bottom: 40, left: 40 },
        duration: 900,
        maxZoom: 10,
      });
    }
  };

  const codigoInicial = departamentoInput.value;
  const savedDepartamento = storage?.getItem(STORAGE_DEPARTAMENTO_KEY);
  await aplicarDepartamento(codigoInicial, {
    ajustarVista: !savedDepartamento || savedDepartamento !== codigoInicial,
  });

  const actualizarPopup = (feature, source) => {
    const meta = obtenerDefinicionesDepartamento(
      currentCodigo,
      manifiesto[currentCodigo].partidos,
    );
    if (source === "municipios") {
      const codigo = feature?.properties?.municipio_codigo;
      if (!codigo || !currentData?.municipios?.[codigo]) return;
      popup.setDOMContent(
        popupNodeMunicipio(
          currentData.municipios[codigo],
          meta,
          manifiesto[currentCodigo].nombre,
        ),
      );
    } else {
      const codigo = feature?.properties?.codigo;
      if (!codigo || !currentData?.recintos?.[codigo]) return;
      popup.setDOMContent(
        popupNode(
          currentData.recintos[codigo],
          meta,
          manifiesto[currentCodigo].nombre,
        ),
      );
    }
    actualizarInteractividadPopup();
  };

  const sameHoverTarget = (feature, source) =>
    map.__activePopupSource === source &&
    map.__activePopupFeature?.properties?.codigo_hover ===
      feature?.properties?.codigo_hover;

  const mousemoveMunicipios = (e) => {
    if (locked) return;
    map.getCanvas().style.cursor = "pointer";
    const feature = e.features?.[0];
    if (!feature) return;
    if (sameHoverTarget(feature, "municipios")) {
      popup.setLngLat(e.lngLat ?? map.getCenter());
      return;
    }
    map.__activePopupFeature = feature;
    map.__activePopupSource = "municipios";
    resaltarFeature(map, "municipios", feature);
    suppressPopupClose = true;
    popup.setLngLat(e.lngLat ?? map.getCenter());
    actualizarPopup(feature, "municipios");
    popup.addTo(map);
    suppressPopupClose = false;
  };

  const mouseleaveMunicipios = () => {
    map.getCanvas().style.cursor = "";
    if (!locked) limpiarInteraccion();
  };

  const clickMunicipios = (e) => {
    const feature = e.features?.[0];
    if (!feature) return;
    locked = true;
    map.__activePopupFeature = feature;
    map.__activePopupSource = "municipios";
    resaltarFeature(map, "municipios", feature);
    suppressPopupClose = true;
    popup.setLngLat(e.lngLat ?? map.getCenter());
    actualizarPopup(feature, "municipios");
    popup.addTo(map);
    suppressPopupClose = false;
  };

  const mousemoveRecintos = (e) => {
    if (locked) return;
    map.getCanvas().style.cursor = "pointer";
    const feature = e.features?.[0];
    if (!feature) return;
    if (sameHoverTarget(feature, "recintos")) return;
    map.__activePopupFeature = feature;
    map.__activePopupSource = "recintos";
    resaltarFeature(map, "recintos", feature);
    suppressPopupClose = true;
    popup.setLngLat(feature.geometry.coordinates);
    actualizarPopup(feature, "recintos");
    popup.addTo(map);
    suppressPopupClose = false;
  };

  const mouseleaveRecintos = () => {
    map.getCanvas().style.cursor = "";
    if (!locked) limpiarInteraccion();
  };

  const clickRecintos = (e) => {
    const feature = e.features?.[0];
    if (!feature) return;
    locked = true;
    map.__activePopupFeature = feature;
    map.__activePopupSource = "recintos";
    resaltarFeature(map, "recintos", feature);
    suppressPopupClose = true;
    popup.setLngLat(feature.geometry.coordinates);
    actualizarPopup(feature, "recintos");
    popup.addTo(map);
    suppressPopupClose = false;
  };

  const clickAny = (e) => {
    const hit = map.queryRenderedFeatures(e.point, {
      layers: ["recintos_hover", "municipios_hover"],
    }).length;
    if (!hit) limpiarInteraccion();
  };

  const closePopup = () => {
    if (suppressPopupClose) return;
    limpiarInteraccion();
  };

  map.on("mousemove", "municipios_hover", mousemoveMunicipios);
  map.on("mouseleave", "municipios_hover", mouseleaveMunicipios);
  map.on("click", "municipios_hover", clickMunicipios);
  map.on("mousemove", "recintos_hover", mousemoveRecintos);
  map.on("mouseleave", "recintos_hover", mouseleaveRecintos);
  map.on("click", "recintos_hover", clickRecintos);
  map.on("click", clickAny);
  popup.on("close", closePopup);

  const actualizarDepartamento = async () => {
    limpiarInteraccion();
    await aplicarDepartamento(departamentoInput.value, { ajustarVista: true });
  };

  departamentoInput.addEventListener("input", actualizarDepartamento);

  invalidation.then(() => {
    departamentoInput.removeEventListener("input", actualizarDepartamento);
    map.off("mousemove", "municipios_hover", mousemoveMunicipios);
    map.off("mouseleave", "municipios_hover", mouseleaveMunicipios);
    map.off("click", "municipios_hover", clickMunicipios);
    map.off("mousemove", "recintos_hover", mousemoveRecintos);
    map.off("mouseleave", "recintos_hover", mouseleaveRecintos);
    map.off("click", "recintos_hover", clickRecintos);
    map.off("click", clickAny);
    popup.off("close", closePopup);
  });
}
```
