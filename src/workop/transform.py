"""
Beregninger og estimeringer basert på WorkOp-datasettet.

Bruk:
    from src.workop.transform import legg_til_kalkulerte_kolonner, estimat
    df = legg_til_kalkulerte_kolonner(df_raw)
    est = estimat(df)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Estimeringsparametere — juster etter behov
# ---------------------------------------------------------------------------
KONTORER_PLAN: dict[int, int] = {
    2026: 30,   # anslått antall Nav-kontorer som kjører WorkOp i 2026
    2027: 57,
    2028: 81,
    2029: 105,
}
WORKOP_PER_KONTOR_PER_AAR = 3

# Planlagt totalt antall WorkOps for år som er delvis gjennomført
# Brukes i bootstrap_usikkerhet for å estimere gjenstående arrangementer
PLANLAGT_WORKOP: dict[int, int] = {
    2026: 56,
}


def legg_til_kalkulerte_kolonner(df: pd.DataFrame) -> pd.DataFrame:
    """
    Legger til avledede kolonner i DataFrame-en fra extract_all().

    Nye kolonner:
      - andel_jobb      : fatt_jobb / oppmotte (0.0–1.0)
      - kumulativ_oppmotte: løpende sum oppmøtte (sortert på dato/workop_nr)
      - kumulativ_fatt_jobb: løpende sum fått jobb
    """
    df = df.copy()

    # Andel som fikk jobb
    df["andel_jobb"] = df["fatt_jobb"] / df["oppmotte"]

    # Kumulativ beregning — sortert på dato for korrekt kronologisk rekkefølge
    df = df.sort_values("dato", na_position="last").reset_index(drop=True)
    aktive = df["har_data"]
    df.loc[aktive, "kumulativ_oppmotte"] = df.loc[aktive, "oppmotte"].cumsum()
    df.loc[aktive, "kumulativ_fatt_jobb"] = df.loc[aktive, "fatt_jobb"].cumsum()

    return df


def snitt_fra_data(df: pd.DataFrame) -> dict[str, float]:
    """Beregner historiske snitt fra aktive WorkOps med data."""
    aktive = df[df["har_data"]].copy()
    snitt_oppmotte = aktive["oppmotte"].mean()
    snitt_antall_i_jobb = aktive["fatt_jobb"].mean()
    snitt_andel_jobb = aktive["andel_jobb"].mean() if "andel_jobb" in aktive.columns else (
        (aktive["fatt_jobb"] / aktive["oppmotte"]).mean()
    )
    return {
        "snitt_oppmotte": round(snitt_oppmotte, 1),
        "snitt_antall_i_jobb": round(snitt_antall_i_jobb, 2),
        "snitt_andel_jobb": round(snitt_andel_jobb, 3),
    }


def estimat(
    df: pd.DataFrame,
    kontorer_plan: dict[int, int] | None = None,
    workop_per_kontor: int = WORKOP_PER_KONTOR_PER_AAR,
) -> pd.DataFrame:
    """
    Beregner fremskrivning for 2026–2029 basert på historiske snitt.

    Args:
        df: DataFrame fra extract_all() (med legg_til_kalkulerte_kolonner())
        kontorer_plan: {år: antall_nav_kontorer}. Default: KONTORER_PLAN.
        workop_per_kontor: Antall WorkOp per kontor per år.

    Returnerer:
        DataFrame med kolonner:
          år, antall_kontorer, antall_workop, est_oppmotte, est_fatt_jobb,
          snitt_oppmotte, snitt_andel_jobb, kilde ('historisk' | 'estimat')
    """
    if kontorer_plan is None:
        kontorer_plan = KONTORER_PLAN

    snitt = snitt_fra_data(df)
    snitt_oppmotte = snitt["snitt_oppmotte"]
    snitt_andel_jobb = snitt["snitt_andel_jobb"]

    # Faktiske tall per år (fra historiske data)
    aktive = df[df["har_data"]].copy()
    if "dato" in aktive.columns and aktive["dato"].notna().any():
        aktive["år"] = aktive["dato"].dt.year.astype("Int64")
    else:
        aktive["år"] = pd.NA

    faktisk_per_aar = (
        aktive.groupby("år", dropna=True)
        .agg(
            antall_workop=("workop_nr", "count"),
            est_oppmotte=("oppmotte", "sum"),
            est_fatt_jobb=("fatt_jobb", "sum"),
        )
        .reset_index()
        .rename(columns={"år": "aar"})
    )
    faktisk_per_aar["aar"] = faktisk_per_aar["aar"].astype(int)
    faktisk_per_aar["kilde"] = "historisk"
    faktisk_per_aar["snitt_oppmotte"] = snitt_oppmotte
    faktisk_per_aar["snitt_andel_jobb"] = snitt_andel_jobb
    faktisk_per_aar["antall_kontorer"] = None

    # Fremskrivning per år i kontorer_plan
    rader = []
    for aar, n_kontorer in sorted(kontorer_plan.items()):
        antall_workop = n_kontorer * workop_per_kontor
        est_oppmotte = antall_workop * snitt_oppmotte
        est_fatt_jobb = est_oppmotte * snitt_andel_jobb
        rader.append(
            {
                "aar": aar,
                "antall_kontorer": n_kontorer,
                "antall_workop": antall_workop,
                "est_oppmotte": round(est_oppmotte),
                "est_fatt_jobb": round(est_fatt_jobb),
                "snitt_oppmotte": snitt_oppmotte,
                "snitt_andel_jobb": snitt_andel_jobb,
                "kilde": "estimat",
            }
        )

    estimat_df = pd.DataFrame(rader)

    # Slå sammen, men unngå duplikate historiske år i estimat-lista
    estimat_df_filtered = estimat_df[~estimat_df["aar"].isin(faktisk_per_aar["aar"])]
    result = pd.concat([faktisk_per_aar, estimat_df_filtered], ignore_index=True)
    result = result.sort_values("aar").reset_index(drop=True)

    return result


def bootstrap_usikkerhet(
    df: pd.DataFrame,
    kontorer_plan: dict[int, int] | None = None,
    workop_per_kontor: int = WORKOP_PER_KONTOR_PER_AAR,
    planlagt_workop: dict[int, int] | None = None,
    n_sim: int = 5000,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Bootstrapper usikkerhetsintervall for antall som får jobb per år.

    For hvert fremtidsår med `k` estimerte WorkOps: trekk `k` verdier fra
    historiske fatt_jobb-observasjoner og summer. Gjenta n_sim ganger og beregn
    2.5- og 97.5-persentiler (95 % CI).

    For år som er delvis gjennomført (definert i `planlagt_workop`):
    bootstrapper kun de gjenstående arrangementene og legger dem oppå faktiske tall.

    Returnerer:
        DataFrame med kolonner:
          aar, faktisk_jobb, est_rest, ci_lo, ci_hi, kilde
          kilde: 'historisk' | 'delvis' | 'estimat'
    """
    if kontorer_plan is None:
        kontorer_plan = KONTORER_PLAN
    if planlagt_workop is None:
        planlagt_workop = PLANLAGT_WORKOP

    rng = np.random.default_rng(seed)
    aktive = df[df["har_data"]].copy()
    historiske_jobb = aktive["fatt_jobb"].dropna().values

    # Historiske år — beregnes først for å ekskludere fra estimat-løkken
    if "dato" in aktive.columns and aktive["dato"].notna().any():
        aktive["_aar"] = aktive["dato"].dt.year.fillna(aktive["fallback_year"]).astype(int)
    else:
        aktive["_aar"] = aktive["fallback_year"].astype(int)

    faktisk_grp = (
        aktive.groupby("_aar")
        .agg(faktisk_jobb=("fatt_jobb", "sum"), antall_gjennomfort=("workop_nr", "count"))
        .reset_index()
        .rename(columns={"_aar": "aar"})
    )
    faktisk_grp["aar"] = faktisk_grp["aar"].astype(int)
    historiske_aar = set(faktisk_grp["aar"].tolist())

    rader = []

    # Rene historiske år (ingen gjenværende planlagte)
    for _, row in faktisk_grp.iterrows():
        aar = int(row["aar"])
        if aar in planlagt_workop:
            gjennomfort = int(row["antall_gjennomfort"])
            planlagt = planlagt_workop[aar]
            gjenstaaende = max(0, planlagt - gjennomfort)
            if gjenstaaende > 0:
                totaler = (
                    row["faktisk_jobb"]
                    + rng.choice(historiske_jobb, size=(n_sim, gjenstaaende), replace=True).sum(axis=1)
                )
                rader.append({
                    "aar": aar,
                    "faktisk_jobb": float(row["faktisk_jobb"]),
                    "est_rest": float(totaler.mean()) - float(row["faktisk_jobb"]),
                    "ci_lo": float(np.percentile(totaler, 2.5)),
                    "ci_hi": float(np.percentile(totaler, 97.5)),
                    "kilde": "delvis",
                })
            else:
                rader.append({
                    "aar": aar,
                    "faktisk_jobb": float(row["faktisk_jobb"]),
                    "est_rest": 0.0,
                    "ci_lo": float("nan"),
                    "ci_hi": float("nan"),
                    "kilde": "historisk",
                })
        else:
            rader.append({
                "aar": aar,
                "faktisk_jobb": float(row["faktisk_jobb"]),
                "est_rest": 0.0,
                "ci_lo": float("nan"),
                "ci_hi": float("nan"),
                "kilde": "historisk",
            })

    # Rene fremtidsår
    for aar, n_kontorer in sorted(kontorer_plan.items()):
        if aar in historiske_aar:
            continue
        k = n_kontorer * workop_per_kontor
        totaler = rng.choice(historiske_jobb, size=(n_sim, k), replace=True).sum(axis=1)
        rader.append({
            "aar": aar,
            "faktisk_jobb": 0.0,
            "est_rest": float(totaler.mean()),
            "ci_lo": float(np.percentile(totaler, 2.5)),
            "ci_hi": float(np.percentile(totaler, 97.5)),
            "kilde": "estimat",
        })

    result = pd.DataFrame(rader).sort_values("aar").reset_index(drop=True)
    result["est_jobb"] = result["faktisk_jobb"] + result["est_rest"]
    return result
