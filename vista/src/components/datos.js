import * as d3 from "npm:d3";

export async function cargarDatos(base, archivoResultados) {
  const [resultadosRaw, municipios, timestampRaw] = await Promise.all([
    d3.json(`${base}${archivoResultados}`),
    d3.json(`${base}municipios.json`),
    d3.text(`${base}timestamp`),
  ]);

  return {
    resultadosRaw,
    municipios,
    timestamp: formatearTimestamp(timestampRaw),
  };
}

function formatearTimestamp(timestampRaw) {
  const timestamp = timestampRaw?.trim();
  if (!timestamp) return null;

  const [fecha, hora] = timestamp.split(" ");
  if (!fecha || !hora) return null;

  const [year, month, day] = fecha.split("-");
  const [hours, minutes] = hora.split(":");
  if (!year || !month || !day || !hours || !minutes) return null;

  return {
    fecha: `${day}/${month}/${year}`,
    hora: `${hours}:${minutes}`,
  };
}

export function crearRecintos(resultadosRaw, municipios, eleccion) {
  return {
    type: "FeatureCollection",
    features: Object.entries(resultadosRaw)
      .map(([codigo, value]) => {
        const municipio = municipios[value.municipio] ?? null;
        const departamento = municipio?.departamento ?? null;
        return {
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [+value.x, +value.y],
          },
          properties: {
            codigo,
            municipio_codigo: value.municipio,
            municipio_nombre: municipio?.nombre_municipio ?? null,
            departamento,
            recinto: value.recinto,
            habilitados: +value.habilitados || 0,
            validos: +value.validos,
            invalido: 1 - +value.validos,
            ganador: +value.ganador,
            partido_ganador_scope: municipio?.[eleccion] ?? null,
          },
        };
      })
      .filter(
        (feature) =>
          Number.isFinite(feature.geometry.coordinates[0]) &&
          Number.isFinite(feature.geometry.coordinates[1])
      ),
  };
}
