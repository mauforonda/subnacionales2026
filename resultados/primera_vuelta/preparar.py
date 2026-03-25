#!/usr/bin/env python3

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from slugify import slugify

ELECCIONES = {
    "alcalde": {
        "slug": "alcaldesaalcalde",
        "scope": "municipio",
    },
    "gobernador": {
        "slug": "gobernador-a",
        "scope": "departamento",
    },
}
ADMIN = [
    "CodigoProvincia",
    "NombreProvincia",
    "CodigoSeccion",
    "NombreMunicipio",
    "CodigoLocalidad",
    "NombreLocalidad",
    "CodigoRecinto",
    "NombreRecinto",
    "CodigoMesa",
    "NumeroMesa",
]
PARTICIPACION = ["VotoValido", "VotoEmitido", "InscritosHabilitados"]

DEPARTAMENTOS = [
    "Chuquisaca",
    "La Paz",
    "Cochabamba",
    "Oruro",
    "Potosí",
    "Tarija",
    "Santa Cruz",
    "Beni",
    "Pando",
]

BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parent.parent
GEO = REPO_ROOT / "geo" / "2026" / "recintos.gpkg"


def identificar(df, codigo_localidad, codigo_recinto):
    return df[codigo_localidad].astype(str) + "." + df[codigo_recinto].astype(str)


def procesar_recintos():
    recintos = gpd.read_file(GEO)
    recintos["codigo"] = identificar(recintos, "asiento", "recinto")
    recintos["x"] = recintos.geometry.x
    recintos["y"] = recintos.geometry.y
    return recintos.set_index("codigo")[["x", "y"]]


def procesar_validos(path, codigo_depto, scope_por_codigo):
    df = pd.read_csv(path)
    partidos = [col for col in df.columns if col not in ADMIN]
    df["codigo"] = identificar(df, "CodigoLocalidad", "CodigoRecinto")
    df = df.join(scope_por_codigo.rename("scope"), on="codigo")

    resultados_scope = df.groupby("scope")[partidos].sum()
    porcentajes_scope = resultados_scope.div(resultados_scope.sum(axis=1), axis=0)
    ganador_scope = pd.DataFrame(
        {
            "partido_ganador": porcentajes_scope.idxmax(axis=1),
            "porcentaje_ganador": porcentajes_scope.max(axis=1),
        }
    )

    resultados_recinto = df.groupby("codigo")[partidos].sum()
    porcentajes_recinto = resultados_recinto.div(resultados_recinto.sum(axis=1), axis=0)
    scope_recinto = df.groupby("codigo")["scope"].first().reindex(porcentajes_recinto.index)
    partido_por_codigo = ganador_scope["partido_ganador"].reindex(scope_recinto).set_axis(
        porcentajes_recinto.index
    )
    indice_partidos = {partido: i for i, partido in enumerate(porcentajes_recinto.columns)}
    partido_idx = partido_por_codigo.map(indice_partidos)
    porcentaje_ganador = pd.Series(
        porcentajes_recinto.to_numpy()[
            range(len(porcentajes_recinto)),
            partido_idx.to_numpy(),
        ],
        index=porcentajes_recinto.index,
    )
    porcentaje_ganador.rename("ganador", inplace=True)

    return ganador_scope, porcentaje_ganador


def procesar_participacion(path, codigo_depto):
    df = pd.read_csv(path)
    df["codigo"] = identificar(df, "CodigoLocalidad", "CodigoRecinto")

    df["municipio"] = (
        str(codigo_depto)
        + df.CodigoProvincia.astype(str).str.rjust(2, "0")
        + df.CodigoSeccion.astype(str).str.rjust(2, "0")
    )

    recintos_admin = df.groupby("codigo")[["municipio", "NombreRecinto"]].first()
    recintos_admin.columns = ["municipio", "recinto"]

    participacion_agregada = df.groupby("codigo")[PARTICIPACION].sum()
    participacion_agregada["validos"] = (
        participacion_agregada.VotoValido / participacion_agregada.VotoEmitido
    )
    participacion_agregada.rename(
        columns={"InscritosHabilitados": "habilitados"}, inplace=True
    )

    participacion = pd.concat(
        [recintos_admin, participacion_agregada[["validos", "habilitados"]]], axis=1
    )

    municipios = df.groupby("municipio")[["NombreMunicipio"]].first()
    municipios.rename(columns={"NombreMunicipio": "nombre_municipio"}, inplace=True)

    return municipios, participacion


def guardar_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False)


def main():
    municipios_data = {}
    resultados_por_eleccion = {eleccion: {} for eleccion in ELECCIONES}
    recintos = procesar_recintos()

    for i, departamento in enumerate(DEPARTAMENTOS):
        depto_slug = slugify(departamento)
        municipios_depto = None

        for eleccion, config in ELECCIONES.items():
            folder = BASE / depto_slug / config["slug"]
            municipios, participacion = procesar_participacion(
                folder / "participacion.csv", i + 1
            )

            if municipios_depto is None:
                municipios_depto = municipios.copy()
                municipios_depto["departamento"] = departamento
            else:
                municipios_depto = municipios_depto.join(
                    municipios[["nombre_municipio"]].rename(
                        columns={"nombre_municipio": "nombre_municipio_nuevo"}
                    ),
                    how="outer",
                )
                municipios_depto["nombre_municipio"] = municipios_depto[
                    "nombre_municipio"
                ].fillna(municipios_depto.pop("nombre_municipio_nuevo"))
                municipios_depto["departamento"] = municipios_depto[
                    "departamento"
                ].fillna(departamento)

            if config["scope"] == "departamento":
                scope_por_codigo = pd.Series(
                    departamento, index=participacion.index, name="scope"
                )
                ganador_scope, porcentaje_ganador = procesar_validos(
                    folder / "validos.csv", i + 1, scope_por_codigo
                )
                partido_ganador = ganador_scope.loc[departamento, "partido_ganador"]
                for municipio_codigo in municipios_depto.index:
                    municipios_data.setdefault(
                        municipio_codigo,
                        {
                            "nombre_municipio": municipios_depto.loc[
                                municipio_codigo, "nombre_municipio"
                            ],
                            "departamento": departamento,
                        },
                    )[eleccion] = partido_ganador
            else:
                scope_por_codigo = participacion["municipio"]
                ganador_scope, porcentaje_ganador = procesar_validos(
                    folder / "validos.csv", i + 1, scope_por_codigo
                )
                for municipio_codigo, partido_ganador in ganador_scope[
                    "partido_ganador"
                ].items():
                    municipios_data.setdefault(
                        municipio_codigo,
                        {
                            "nombre_municipio": municipios_depto.loc[
                                municipio_codigo, "nombre_municipio"
                            ],
                            "departamento": departamento,
                        },
                    )[eleccion] = partido_ganador

            resultados_eleccion = pd.concat(
                [participacion, porcentaje_ganador, recintos], axis=1
            ).dropna()
            resultados_por_eleccion[eleccion].update(
                resultados_eleccion.to_dict(orient="index")
            )

        for municipio_codigo, row in municipios_depto.to_dict(orient="index").items():
            municipios_data.setdefault(
                municipio_codigo,
                {
                    "nombre_municipio": row["nombre_municipio"],
                    "departamento": row["departamento"],
                },
            )

    guardar_json(BASE / "municipios.json", municipios_data)
    for eleccion, resultados in resultados_por_eleccion.items():
        guardar_json(BASE / f"resultados_{eleccion}.json", resultados)


if __name__ == "__main__":
    main()
