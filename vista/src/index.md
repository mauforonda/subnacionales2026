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
import {
  cargarDatos,
  crearRecintosConDepartamentos,
  crearTerritorios,
} from "./components/datos.js";
import {
  aplicarMetricaMapa,
  limpiarResaltado,
  crearCapasBase,
  crearMapa,
  leerMapaInicial,
  persistirMapa,
  resaltarFeature,
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
    <div class="header__subtitle">Votos para <span class="header__eleccion">${eleccionInput}</span></div>
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
const { resultadosRaw, municipios, departamentos, territoriosRaw, timestamp } =
  await cargarDatos(
  DATA_BASE,
  obtenerEleccionActual().archivo,
);
const recintos = crearRecintosConDepartamentos(
  resultadosRaw,
  municipios,
  departamentos,
  eleccionInput.value,
);
const territorios = crearTerritorios(
  territoriosRaw,
  municipios,
  departamentos,
  eleccionInput.value,
);
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
const ready = new Promise((resolve) => {
  map.on("load", () => {
    crearCapasBase(map, territorios, recintos, metricas.invalido);
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
    if (map.__activePopupFeature) {
      popup.setHTML(popupHTML(map.__activePopupFeature, metricaSiguiente));
      resaltarFeature(
        map,
        map.__activePopupFeature.properties.nivel === "recinto"
          ? "recintos"
          : "territorios",
        map.__activePopupFeature,
      );
    }
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
  let eleccionRequestId = 0;
  const actualizarEleccion = async () => {
    eleccionRequestId += 1;
    const requestId = eleccionRequestId;
    const eleccionSiguiente = obtenerEleccionActual();
    if (storage) storage.setItem(STORAGE_ELECCION_KEY, eleccionInput.value);
    const {
      resultadosRaw,
      municipios,
      departamentos,
      territoriosRaw,
      timestamp,
    } = await cargarDatos(
      DATA_BASE,
      eleccionSiguiente.archivo,
    );
    if (requestId !== eleccionRequestId) return;
    const recintosNuevos = crearRecintosConDepartamentos(
      resultadosRaw,
      municipios,
      departamentos,
      eleccionInput.value,
    );
    const territoriosNuevos = crearTerritorios(
      territoriosRaw,
      municipios,
      departamentos,
      eleccionInput.value,
    );
    limpiarResaltado(map);
    map.__activePopupFeature = null;
    map.getSource("recintos")?.setData(recintosNuevos);
    map.getSource("territorios")?.setData(territoriosNuevos);
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
  let suppressPopupClose = false;

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

  if (map.__hoverHandlers) {
    const {
      mousemoveRecintos,
      mouseleaveRecintos,
      clickRecintos,
      mousemoveTerritorios,
      mouseleaveTerritorios,
      clickTerritorios,
      clickAny,
      closePopup,
    } = map.__hoverHandlers;
    map.off("mousemove", "recintos_hover", mousemoveRecintos);
    map.off("mouseleave", "recintos_hover", mouseleaveRecintos);
    map.off("click", "recintos_hover", clickRecintos);
    map.off("mousemove", "territorios_hover", mousemoveTerritorios);
    map.off("mouseleave", "territorios_hover", mouseleaveTerritorios);
    map.off("click", "territorios_hover", clickTerritorios);
    map.off("click", clickAny);
    popup.off("close", closePopup);
  }

  const sameHoverTarget = (feature, source) => {
    if (map.__activePopupSource !== source) return false;
    if (source === "territorios") {
      return (
        (map.__activePopupFeature?.id ??
          map.__activePopupFeature?.properties?.feature_id) ===
        (feature?.id ?? feature?.properties?.feature_id)
      );
    }
    return (
      map.__activePopupFeature?.properties?.codigo_hover ===
      feature?.properties?.codigo_hover
    );
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
    popup
      .setLngLat(feature.geometry.coordinates)
      .setHTML(popupHTML(feature, obtenerMetricaActual()))
      .addTo(map);
    suppressPopupClose = false;
    actualizarInteractividadPopup();
  };

  const mouseleaveRecintos = () => {
    map.getCanvas().style.cursor = "";
    if (!locked) {
      limpiarInteraccion();
    }
  };

  const clickRecintos = (e) => {
    const feature = e.features?.[0];
    if (!feature) return;
    locked = true;
    map.__activePopupFeature = feature;
    map.__activePopupSource = "recintos";
    resaltarFeature(map, "recintos", feature);
    suppressPopupClose = true;
    popup
      .setLngLat(feature.geometry.coordinates)
      .setHTML(popupHTML(feature, obtenerMetricaActual()))
      .addTo(map);
    suppressPopupClose = false;
    actualizarInteractividadPopup();
  };

  const mousemoveTerritorios = (e) => {
    if (locked) return;
    map.getCanvas().style.cursor = "pointer";
    const feature = e.features?.[0];
    if (!feature) return;
    if (sameHoverTarget(feature, "territorios")) {
      popup.setLngLat(e.lngLat ?? map.getCenter());
      return;
    }
    map.__activePopupFeature = feature;
    map.__activePopupSource = "territorios";
    resaltarFeature(map, "territorios", feature);
    suppressPopupClose = true;
    popup
      .setLngLat(e.lngLat ?? map.getCenter())
      .setHTML(popupHTML(feature, obtenerMetricaActual()))
      .addTo(map);
    suppressPopupClose = false;
    actualizarInteractividadPopup();
  };

  const mouseleaveTerritorios = () => {
    map.getCanvas().style.cursor = "";
    if (!locked) {
      limpiarInteraccion();
    }
  };

  const clickTerritorios = (e) => {
    const feature = e.features?.[0];
    if (!feature) return;
    locked = true;
    map.__activePopupFeature = feature;
    map.__activePopupSource = "territorios";
    resaltarFeature(map, "territorios", feature);
    suppressPopupClose = true;
    popup
      .setLngLat(e.lngLat ?? map.getCenter())
      .setHTML(popupHTML(feature, obtenerMetricaActual()))
      .addTo(map);
    suppressPopupClose = false;
    actualizarInteractividadPopup();
  };

  const clickAny = (e) => {
    const hit = map.queryRenderedFeatures(e.point, {
      layers: ["recintos_hover", "territorios_hover"],
    }).length;
    if (!hit) {
      limpiarInteraccion();
    }
  };

  const closePopup = () => {
    if (suppressPopupClose) return;
    limpiarInteraccion();
  };

  map.on("mousemove", "recintos_hover", mousemoveRecintos);
  map.on("mouseleave", "recintos_hover", mouseleaveRecintos);
  map.on("click", "recintos_hover", clickRecintos);
  map.on("mousemove", "territorios_hover", mousemoveTerritorios);
  map.on("mouseleave", "territorios_hover", mouseleaveTerritorios);
  map.on("click", "territorios_hover", clickTerritorios);
  map.on("click", clickAny);
  popup.on("close", closePopup);

  map.__hoverHandlers = {
    mousemoveRecintos,
    mouseleaveRecintos,
    clickRecintos,
    mousemoveTerritorios,
    mouseleaveTerritorios,
    clickTerritorios,
    clickAny,
    closePopup,
  };
}
```
