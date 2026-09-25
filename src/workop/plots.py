"""
Plotly-figurer for WorkOp-visualiseringer.

Alle funksjoner returnerer et plotly.graph_objects.Figure-objekt
som kan vises i Quarto (.qmd) eller notebook.

Bruk:
    from src.workop.plots import (
        fig_deltakere_jobb_tid,
        fig_kumulativ,
        fig_bransje,
        fig_bedriftsstorrelse,
        fig_jobb_usikkerhet,
    )
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.workop.kontorer import unike_kontorer

_REPO_ROOT = Path(__file__).resolve().parents[2]
_palett_raw = json.loads((_REPO_ROOT / "palett.json").read_text())
PALETT = {k: v["hex"] for k, v in _palett_raw.items()}


def _rgba(hex_color: str, alpha: float) -> str:
    """Konverter hex til rgba-streng for Plotly."""
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def antall_unike_kontorer(df: pd.DataFrame) -> tuple[int, int]:
    """
    Returnerer (antall lokasjoner, antall faktiske Nav-kontorer).

    Teller gjennomførte arrangementer, ikke bare de med resultat — et kontor har
    arrangert WorkOp selv om Forms 2 ikke er besvart ennå.

    Kontorene telles som et sett, ikke som en sum per lokasjon. Et kontor kan ha
    arrangert både alene og sammen med naboene, og skal da telles én gang.
    """
    aktive = df[df["har_gjennomforing"]]
    lokasjoner = aktive["nav_kontor"].dropna().unique().tolist()
    return len(lokasjoner), len(unike_kontorer(lokasjoner))


def tabell_per_fylke(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregert tabell per fylke, sortert på antall som fikk jobb.

    Arrangementer telles på `har_gjennomforing`, mens oppmøtte, jobbtall og
    andel regnes på `har_data`. Et fylke kan derfor ha flere arrangementer enn
    det har resultater for — kolonnen «Med resultat» viser forskjellen.
    """
    gjennomfort = df[df["har_gjennomforing"] & df["fylke"].notna()]

    antall = gjennomfort.groupby("fylke")["workop_nr"].count()
    med_resultat = df[df["har_data"] & df["fylke"].notna()].groupby("fylke")
    summer = med_resultat.agg(
        med_resultat=("workop_nr", "count"),
        oppmotte=("oppmotte", "sum"),
        fatt_jobb=("fatt_jobb", "sum"),
    )

    grp = pd.concat([antall.rename("antall_workop"), summer], axis=1).fillna(0)
    heltall = ["antall_workop", "med_resultat", "oppmotte", "fatt_jobb"]
    grp[heltall] = grp[heltall].astype(int)
    grp["andel"] = (grp["fatt_jobb"] / grp["oppmotte"] * 100).round(1)
    grp = grp.sort_values("fatt_jobb", ascending=False).reset_index()

    grp.columns = [
        "Fylke", "Arrangementer", "Med resultat", "Oppmøtte", "Fått jobb", "Andel (%)",
    ]
    return grp


def fig_fylke_sammenlikning(df: pd.DataFrame, fylker: list[str] | None = None) -> go.Figure:
    """
    Liggende søyler per fylke: oppmøtte mot antall som fikk jobb.

    Args:
        df: datasettet med `fylke`-kolonne fra transform.
        fylker: begrens til et utvalg fylker. None betyr alle.

    Sortert med flest i jobb øverst. Bare arrangementer med resultat teller,
    siden figuren viser jobbtall.
    """
    tabell = tabell_per_fylke(df)
    if fylker:
        tabell = tabell[tabell["Fylke"].isin(fylker)]
    tabell = tabell.sort_values("Fått jobb")  # stigende → flest øverst

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=tabell["Oppmøtte"],
            y=tabell["Fylke"],
            orientation="h",
            name="Oppmøtte",
            marker_color=FARGE_OPPMOTTE,
            hovertemplate="%{y}<br>Oppmøtte: %{x}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=tabell["Fått jobb"],
            y=tabell["Fylke"],
            orientation="h",
            name="Fikk jobb",
            marker_color=FARGE_JOBB,
            customdata=tabell["Andel (%)"],
            text=[f"{a:.0f} %" for a in tabell["Andel (%)"]],
            textposition="outside",
            textfont_size=11,
            cliponaxis=False,
            hovertemplate="%{y}<br>Fikk jobb: %{x} (%{customdata} %)<extra></extra>",
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Oppmøtte og antall som fikk jobb per fylke",
        xaxis_title="Antall personer",
        yaxis_title=None,
        barmode="group",
        legend=_LEGEND_BUNN,
        margin={"t": 70, "b": 80, "l": 160, "r": 70},
        height=max(380, len(tabell) * 58 + 140),
        xaxis_range=[0, tabell["Oppmøtte"].max() * 1.08],
    )
    return fig


def fig_fylke_andel(df: pd.DataFrame) -> go.Figure:
    """
    Liggende søyler: andel av de oppmøtte som fikk jobb, per fylke.

    Sortert med høyest andel øverst, og med en stiplet linje for landssnittet.
    Andeler fra fylker med få arrangementer svinger mye, så antall arrangementer
    ligger i hover-teksten som kontekst.
    """
    tabell = tabell_per_fylke(df).sort_values("Andel (%)")  # stigende → høyest øverst

    aktive = df[df["har_data"]]
    landssnitt = aktive["fatt_jobb"].sum() / aktive["oppmotte"].sum() * 100

    fig = go.Figure(
        go.Bar(
            x=tabell["Andel (%)"],
            y=tabell["Fylke"],
            orientation="h",
            marker_color=FARGE_JOBB,
            text=[f"{a:.0f} %" for a in tabell["Andel (%)"]],
            textposition="outside",
            customdata=tabell[["Fått jobb", "Oppmøtte", "Med resultat"]].values,
            hovertemplate=(
                "%{y}<br>"
                "Andel: %{x:.1f} %<br>"
                "%{customdata[0]} av %{customdata[1]} oppmøtte<br>"
                "Bygger på %{customdata[2]} arrangementer<extra></extra>"
            ),
        )
    )
    fig.add_vline(
        x=landssnitt,
        line_dash="dash",
        line_color=PALETT["Lilla"],
        line_width=2,
        annotation_text=f"Hele landet: {landssnitt:.0f} %",
        annotation_position="top right",
        annotation_font_size=13,
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Andel av de oppmøtte som fikk jobb, per fylke",
        xaxis_title="Andel som fikk jobb (%)",
        yaxis_title=None,
        showlegend=False,
        margin={"t": 70, "b": 50, "l": 170, "r": 70},
        height=max(380, len(tabell) * 44 + 140),
        xaxis_range=[0, max(tabell["Andel (%)"].max(), landssnitt) * 1.18],
    )
    return fig


def tabell_per_kontor(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregert tabell: Nav-kontor | Antall WOs | Oppmøtte | Fått jobb | Andel."""
    aktive = df[df["har_data"]].copy()
    med_kontor = aktive[aktive["nav_kontor"].notna()]
    grp = (
        med_kontor.groupby("nav_kontor")
        .agg(
            antall_workop=("workop_nr", "count"),
            oppmotte=("oppmotte", "sum"),
            fatt_jobb=("fatt_jobb", "sum"),
        )
        .reset_index()
    )
    grp["andel"] = (grp["fatt_jobb"] / grp["oppmotte"] * 100).round(1)
    grp = grp.sort_values("fatt_jobb", ascending=False).reset_index(drop=True)
    grp.columns = ["Lokasjon", "Antall WorkOp", "Oppmøtte", "Fått jobb", "Andel (%)"]
    return grp


# ---------------------------------------------------------------------------
# Fargepalett (Nav Ung — se palett.json og README)
# ---------------------------------------------------------------------------
FARGE_OPPMOTTE = PALETT["Mellom Grønn"]
FARGE_JOBB = PALETT["Mellom Blå"]
FARGE_ESTIMAT = PALETT["Mellom Lilla"]
FARGE_OPPMOTTE_STERK = PALETT["Grønn"]
FARGE_JOBB_STERK = PALETT["Blå"]

FARGE_NEDSATT = PALETT["Mellom Blå"]
FARGE_VEILEDNING = PALETT["Mellom Lilla"]
FARGE_GODE = PALETT["Mellom Turkis"]

PLOTLY_TEMPLATE = "plotly_white"

# Legend nederst og toppmargin for lang tittel — unngår overlapp med Plotly-toolbar
_LEGEND_BUNN = {"orientation": "h", "yanchor": "top", "y": -0.18, "xanchor": "center", "x": 0.5}
_MARGIN = {"t": 70, "b": 80}
_FARGE_UKJENT = "#AAAAAA"


def figurtekst(
    beskrivelse: str,
    df: pd.DataFrame | None = None,
    *,
    antall: int | None = None,
) -> str:
    """
    Lager hjelpeteksten som står under et plott.

    Teksten skal si kort hva figuren viser, i vanlig språk, og hvor mange
    arrangementer tallene bygger på. Den rendres som vanlig HTML og ikke som en
    del av bildet, slik at skjermlesere får den med.

    Args:
        beskrivelse: Én setning om hva figuren viser. Avsluttes med punktum.
        df: DataFrame — antall hentes fra `har_data` når `antall` ikke er satt.
        antall: Overstyrer antallet, for figurer med et annet datagrunnlag.

    Returnerer:
        HTML-streng som kan sendes rett til `display(HTML(...))`.
    """
    if antall is None:
        if df is None:
            raise ValueError("figurtekst() trenger enten df eller antall")
        antall = int(df["har_data"].sum())

    arrangement = "arrangement" if antall == 1 else "arrangementer"

    return (
        '<p style="color:#555; font-size:0.8rem; font-style:italic; margin:-0.1rem 0 1.5rem 0;">'
        f"{beskrivelse} Tall fra {antall} WorkOp-{arrangement}."
        "</p>"
    )


def _beregn_innsatsgrupper(df: pd.DataFrame) -> tuple[list[str], list[float], list[str], int]:
    """Felles beregning av innsatsgruppe-verdier for gjenbruk i flere plott."""
    aktive = df[df["har_data"]].copy()

    nedsatt = aktive["fatt_jobb_nedsatt"].sum()
    veiledning = aktive["fatt_jobb_veiledning"].sum()
    gode = aktive["fatt_jobb_gode"].sum()
    kjent_sum = aktive[["fatt_jobb_nedsatt", "fatt_jobb_veiledning", "fatt_jobb_gode"]].sum(axis=1)
    ukjent = (aktive["fatt_jobb"] - kjent_sum).clip(lower=0).sum()
    totalt = int(aktive["fatt_jobb"].sum())

    kategorier = ["Trenger veiledning", "Nedsatt arbeidsevne", "Gode muligheter", "Ukjent"]
    verdier = [veiledning, nedsatt, gode, ukjent]
    farger = [FARGE_VEILEDNING, FARGE_NEDSATT, FARGE_GODE, _FARGE_UKJENT]
    return kategorier, verdier, farger, totalt


def fig_innsatsgrupper_totalt(df: pd.DataFrame) -> go.Figure:
    """Horisontalt søylediagram: totalt antall som fikk jobb per innsatsgruppe."""
    kategorier, verdier, farger, _ = _beregn_innsatsgrupper(df)

    fig = go.Figure(
        go.Bar(
            x=verdier,
            y=kategorier,
            orientation="h",
            marker_color=farger,
            text=[f"{int(v)}" for v in verdier],
            textposition="outside",
            hovertemplate="%{y}: %{x:.0f} personer<extra></extra>",
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Innsatsgrupper blant de som fikk jobb",
        xaxis_title="Antall personer",
        yaxis_title=None,
        showlegend=False,
        margin={"t": 70, "b": 50, "l": 180, "r": 60},
        xaxis_range=[0, max(verdier) * 1.15],
    )
    return fig


def fig_innsatsgrupper_kake(df: pd.DataFrame) -> go.Figure:
    """Kakediagram: fordeling av innsatsgrupper blant de som fikk jobb."""
    kategorier, verdier, farger, _ = _beregn_innsatsgrupper(df)

    fig = go.Figure(
        go.Pie(
            labels=kategorier,
            values=verdier,
            marker={"colors": farger},
            textinfo="label+percent",
            textposition="outside",
            texttemplate="<b>%{label}: %{percent}</b>",
            hovertemplate="%{label}: %{value:.0f} personer (%{percent})<extra></extra>",
            sort=False,
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Fordeling av innsatsgrupper blant de som fikk jobb",
        showlegend=False,
        margin={"t": 70, "b": 50, "l": 60, "r": 60},
    )
    fig.update_traces(marker={"line": {"color": "#FFFFFF", "width": 2}})
    return fig


def _stacked_wo_histogram(
    df: pd.DataFrame,
    kolonne: str,
    farge: str,
    snitt_farge: str,
    tittel: str,
    x_tittel: str,
    hover_felt_label: str,
    extra_cols: list[str] | None = None,
    extra_hover: str = "",
) -> go.Figure:
    """Felles logikk for stablede WO-segment-histogrammer."""
    aktive = df[df["har_data"]].copy()
    cols = ["workop_nr", kolonne, "nav_kontor", "dato"] + (extra_cols or [])
    data = aktive[cols].dropna(subset=[kolonne]).copy()
    data[kolonne] = data[kolonne].astype(int)
    snitt = data[kolonne].mean()

    data = data.sort_values([kolonne, "workop_nr"])
    data["stack_idx"] = data.groupby(kolonne).cumcount()
    max_stack = data["stack_idx"].max()

    fig = go.Figure()
    for i in range(max_stack + 1):
        lag = data[data["stack_idx"] == i]
        dato_str = lag["dato"].dt.strftime("%d.%m.%Y").fillna("—").tolist()
        customdata = list(zip(
            lag["workop_nr"].tolist(),
            lag["nav_kontor"].fillna("—").tolist(),
            dato_str,
            lag[kolonne].tolist(),
        ))
        fig.add_trace(
            go.Bar(
                x=lag[kolonne].tolist(),
                y=[1] * len(lag),
                marker_color=farge,
                marker_line={"color": "white", "width": 1},
                opacity=0.85,
                customdata=customdata,
                hovertemplate=(
                    f"<b>WO %{{customdata[0]}}</b><br>"
                    f"Lokasjon: %{{customdata[1]}}<br>"
                    f"Dato: %{{customdata[2]}}<br>"
                    f"{hover_felt_label}: %{{x}}{extra_hover}<extra></extra>"
                ),
                showlegend=False,
            )
        )

    fig.add_vline(
        x=snitt,
        line_dash="dash",
        line_color=snitt_farge,
        line_width=2,
        annotation_text=f"Snitt: {snitt:.1f}",
        annotation_position="top right",
        annotation_font_size=13,
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=tittel,
        xaxis_title=x_tittel,
        yaxis_title="Antall WorkOp-er",
        barmode="stack",
        xaxis={"dtick": 1},
        yaxis={"dtick": 1},
        margin=_MARGIN,
    )
    return fig


def fig_histogram_jobb(df: pd.DataFrame) -> go.Figure:
    """Stablet søylediagram: hver WorkOp er et segment, gruppert per fatt_jobb-verdi."""
    aktive = df[df["har_data"]].copy()
    jobb = aktive[["workop_nr", "fatt_jobb", "nav_kontor", "dato", "oppmotte"]].dropna(subset=["fatt_jobb"]).copy()
    jobb["fatt_jobb"] = jobb["fatt_jobb"].astype(int)
    jobb["andel_fatt_jobb"] = (jobb["fatt_jobb"] / jobb["oppmotte"] * 100).round(0).astype(str) + "%"
    snitt = jobb["fatt_jobb"].mean()

    # Sorter og tildel stabel-posisjon per x-verdi
    jobb = jobb.sort_values(["fatt_jobb", "workop_nr"])
    jobb["stack_idx"] = jobb.groupby("fatt_jobb").cumcount()
    max_stack = jobb["stack_idx"].max()

    fig = go.Figure()
    for i in range(max_stack + 1):
        lag = jobb[jobb["stack_idx"] == i]
        dato_str = lag["dato"].dt.strftime("%d.%m.%Y").fillna("—").tolist()
        customdata = list(zip(
            lag["workop_nr"].tolist(),
            lag["nav_kontor"].fillna("—").tolist(),
            dato_str,
            lag["oppmotte"].fillna(0).astype(int).tolist(),
            lag["fatt_jobb"].astype(int).tolist(),
            lag["andel_fatt_jobb"].tolist(),
        ))
        fig.add_trace(
            go.Bar(
                x=lag["fatt_jobb"].tolist(),
                y=[1] * len(lag),
                marker_color=FARGE_JOBB,
                marker_line={"color": "white", "width": 1},
                opacity=0.85,
                customdata=customdata,
                hovertemplate=(
                    "<b>WO %{customdata[0]}</b><br>"
                    "Lokasjon: %{customdata[1]}<br>"
                    "Dato: %{customdata[2]}<br>"
                    "Oppmøtte: %{customdata[3]}<br>"
                    "Fått jobb: %{x}<br>"
                    "Andel: %{customdata[5]}<extra></extra>"
                ),
                showlegend=False,
            )
        )

    fig.add_vline(
        x=snitt,
        line_dash="dash",
        line_color=FARGE_OPPMOTTE,
        line_width=2,
        annotation_text=f"Snitt: {snitt:.1f}",
        annotation_position="top right",
        annotation_font_size=13,
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Fordeling: antall som fikk jobb per WorkOp",
        xaxis_title="Antall som fikk jobb",
        yaxis_title="Antall WorkOp-er",
        barmode="stack",
        xaxis={"dtick": 2},
        yaxis={"dtick": 1},
        margin=_MARGIN,
    )
    return fig


def fig_histogram_andel_jobb(df: pd.DataFrame, bin_storrelse: int = 5) -> go.Figure:
    """Stablet søylediagram: hver WorkOp er et segment, gruppert per andel som fikk jobb.

    Andelen rundes ned til nærmeste bin (default 5 %-poeng) og vises som «X–Y%»-labels.
    """
    aktive = df[df["har_data"]].copy()
    data = aktive[["workop_nr", "fatt_jobb", "oppmotte", "nav_kontor", "dato"]].dropna(subset=["fatt_jobb"]).copy()
    data["fatt_jobb"] = data["fatt_jobb"].astype(int)
    data["andel"] = data["fatt_jobb"] / data["oppmotte"] * 100
    data["bin"] = (data["andel"] // bin_storrelse * bin_storrelse).astype(int)

    snitt_andel = data["andel"].mean()
    snitt_bin = snitt_andel // bin_storrelse * bin_storrelse

    alle_bins = list(range(0, int(data["bin"].max()) + bin_storrelse, bin_storrelse))
    bin_labels = {b: f"{b}–{b + bin_storrelse}%" for b in alle_bins}

    data = data.sort_values(["bin", "workop_nr"])
    data["stack_idx"] = data.groupby("bin").cumcount()
    max_stack = int(data["stack_idx"].max())

    fig = go.Figure()
    for i in range(max_stack + 1):
        lag = data[data["stack_idx"] == i]
        dato_str = lag["dato"].dt.strftime("%d.%m.%Y").fillna("—").tolist()
        customdata = list(zip(
            lag["workop_nr"].tolist(),
            lag["nav_kontor"].fillna("—").tolist(),
            dato_str,
            lag["oppmotte"].fillna(0).astype(int).tolist(),
            lag["fatt_jobb"].astype(int).tolist(),
            lag["andel"].round(1).tolist(),
        ))
        x_labels = [bin_labels[b] for b in lag["bin"].tolist()]
        fig.add_trace(
            go.Bar(
                x=x_labels,
                y=[1] * len(lag),
                marker_color=FARGE_JOBB,
                marker_line={"color": "white", "width": 1},
                opacity=0.85,
                customdata=customdata,
                hovertemplate=(
                    "<b>WO %{customdata[0]}</b><br>"
                    "Lokasjon: %{customdata[1]}<br>"
                    "Dato: %{customdata[2]}<br>"
                    "Oppmøtte: %{customdata[3]}<br>"
                    "Fikk jobb: %{customdata[4]}<br>"
                    "Andel: %{customdata[5]:.1f}%<extra></extra>"
                ),
                showlegend=False,
            )
        )

    snitt_label = bin_labels[int(snitt_bin)]
    # add_vline fungerer ikke på kategorisk x-akse — bruk scatter-trace i stedet
    fig.add_trace(
        go.Scatter(
            x=[snitt_label, snitt_label],
            y=[0, max(
                sum(1 for tr in fig.data for bx in tr.x if bx == snitt_label) + 1, # type: ignore
                2
            )],
            mode="lines",
            line={"dash": "dash", "color": FARGE_OPPMOTTE, "width": 2},
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_annotation(
        x=snitt_label,
        y=1,
        yref="paper",
        text=f"Snitt: {snitt_andel:.1f}%",
        showarrow=False,
        xanchor="left",
        font={"size": 13},
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Fordeling: andel som fikk jobb per WorkOp",
        xaxis_title=f"Andel som fikk jobb (gruppert i intervaller på {bin_storrelse} prosentpoeng)",
        yaxis_title="Antall WorkOp-er",
        barmode="stack",
        xaxis={"categoryorder": "array", "categoryarray": [bin_labels[b] for b in alle_bins]},
        yaxis={"dtick": 1},
        margin=_MARGIN,
    )
    return fig


def fig_histogram_bedrifter(df: pd.DataFrame) -> go.Figure:
    """Stablet søylediagram: hver WorkOp er et segment, gruppert per antall bedrifter."""
    return _stacked_wo_histogram(
        df,
        kolonne="arbeidsgivere",
        farge=PALETT["Oransj"],
        snitt_farge=PALETT["Rød"],
        tittel="Fordeling: antall bedrifter per WorkOp",
        x_tittel="Antall bedrifter",
        hover_felt_label="Bedrifter",
    )


def _stacked_subplot_traces(
    data: pd.DataFrame,
    kolonne: str,
    farge: str,
    hover_label: str,
) -> tuple[list[go.Bar], float]:
    """Bygg stablede go.Bar-traces for ett subplot med per-WO hover-info."""
    data = data.sort_values([kolonne, "workop_nr"])
    data["stack_idx"] = data.groupby(kolonne).cumcount()
    max_stack = int(data["stack_idx"].max())
    snitt = data[kolonne].mean()

    traces = []
    for i in range(max_stack + 1):
        lag = data[data["stack_idx"] == i]
        dato_str = lag["dato"].dt.strftime("%d.%m.%Y").fillna("—").tolist()
        forberedende_str = lag["oppmotte_forberedende"].apply(
            lambda v: str(int(v)) if pd.notna(v) else "—"
        ).tolist()
        customdata = list(zip(
            lag["workop_nr"].tolist(),
            lag["nav_kontor"].fillna("—").tolist(),
            dato_str,
            forberedende_str,
            lag["oppmotte"].astype(int).tolist(),
            lag["fatt_jobb"].fillna(0).astype(int).tolist(),
        ))
        traces.append(go.Bar(
            x=lag[kolonne].tolist(),
            y=[1] * len(lag),
            marker_color=farge,
            marker_line={"color": "white", "width": 1},
            opacity=0.85,
            customdata=customdata,
            hovertemplate=(
                "<b>WO %{customdata[0]}</b><br>"
                "Forberedende: %{customdata[3]}<br>"
                "Oppmøtte WorkOp: %{customdata[4]}<br>"
                "Fikk jobb: %{customdata[5]}<br>"
                "Lokasjon: %{customdata[1]}<br>"
                "Dato: %{customdata[2]}<br>"
            ),
            showlegend=False,
        ))
    return traces, snitt


def fig_histogram_deltakere(df: pd.DataFrame) -> tuple[go.Figure, str]:
    """To side-om-side subplott: fordeling av oppmøtte til forberedende og til WorkOp."""
    aktive = df[df["har_data"]].copy()
    cols = ["workop_nr", "oppmotte_forberedende", "oppmotte", "nav_kontor", "dato", "fatt_jobb"]

    med_forberedende = aktive[cols].dropna(subset=["oppmotte_forberedende"]).copy()
    med_forberedende["oppmotte_forberedende"] = med_forberedende["oppmotte_forberedende"].astype(int)
    alle = aktive[cols].copy()

    traces_f, snitt_f = _stacked_subplot_traces(med_forberedende, "oppmotte_forberedende", PALETT["Lilla"], "Forberedende")
    traces_o, snitt_o = _stacked_subplot_traces(alle, "oppmotte", PALETT["Blå"], "Oppmøtte WorkOp")

    n_f = len(med_forberedende)
    n_o = len(alle)
    note = (
        f"{n_o - n_f} arrangementer mangler antall deltakere på forberedende workshop"
        if n_o > n_f
        else ""
    )

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            "Forberedende workshop",
            "Oppmøtte på WorkOp",
        ],
        shared_yaxes=True,
    )

    for t in traces_f:
        fig.add_trace(t, row=1, col=1)
    for t in traces_o:
        fig.add_trace(t, row=1, col=2)

    fig.add_vline(x=snitt_f, line_dash="dash", line_color=PALETT["Lilla"], line_width=2,
                  annotation_text=f"Snitt: {snitt_f:.1f}", annotation_position="top right",
                  annotation_font_size=12, row=1, col=1)  # type: ignore
    fig.add_vline(x=snitt_o, line_dash="dash", line_color=PALETT["Blå"], line_width=2,
                  annotation_text=f"Snitt: {snitt_o:.1f}", annotation_position="top right",
                  annotation_font_size=12, row=1, col=2)  # type: ignore

    fig.update_xaxes(dtick=2, title_text="Antall deltakere")
    fig.update_yaxes(dtick=1, title_text="Antall WorkOp-er", col=1)
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Deltakere på forberedende workshop og på WorkOp",
        barmode="stack",
        margin={**_MARGIN, "t": 100},
    )
    return fig, note


def fig_deltakere_jobb_tid(df: pd.DataFrame) -> go.Figure:
    """
    Stablet søylediagram med programvekst over tid — kvartalsvis aggregering.

    Grupper alle aktive WorkOps med parsbar dato per kvartal. Tomme kvartaler
    (ingen WorkOp) vises som 0 for å synliggjøre gapene i programmet.
    Arrangementer uten dato nevnes i tittelen.
    """
    aktive = df[df["har_data"]].copy()
    med_dato = aktive[aktive["dato"].notna()].copy()
    antall_uten = int(aktive["dato"].isna().sum())

    med_dato["kvartal"] = med_dato["dato"].dt.to_period("Q")
    kvartalsvis = (
        med_dato.groupby("kvartal")
        .agg(oppmotte=("oppmotte", "sum"), fatt_jobb=("fatt_jobb", "sum"), antall=("workop_nr", "count"))
        .reset_index()
    )

    alle_kvartaler = pd.period_range(kvartalsvis["kvartal"].min(), kvartalsvis["kvartal"].max(), freq="Q")
    kvartalsvis = kvartalsvis.set_index("kvartal").reindex(alle_kvartaler, fill_value=0).reset_index()
    kvartalsvis.columns = ["kvartal", "oppmotte", "fatt_jobb", "antall"]

    labels = kvartalsvis["kvartal"].map(lambda p: f"Q{p.quarter} {p.year}").tolist() # type: ignore
    ikke_jobb = (kvartalsvis["oppmotte"] - kvartalsvis["fatt_jobb"]).tolist()
    customdata = list(zip(kvartalsvis["antall"].tolist(), kvartalsvis["oppmotte"].tolist()))

    note = f" ({antall_uten} arrangementer uten dato er utelatt)" if antall_uten else ""

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=kvartalsvis["fatt_jobb"].tolist(),
            name="Oppmøtte som fikk jobb",
            marker_color=FARGE_JOBB,
            customdata=customdata,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "%{customdata[0]} WorkOps — %{customdata[1]} oppmøtte<br>"
                "Fikk jobb: <b>%{y}</b><extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Bar(
            x=labels,
            y=ikke_jobb,
            name="Oppmøtte som ikke fikk jobb",
            marker_color=FARGE_OPPMOTTE,
            customdata=customdata,
            hovertemplate=(
                "<b>%{x}</b><br>%{customdata[0]} WorkOps — %{customdata[1]} oppmøtte<br>Uten jobb: %{y}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=f"Programvekst over tid — oppmøtte og fikk jobb per kvartal{note}",
        xaxis_title="Kvartal",
        yaxis_title="Antall personer",
        barmode="stack",
        legend=_LEGEND_BUNN,
        hovermode="x unified",
        margin=_MARGIN,
    )
    return fig


def fig_kumulativ(df: pd.DataFrame) -> go.Figure:
    """Kumulativ sum oppmøtte og fått jobb over alle arrangement, sortert på dato.

    Viser også en mållinje: kumulativt antall arbeidsgivere (mål = 1 jobb per bedrift).
    """
    aktive = df[df["har_data"]].copy()
    aktive = aktive.sort_values("dato")

    aktive["kumulativ_oppmotte"] = aktive["oppmotte"].cumsum()
    aktive["kumulativ_fatt_jobb"] = aktive["fatt_jobb"].cumsum()
    aktive["kumulativ_maal"] = aktive["arbeidsgivere"].cumsum()

    x = aktive["dato"].dt.strftime("%Y-%m-%d").where(aktive["dato"].notna(), None).tolist()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=aktive["kumulativ_oppmotte"].tolist(),
            mode="lines+markers",
            name="Kumulativt oppmøtte",
            fill="tonexty",
            fillcolor=_rgba(FARGE_OPPMOTTE, 0.6),
            line={"color": FARGE_OPPMOTTE_STERK, "width": 3},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=aktive["kumulativ_fatt_jobb"].tolist(),
            mode="lines+markers",
            name="Kumulativt fikk jobb",
            fill="tozeroy",
            fillcolor=_rgba(FARGE_JOBB, 0.6),
            line={"color": FARGE_JOBB_STERK, "width": 3},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=aktive["kumulativ_maal"].tolist(),
            mode="lines",
            name="Mål (1 per bedrift)",
            line={"color": PALETT["Mellom Lilla"], "width": 2},
            hovertemplate="Mål: %{y} (1 per bedrift)<extra></extra>",
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Kumulativt antall deltakere og jobbplasseringer",
        xaxis_title="Dato",
        yaxis_title="Antall (kumulativt)",
        legend=_LEGEND_BUNN,
        margin=_MARGIN,
        # legend_traceorder="reversed",
    )
    return fig


# ---------------------------------------------------------------------------
# Arbeidsgiverplott
# ---------------------------------------------------------------------------

# Fargepalett for kategoriske bransjer
_FARGE_BRANSJE = [
    PALETT["Lilla"],
    PALETT["Rød"],
    PALETT["Blå"],
    PALETT["Turkis"],
    PALETT["Oransj"],
]

_STORRELSE_ORDEN = ["Mikro\n(<10)", "Liten\n(10–49)", "Medium\n(50–249)", "Stor\n(≥250)"]
_STORRELSE_MAP = {
    "Mikro": "Mikro\n(<10)",
    "Liten": "Liten\n(10–49)",
    "Medium": "Medium\n(50–249)",
    "Stor": "Stor\n(≥250)",
}
_STORRELSE_FARGER = [PALETT["Lilla"], PALETT["Blå"], PALETT["Turkis"], PALETT["Oransj"]]


# ---------------------------------------------------------------------------
# Etterlevelse av metoden (Forms 1, flervalg)
# ---------------------------------------------------------------------------
# Nøkkel = starten på svaralternativet i Forms (små bokstaver), verdi = kort
# visningstekst. Rekkefølgen styrer også rekkefølgen i tabell og figur.
_METODE_KATEGORIER: dict[str, str] = {
    "vi fulgte metoden": "Fulgte metoden fullt ut",
    "vi gjorde noen mindre": "Mindre lokale tilpasninger",
    "vi justerte metoden": "Justerte metoden",
}
_METODE_ANNET = "Annet svar"
_METODE_FARGER = [PALETT["Mellom Grønn"], PALETT["Mellom Blå"], PALETT["Mellom Lilla"], _FARGE_UKJENT]


def _metode_label(verdi: str) -> str:
    """Kort visningstekst for et svar på metode-spørsmålet."""
    tekst = str(verdi).strip().lower()
    for prefiks, label in _METODE_KATEGORIER.items():
        if tekst.startswith(prefiks):
            return label
    return _METODE_ANNET


def tabell_metode_etterlevelse(df: pd.DataFrame) -> pd.DataFrame:
    """
    Smal tabell: WorkOp | Dato | Lokasjon | Fulgte metoden.

    Tar bare med arrangementer som har svart på metode-spørsmålet. Spørsmålet
    er nytt i gjennomføringsskjemaet, så de fleste arrangementene mangler svar.
    """
    svar = df[df["metode_etterlevelse"].notna()].copy()
    svar["metode_label"] = svar["metode_etterlevelse"].map(_metode_label)
    svar = svar.sort_values("workop_nr")

    ut = pd.DataFrame(
        {
            "WorkOp": svar["workop_nr"].astype("Int64"),
            "Dato": svar["dato"].dt.strftime("%d.%m.%Y").fillna("—"),
            "Lokasjon": svar["nav_kontor"].fillna("—"),
            "Fulgte metoden": svar["metode_label"],
        }
    )
    return ut.reset_index(drop=True)


def fig_metode_etterlevelse(df: pd.DataFrame) -> go.Figure:
    """
    Horisontalt søylediagram: antall arrangementer per svar på metode-spørsmålet.

    Alle svaralternativene vises selv om de har null svar, slik at figuren viser
    hele spennet fra «fulgte metoden fullt ut» til «justerte metoden».
    """
    svar = df[df["metode_etterlevelse"].notna()].copy()
    labels = list(_METODE_KATEGORIER.values())
    antall_per_label = svar["metode_etterlevelse"].map(_metode_label).value_counts()

    if (antall_per_label.index == _METODE_ANNET).any():
        labels.append(_METODE_ANNET)

    verdier = [int(antall_per_label.get(label, 0)) for label in labels]
    maks = max(verdier) if verdier else 0

    # Snus fordi horisontale søyler tegnes nedenfra og opp
    fig = go.Figure(
        go.Bar(
            x=verdier[::-1],
            y=labels[::-1],
            orientation="h",
            marker_color=_METODE_FARGER[: len(labels)][::-1],
            text=verdier[::-1],
            textposition="outside",
            hovertemplate="%{y}: %{x} arrangementer<extra></extra>",
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Hvor tett arrangørene fulgte WorkOp-metoden",
        xaxis_title="Antall arrangementer",
        yaxis_title=None,
        showlegend=False,
        margin={"t": 70, "b": 50, "l": 200, "r": 60},
        height=320,
        xaxis_range=[0, max(maks * 1.25, 1)],
    )
    return fig


def tabell_arrangementer_per_aar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Antall gjennomførte arrangementer per år, delt på om resultatet foreligger.

    Teller på `har_gjennomforing`, altså alle avholdte arrangementer. Året
    hentes fra `dato`, med `fallback_year` for rader som mangler dato.
    """
    gjennomfort = df[df["har_gjennomforing"]].copy()

    aar = gjennomfort["dato"].dt.year
    if "fallback_year" in gjennomfort.columns:
        aar = aar.fillna(gjennomfort["fallback_year"])
    gjennomfort = gjennomfort[aar.notna()]
    gjennomfort["aar"] = aar[aar.notna()].astype(int)

    grp = (
        gjennomfort.groupby("aar")
        .agg(
            med_resultat=("har_data", "sum"),
            venter=("venter_pa_forms2", "sum"),
        )
        .reset_index()
        .sort_values("aar")
    )
    grp[["med_resultat", "venter"]] = grp[["med_resultat", "venter"]].astype(int)
    grp["totalt"] = grp["med_resultat"] + grp["venter"]

    grp.columns = ["År", "Med resultat", "Venter på resultat", "Totalt"]
    return grp


def fig_arrangementer_per_aar(df: pd.DataFrame) -> go.Figure:
    """
    Stablet søylediagram: antall gjennomførte WorkOp-arrangementer per år.

    Laget for rapportering, så figuren viser antall avholdte arrangementer og
    ikke resultater. Søylene deles i to slik at det synes hvilke arrangementer
    som fortsatt venter på oppfølgingsskjemaet.
    """
    tabell = tabell_arrangementer_per_aar(df)
    aar = tabell["År"].tolist()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=aar,
            y=tabell["Med resultat"],
            name="Med resultat",
            marker_color=FARGE_JOBB_STERK,
            hovertemplate="%{x}: %{y} arrangementer med resultat<extra></extra>",
        )
    )
    if tabell["Venter på resultat"].sum() > 0:
        fig.add_trace(
            go.Bar(
                x=aar,
                y=tabell["Venter på resultat"],
                name="Venter på resultat",
                marker_color=PALETT["Mellom Lilla"],
                hovertemplate="%{x}: %{y} venter på resultat<extra></extra>",
            )
        )

    # Totalen står over hele stabelen, slik at rapporteringstallet er lett å lese
    fig.add_trace(
        go.Scatter(
            x=aar,
            y=tabell["Totalt"],
            mode="text",
            text=[str(n) for n in tabell["Totalt"]],
            textposition="top center",
            textfont={"size": 13},
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        barmode="stack",
        title="Antall gjennomførte WorkOp-arrangementer per år",
        xaxis_title=None,
        yaxis_title="Antall arrangementer",
        legend=_LEGEND_BUNN,
        margin=_MARGIN,
        height=420,
        xaxis={"type": "category"},
        yaxis_range=[0, max(tabell["Totalt"].max() * 1.15, 1)],
    )
    return fig


def fig_bransje(df_ag: pd.DataFrame) -> go.Figure:
    """
    Horisontal søylediagram: antall arbeidsgiverbesøk per normalisert bransje.

    Sortert høyest antall øverst. Viser bare rader med kjent bransje.
    Dekning (n med bransje / n totalt) vises i tittelen.
    """
    med_bransje = df_ag[df_ag["bransje"].notna()].copy()

    grp = (
        med_bransje.groupby("bransje")
        .size()
        .reset_index(name="antall")
        .sort_values("antall", ascending=True)  # ascending → høyest øverst i horisontal bar
    )

    farger = [_FARGE_BRANSJE[i % len(_FARGE_BRANSJE)] for i in range(len(grp))]

    fig = go.Figure(
        go.Bar(
            x=grp["antall"].tolist(),
            y=grp["bransje"].tolist(),
            orientation="h",
            marker_color=farger,
            text=grp["antall"].tolist(),
            textposition="outside",
            hovertemplate="%{y}: %{x} arbeidsgiverbesøk<extra></extra>",
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Bransjefordeling blant arbeidsgivere",
        xaxis_title="Antall arbeidsgiverbesøk",
        yaxis_title=None,
        margin={"t": 70, "b": 50, "l": 210, "r": 60},
        height=max(400, len(grp) * 32 + 100),
    )
    return fig


def fig_bedriftsstorrelse(df_ag: pd.DataFrame) -> go.Figure:
    """
    Søylediagram: antall arbeidsgivere per EU SME-størrelsesbøtte.

    Mikro (<10) / Liten (10–49) / Medium (50–249) / Stor (≥250).
    Dekning (n med antall_ansatte / n totalt) vises i tittelen.
    """
    med_storrelse = df_ag[df_ag["storrelse"].notna()].copy()

    med_storrelse = med_storrelse.copy()
    med_storrelse["storrelse_label"] = med_storrelse["storrelse"].map(_STORRELSE_MAP)

    grp = med_storrelse.groupby("storrelse_label").size().reindex(_STORRELSE_ORDEN, fill_value=0).reset_index()
    grp.columns = ["kategori", "antall"]

    fig = go.Figure(
        go.Bar(
            x=grp["kategori"].tolist(),
            y=grp["antall"].tolist(),
            marker_color=_STORRELSE_FARGER,
            text=grp["antall"].tolist(),
            textposition="outside",
            hovertemplate=("%{x}<br>Antall arbeidsgivere: %{y}<extra></extra>"),
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Bedriftsstørrelse",
        xaxis_title="Antall ansatte i bedriften",
        yaxis_title="Antall arbeidsgivere",
        showlegend=False,
        margin=_MARGIN,
        yaxis_range=[0, grp["antall"].max() * 1.15],
    )
    return fig


def fig_jobb_usikkerhet(bootstrap_df: pd.DataFrame) -> go.Figure:
    """
    Søylediagram: estimert antall som får jobb med 95 % bootstrap-konfidensintervall.

    Historiske år: grønne søyler.
    Delvise år (faktisk + gjenstående estimat): stablet søyle med CI-whisker.
    Fremtidige år: oransje stripete søyler med error bars (95 % CI).
    Bootstrap-båndet reflekterer variasjon i fatt_jobb på tvers av enkelt-WorkOps.
    """
    historisk = bootstrap_df[bootstrap_df["kilde"] == "historisk"]
    delvis = bootstrap_df[bootstrap_df["kilde"] == "delvis"]
    fremskrivning = bootstrap_df[bootstrap_df["kilde"] == "estimat"]

    fig = go.Figure()

    # Rene historiske år — grønne søyler
    if not historisk.empty:
        fig.add_trace(
            go.Bar(
                x=historisk["aar"].astype(str).tolist(),
                y=historisk["faktisk_jobb"].tolist(),
                name="Faktisk",
                marker_color=FARGE_JOBB,
                hovertemplate="År %{x}<br>Fikk jobb: %{y:.0f}<extra></extra>",
            )
        )

    # Delvise år — stablet søyle: faktisk bunn + estimert topp
    if not delvis.empty:
        # Faktisk del (grønn solid) — uten legend-oppføring (samme farge som "Faktisk")
        fig.add_trace(
            go.Bar(
                x=delvis["aar"].astype(str).tolist(),
                y=delvis["faktisk_jobb"].tolist(),
                name="Faktisk (delvis år)",
                marker_color=FARGE_JOBB,
                showlegend=False,
                hovertemplate=("År %{x}<br>Gjennomført: %{y:.0f}<extra></extra>"),
            )
        )
        # Gjenstående estimat (stiplet oransje topp)
        fig.add_trace(
            go.Bar(
                x=delvis["aar"].astype(str).tolist(),
                y=delvis["est_rest"].tolist(),
                name="Gjenstående (estimat)",
                marker_color=FARGE_ESTIMAT,
                marker_pattern_shape=".",
                opacity=0.7,
                error_y={
                    "type": "data",
                    "array": [
                        (hi - fakt - rest)
                        for hi, fakt, rest in zip(
                            delvis["ci_hi"].tolist(),
                            delvis["faktisk_jobb"].tolist(),
                            delvis["est_rest"].tolist(),
                        )
                    ],
                    "arrayminus": [
                        (fakt + rest - lo)
                        for lo, fakt, rest in zip(
                            delvis["ci_lo"].tolist(),
                            delvis["faktisk_jobb"].tolist(),
                            delvis["est_rest"].tolist(),
                        )
                    ],
                    "visible": True,
                    "color": "#555555",
                },
                hovertemplate=(
                    "År %{x}<br>"
                    "Gjenstående estimat: %{y:.0f}<br>"
                    "95 % CI: [%{customdata[0]:.0f}, %{customdata[1]:.0f}]<extra></extra>"
                ),
                customdata=list(
                    zip(
                        delvis["ci_lo"].tolist(),
                        delvis["ci_hi"].tolist(),
                    )
                ),
            )
        )

    # Fremtidige år — søyler med error bars (CI)
    if not fremskrivning.empty:
        x_est = fremskrivning["aar"].astype(str).tolist()
        ci_lo = fremskrivning["ci_lo"].tolist()
        ci_hi = fremskrivning["ci_hi"].tolist()
        est_jobb = fremskrivning["est_jobb"].tolist()

        fig.add_trace(
            go.Bar(
                x=x_est,
                y=est_jobb,
                name="Estimat",
                marker_color=FARGE_ESTIMAT,
                marker_pattern_shape="/",
                opacity=0.7,
                error_y={
                    "type": "data",
                    "array": [hi - est for hi, est in zip(ci_hi, est_jobb)],
                    "arrayminus": [est - lo for lo, est in zip(ci_lo, est_jobb)],
                    "visible": True,
                    "color": "#555555",
                },
                hovertemplate=(
                    "År %{x} (estimat)<br>"
                    "Sentralestimat: %{y:.0f}<br>"
                    "95 % CI: [%{customdata[0]:.0f}, %{customdata[1]:.0f}]<extra></extra>"
                ),
                customdata=list(zip(ci_lo, ci_hi)),
            )
        )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Estimert antall som får jobb med 95 % konfidensintervall",
        xaxis={"title": "År", "type": "category"},
        yaxis_title="Antall personer",
        barmode="stack",
        legend=_LEGEND_BUNN,
        margin=_MARGIN,
    )
    return fig
