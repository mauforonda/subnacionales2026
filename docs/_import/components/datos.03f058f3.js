import * as d3 from "../../_npm/d3@7.9.0/66d82917.js";

export async function cargarDatos(base, archivoResultados) {
  const [resultadosRaw, municipios, departamentos, territoriosRaw, timestampRaw] =
    await Promise.all([
    d3.json(`${base}${archivoResultados}`),
    d3.json(`${base}municipios.json`),
    d3.json(`${base}departamentos.json`),
    d3.json(`${base}municipios.geojson`),
    d3.text(`${base}timestamp`),
    ]);

  return {
    resultadosRaw,
    municipios,
    departamentos,
    territoriosRaw,
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
  return crearRecintosConDepartamentos(resultadosRaw, municipios, {}, eleccion);
}

export function crearRecintosConDepartamentos(
  resultadosRaw,
  municipios,
  departamentos,
  eleccion,
) {
  return {
    type: "FeatureCollection",
    features: Object.entries(resultadosRaw)
      .map(([codigo, value]) => {
        const municipio = municipios[value.municipio] ?? null;
        const departamento = municipio?.departamento ?? null;
        const departamentoCodigo = normalizarDepartamentoCodigo(value.municipio);
        const partidoGanador =
          eleccion === "alcalde"
            ? municipio?.alcalde?.nombre ?? null
            : departamentos[departamentoCodigo]?.gobernador?.nombre ?? null;
        return {
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [+value.x, +value.y],
          },
          properties: {
            codigo,
            nivel: "recinto",
            municipio_codigo: value.municipio,
            departamento_codigo: departamentoCodigo,
            municipio_nombre: municipio?.nombre_municipio ?? null,
            departamento,
            recinto: value.recinto,
            habilitados: +value.habilitados || 0,
            validos: +value.validos,
            invalido: 1 - +value.validos,
            ganador: +value.ganador,
            partido_ganador_scope: partidoGanador,
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

export function crearTerritorios(territoriosRaw, municipios, departamentos, eleccion) {
  return {
    type: "FeatureCollection",
    features: territoriosRaw.features
      .map((feature) => {
        const municipioCodigo = normalizarMunicipioCodigo(
          feature.properties?.municipio,
        );
        const departamentoCodigo = `${feature.properties?.departamento ?? ""}`;
        const municipio = municipios[municipioCodigo] ?? null;
        const departamento = departamentos[departamentoCodigo] ?? null;
        const agregado =
          eleccion === "alcalde"
            ? municipio?.alcalde ?? null
            : departamento?.gobernador ?? null;
        const nombreTerritorio =
          eleccion === "alcalde"
            ? municipio?.nombre_municipio ?? null
            : departamento?.nombre_departamento ?? null;
        const nombreDepartamento =
          eleccion === "alcalde"
            ? municipio?.departamento ?? null
            : departamento?.nombre_departamento ?? null;

        return {
          type: "Feature",
          geometry: feature.geometry,
          properties: {
            municipio_codigo: municipioCodigo,
            departamento_codigo: departamentoCodigo,
            nivel: eleccion === "alcalde" ? "municipio" : "departamento",
            nombre_territorio: nombreTerritorio,
            municipio_nombre: eleccion === "alcalde" ? municipio?.nombre_municipio : null,
            departamento: nombreDepartamento,
            habilitados: agregado?.habilitados ?? null,
            validos: agregado?.validos ?? null,
            invalido:
              agregado?.validos != null ? 1 - Number(agregado.validos) : null,
            ganador: agregado?.ganador ?? null,
            partido_ganador_scope: agregado?.nombre ?? null,
          },
        };
      })
      .filter((feature) => feature.properties.nombre_territorio != null),
  };
}

function normalizarMunicipioCodigo(value) {
  return `${value ?? ""}`.replace(/^0+/, "");
}

function normalizarDepartamentoCodigo(municipioCodigo) {
  return normalizarMunicipioCodigo(municipioCodigo).slice(0, 1);
}
