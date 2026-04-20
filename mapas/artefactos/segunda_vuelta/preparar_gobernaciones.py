#!/usr/bin/env python3

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from slugify import slugify

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
DEPARTAMENTOS = {
    "1": "Chuquisaca",
    "4": "Oruro",
    "6": "Tarija",
    "7": "Santa Cruz",
    "8": "Beni",
}
ACTAS_TOTALES = {
    "1": 1758,
    "4": 1679,
    "6": 1766,
    "7": 8962,
    "8": 1347,
}
ARTEFACTOS_DIR = Path(__file__).resolve().parent
REPO_ROOT = ARTEFACTOS_DIR.parent.parent.parent
RESULTADOS_DIR = REPO_ROOT / "resultados" / "segunda_vuelta"
GEO = REPO_ROOT / "geo" / "2026" / "recintos.gpkg"
SALIDA_DIR = ARTEFACTOS_DIR / "gobernaciones"
SALIDA_MANIFIESTO = SALIDA_DIR / "manifiesto.json"
SALIDA_TIMESTAMP = ARTEFACTOS_DIR / "timestamp"
SALIDA_MUNICIPIOS = ARTEFACTOS_DIR / "municipios.json"


def identificar(df, codigo_localidad, codigo_recinto):
    return df[codigo_localidad].astype(str) + "." + df[codigo_recinto].astype(str)


def guardar_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False)


def limpiar_salida():
    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    for path in SALIDA_DIR.glob("*.json"):
        path.unlink()


def cargar_recintos_geo():
    recintos = gpd.read_file(GEO)
    recintos["codigo"] = identificar(recintos, "asiento", "recinto")
    recintos["x"] = recintos.geometry.x
    recintos["y"] = recintos.geometry.y
    return recintos.set_index("codigo")[["geometry", "x", "y"]]


def cargar_participacion(path_participacion, codigo_depto):
    df = pd.read_csv(path_participacion)
    df["codigo"] = identificar(df, "CodigoLocalidad", "CodigoRecinto")
    df["municipio"] = (
        str(codigo_depto)
        + df.CodigoProvincia.astype(str).str.rjust(2, "0")
        + df.CodigoSeccion.astype(str).str.rjust(2, "0")
    )

    admin = df.groupby("codigo")[
        ["NombreRecinto", "NombreMunicipio", "municipio"]
    ].first()
    admin.columns = ["recinto", "municipio_nombre", "municipio_codigo"]

    agregada = df.groupby("codigo")[PARTICIPACION].sum()
    agregada.rename(
        columns={
            "VotoValido": "voto_valido",
            "VotoEmitido": "voto_emitido",
            "InscritosHabilitados": "habilitados",
        },
        inplace=True,
    )
    return pd.concat([admin, agregada], axis=1)


def cargar_validos(path_validos):
    df = pd.read_csv(path_validos)
    partidos = [col for col in df.columns if col not in ADMIN]
    df["codigo"] = identificar(df, "CodigoLocalidad", "CodigoRecinto")
    return df.groupby("codigo")[partidos].sum()


def seleccionar_candidaturas(validos):
    resultados_departamento = validos.sum(axis=0)
    candidaturas = resultados_departamento[
        resultados_departamento.notna()
    ].index.tolist()

    # En segunda vuelta deberían existir solo dos candidaturas; si la fuente
    # conserva columnas extra vacías, las descartamos antes de validar.
    no_vacias = resultados_departamento[resultados_departamento > 0].index.tolist()
    if len(no_vacias) == 2:
        return no_vacias
    if len(candidaturas) == 2:
        return candidaturas
    raise ValueError(
        "Se esperaban exactamente 2 candidaturas en votos válidos y se encontraron "
        f"{len(candidaturas)}: {candidaturas}"
    )


def estimar_centro(recintos_geo):
    geometrias = gpd.GeoSeries(recintos_geo["geometry"])
    union = geometrias.union_all()
    centroid = union.convex_hull.centroid
    return [round(float(centroid.x), 5), round(float(centroid.y), 5)]


def ganador_real(resultados):
    return resultados.sort_values(ascending=False).index[0]


def obtener_insumos_departamento(nombre_depto):
    depto_slug = slugify(nombre_depto)
    folder = RESULTADOS_DIR / depto_slug / "gobernador-a"
    participacion = folder / "participacion.csv"
    validos = folder / "validos.csv"
    if participacion.exists() and validos.exists():
        return folder
    return None


def serializar_resultados(serie_resultados, candidaturas):
    return {
        candidatura: int(serie_resultados.get(candidatura, 0))
        for candidatura in candidaturas
    }


def preparar_municipios(tabla, candidaturas, nombre_depto):
    municipios_admin = tabla.groupby("municipio_codigo")[["municipio_nombre"]].first()
    municipios_admin.rename(
        columns={"municipio_nombre": "nombre_municipio"}, inplace=True
    )

    participacion = tabla.groupby("municipio_codigo")[
        ["voto_valido", "voto_emitido", "habilitados"]
    ].sum()
    resultados = tabla.groupby("municipio_codigo")[candidaturas].sum()

    municipios = {}
    for municipio_codigo in resultados.index:
        resultado = resultados.loc[municipio_codigo]
        total = float(resultado.sum())
        ganador = ganador_real(resultado) if total > 0 else candidaturas[0]
        municipios[municipio_codigo] = {
            "nombre_municipio": municipios_admin.loc[
                municipio_codigo, "nombre_municipio"
            ],
            "departamento": nombre_depto,
            "gobernador": {
                "nombre": ganador,
                "validos": round(
                    float(
                        participacion.loc[municipio_codigo, "voto_valido"]
                        / participacion.loc[municipio_codigo, "voto_emitido"]
                    ),
                    4,
                )
                if participacion.loc[municipio_codigo, "voto_emitido"] > 0
                else 0,
                "habilitados": int(participacion.loc[municipio_codigo, "habilitados"]),
                "ganador": round(float(resultado.max() / total), 4) if total > 0 else 0,
                "resultados": serializar_resultados(resultado, candidaturas),
            },
        }

    return municipios


def preparar_departamento(codigo_depto, nombre_depto, recintos_geo):
    folder = obtener_insumos_departamento(nombre_depto)
    if folder is None:
        return None

    participacion = cargar_participacion(folder / "participacion.csv", codigo_depto)
    validos_raw = cargar_validos(folder / "validos.csv")
    candidaturas = seleccionar_candidaturas(validos_raw)
    validos = validos_raw[candidaturas].copy()

    tabla = participacion.join(validos, how="inner").join(recintos_geo, how="inner")
    tabla = tabla.dropna(subset=["x", "y"])
    if tabla.empty:
        return None

    resultados_departamento = tabla[candidaturas].sum()
    actas_contadas = len(validos_raw.index)
    actas_totales = ACTAS_TOTALES.get(codigo_depto)
    recintos = {}
    for codigo, row in tabla.iterrows():
        resultados_recinto = serializar_resultados(row[candidaturas], candidaturas)
        recintos[codigo] = {
            "habilitados": int(row["habilitados"]),
            "ganador": ganador_real(row[candidaturas]),
            "recinto": row["recinto"],
            "municipio": row["municipio_nombre"],
            "x": round(float(row["x"]), 5),
            "y": round(float(row["y"]), 5),
            "resultados": resultados_recinto,
        }

    manifiesto = {
        "nombre": nombre_depto,
        "center": estimar_centro(tabla),
        "partidos": serializar_resultados(resultados_departamento, candidaturas),
        "ganador": ganador_real(resultados_departamento),
        "completo": round(actas_contadas / actas_totales, 4) if actas_totales else None,
    }

    return manifiesto, recintos


def guardar_timestamp_agregado():
    timestamps = []
    for nombre_departamento in DEPARTAMENTOS.values():
        timestamp_path = RESULTADOS_DIR / slugify(nombre_departamento) / "timestamp"
        if timestamp_path.exists():
            timestamps.append(timestamp_path.read_text().strip())

    SALIDA_TIMESTAMP.parent.mkdir(parents=True, exist_ok=True)
    SALIDA_TIMESTAMP.write_text(f"{max(timestamps)}\n" if timestamps else "")


def main():
    limpiar_salida()
    recintos_geo = cargar_recintos_geo()
    manifiesto = {}
    municipios = {}

    for codigo_depto, nombre_depto in DEPARTAMENTOS.items():
        preparado = preparar_departamento(
            codigo_depto,
            nombre_depto,
            recintos_geo,
        )
        if preparado is None:
            continue

        manifiesto_depto, recintos_depto = preparado
        manifiesto[codigo_depto] = manifiesto_depto
        guardar_json(SALIDA_DIR / f"{codigo_depto}.json", recintos_depto)

        folder = obtener_insumos_departamento(nombre_depto)
        participacion = cargar_participacion(folder / "participacion.csv", codigo_depto)
        validos_raw = cargar_validos(folder / "validos.csv")
        candidaturas = seleccionar_candidaturas(validos_raw)
        validos = validos_raw[candidaturas].copy()
        tabla = participacion.join(validos, how="inner")
        municipios.update(preparar_municipios(tabla, candidaturas, nombre_depto))

    guardar_json(SALIDA_MANIFIESTO, manifiesto)
    guardar_json(SALIDA_MUNICIPIOS, municipios)
    guardar_timestamp_agregado()


if __name__ == "__main__":
    main()
