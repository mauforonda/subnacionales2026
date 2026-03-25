---
theme: dashboard
title: Subnacionales 2026
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

```js
import maplibregl from "npm:maplibre-gl";
import {
  DATA_BASE,
  MAPA_FALLBACK,
  STORAGE_ELECCION_KEY,
  STORAGE_KEY,
  STORAGE_MAP_KEY,
  elecciones,
  getStorage,
  metricas,
} from "./components/definiciones.js";
import { cargarDatos, crearRecintos } from "./components/datos.js";
import {
  aplicarMetricaMapa,
  crearCapasBase,
  crearMapa,
  leerMapaInicial,
  persistirMapa,
} from "./components/mapa.js";
import { popupHTML, renderizarLeyenda } from "./components/ui.js";
```

```js
const storage = getStorage();
const metricaInicial = storage?.getItem(STORAGE_KEY) ?? "invalido";
const eleccionInicial = storage?.getItem(STORAGE_ELECCION_KEY) ?? "gobernador";
const metricaInput = Inputs.radio(Object.keys(metricas), {
  value: metricas[metricaInicial] ? metricaInicial : "invalido",
  format: (d) => metricas[d].nombre,
  label: null,
});
const eleccionInput = Inputs.select(Object.keys(elecciones), {
  value: elecciones[eleccionInicial] ? eleccionInicial : "gobernador",
  format: (d) => elecciones[d].nombre,
  label: null,
});
const metrica = Generators.input(metricaInput);
const eleccion = Generators.input(eleccionInput);

function obtenerMetricaActual() {
  return metricas[metricaInput.value] ?? metricas.invalido;
}

function obtenerEleccionActual() {
  return elecciones[eleccionInput.value] ?? elecciones.gobernador;
}
```

<div class="app">
  <header class="header">
    <div class="header__eyebrow">Elecciones subnacionales 2026</div>
    <div class="header__subtitle">Votos a <span class="header__eleccion">${eleccionInput}</span> por recinto a nivel nacional</div>
    <div class="header__timestamp" id="timestamp-container"></div>
    <div class="header__controls">
      <div class="control control--legend">
        <div class="control__input">${metricaInput}</div>
        <div class="control__description" id="legend-description"></div>
        <div id="legend-container"></div>
      </div>
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
const { resultadosRaw, municipios, timestamp } = await cargarDatos(
  DATA_BASE,
  obtenerEleccionActual().archivo,
);
const recintos = crearRecintos(resultadosRaw, municipios, eleccionInput.value);
const mapaInicial = leerMapaInicial(storage, STORAGE_MAP_KEY, MAPA_FALLBACK);
```

```js
{
  const container = document.querySelector("#timestamp-container");
  container.textContent = timestamp
    ? `actualizado el ${timestamp.fecha} a las ${timestamp.hora}`
    : "";
}
```

```js
const map = crearMapa("#mapa", mapaInicial);
const popup = new maplibregl.Popup({
  closeButton: false,
  closeOnClick: false,
});

persistirMapa(map, storage, STORAGE_MAP_KEY);

invalidation.then(() => {
  popup.remove();
  map.remove();
});
```

```js
const ready = new Promise((resolve) => {
  map.on("load", () => {
    crearCapasBase(map, recintos, metricas.invalido);
    resolve();
  });
});
```

```js
{
  await ready;
  renderizarLeyenda(obtenerMetricaActual());
  aplicarMetricaMapa(map, obtenerMetricaActual());
}
```

```js
{
  await ready;
  const actualizar = () => {
    const metricaSiguiente = obtenerMetricaActual();
    if (storage) storage.setItem(STORAGE_KEY, metricaInput.value);
    renderizarLeyenda(metricaSiguiente);
    aplicarMetricaMapa(map, metricaSiguiente);
  };
  metricaInput.addEventListener("input", actualizar);
  invalidation.then(() =>
    metricaInput.removeEventListener("input", actualizar),
  );
}
```

```js
{
  await ready;
  const actualizarEleccion = async () => {
    const eleccionSiguiente = obtenerEleccionActual();
    if (storage) storage.setItem(STORAGE_ELECCION_KEY, eleccionInput.value);
    const { resultadosRaw, municipios, timestamp } = await cargarDatos(
      DATA_BASE,
      eleccionSiguiente.archivo,
    );
    const recintosNuevos = crearRecintos(
      resultadosRaw,
      municipios,
      eleccionInput.value,
    );
    map.getSource("recintos")?.setData(recintosNuevos);
    const container = document.querySelector("#timestamp-container");
    container.textContent = timestamp
      ? `actualizado el ${timestamp.fecha} a las ${timestamp.hora}`
      : "";
  };
  eleccionInput.addEventListener("input", actualizarEleccion);
  invalidation.then(() =>
    eleccionInput.removeEventListener("input", actualizarEleccion),
  );
}
```

```js
let locked = false;

{
  await ready;

  if (map.__hoverHandlers) {
    const { mouseenter, mouseleave, clickIn, clickAny } = map.__hoverHandlers;
    map.off("mouseenter", "recintos_hover", mouseenter);
    map.off("mouseleave", "recintos_hover", mouseleave);
    map.off("click", "recintos_hover", clickIn);
    map.off("click", clickAny);
  }

  const mouseenter = (e) => {
    map.getCanvas().style.cursor = "pointer";
    const feature = e.features?.[0];
    if (!feature) return;

    popup
      .setLngLat(feature.geometry.coordinates)
      .setHTML(popupHTML(feature, obtenerMetricaActual()))
      .addTo(map);
  };

  const mouseleave = () => {
    map.getCanvas().style.cursor = "";
    if (!locked) popup.remove();
  };

  const clickIn = () => {
    locked = true;
  };

  const clickAny = (e) => {
    const hit = map.queryRenderedFeatures(e.point, {
      layers: ["recintos_hover"],
    }).length;
    if (!hit) {
      locked = false;
      popup.remove();
    }
  };

  map.on("mouseenter", "recintos_hover", mouseenter);
  map.on("mouseleave", "recintos_hover", mouseleave);
  map.on("click", "recintos_hover", clickIn);
  map.on("click", clickAny);

  map.__hoverHandlers = { mouseenter, mouseleave, clickIn, clickAny };
}
```
