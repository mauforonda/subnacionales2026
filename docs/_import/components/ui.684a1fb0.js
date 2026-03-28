import * as d3 from "../../_npm/d3@7.9.0/66d82917.js";
import * as Plot from "../../_npm/@observablehq/plot@0.6.17/a96a6bbb.js";

export function popupHTML(feature, metrica) {
  const p = feature.properties ?? {};
  const valor = p[metrica.campo];
  const color = d3
    .scaleLinear()
    .domain([
      metrica.dominio[0],
      (metrica.dominio[0] + metrica.dominio[1]) / 2,
      metrica.dominio[1],
    ])
    .range(metrica.colores)
    .clamp(true)(valor ?? metrica.dominio[0]);
  const detalle =
    metrica.campo === "invalido"
      ? 'de <span class="popup__metric_emphasis">blancos o nulos</span>'
      : `a <span class="popup__metric_emphasis">${p.partido_ganador_scope ?? "la opcion ganadora"}</span>`;
  const titulo =
    p.nivel === "recinto"
      ? p.recinto ?? "Recinto sin nombre"
      : p.nombre_territorio ?? "Territorio sin nombre";
  const placeHTML =
    p.nivel === "departamento"
      ? `<div class="popup__place">
          <div class="popup__municipio">${p.departamento ?? "s/d"}</div>
        </div>`
      : `<div class="popup__place">
          <div class="popup__municipio">${p.municipio_nombre ?? "s/d"}</div>
          <div class="popup__departamento">${p.departamento ?? "s/d"}</div>
        </div>`;

  return `
    <div class="popup" style="--popup-accent:${color}">
      <div class="popup__title">${titulo}</div>
      <div class="popup__subtitle">${d3.format(",")(p.habilitados ?? 0)} votantes habilitados</div>
      <div class="popup__metric">
        <div class="popup__metric_value">${d3.format(".0%")(valor ?? 0)}</div>
        <div class="popup__metric_label">${detalle}</div>
      </div>
      ${placeHTML}
    </div>
  `;
}

export function renderizarLeyenda(metrica) {
  const description = document.querySelector("#legend-description");
  const container = document.querySelector("#legend-container");
  if (!description || !container) return;

  description.textContent = metrica.descripcion;
  container.replaceChildren(
    Plot.legend({
      margin: 0,
      width: 260,
      height: 46,
      className: "leyenda",
      color: {
        type: "linear",
        domain: metrica.dominio,
        range: metrica.colores,
        ticks: metrica.ticks,
        tickFormat: metrica.format,
      },
    })
  );
}
