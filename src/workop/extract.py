"""
Henter og normaliserer data fra WorkOp Forms CSV-filer.

Bruk:
    df, warnings = extract_all()
    df_ag, ag_warnings = extract_arbeidsgivere()
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Standardstier
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
FORMS1_CSV = DATA_DIR / "Rett etter gjennomføring av WorkOp.csv"
FORMS2_CSV = DATA_DIR / "Hvor mange fikk jobb etter WorkOp.csv"

# Grense for semantikk-skift: WO ≤ denne verdien bruker kol9 som total fått jobb
# WO > denne verdien: total = kol9 + kol10
SEMANTIKK_GRENSE = 46

# Antall arbeidsgiver-slots i Forms 2 branching
AG_SLOTS = 7

# Normalisering fritekst-bransje → standardisert kategori (nøkler er lowercase).
# Oppdater når nye bransjetyper dukker opp.
BRANSJE_NORM: dict[str, str] = {
    # Restaurant og servering
    "restaurant": "Restaurant og servering",
    "servering": "Restaurant og servering",
    "servering/sjåfør": "Restaurant og servering",
    "servering/kokk": "Restaurant og servering",
    "servitør": "Restaurant og servering",
    "kafe": "Restaurant og servering",
    "rest./kantine/kafe": "Restaurant og servering",
    "restaurantmedarbeider og kokk/kjøkkenassistent": "Restaurant og servering",
    "medarbeider innen mat og servering": "Restaurant og servering",
    "overnattings- og serveringsvirksomhet": "Restaurant og servering",
    "kiosk/lager/servering": "Restaurant og servering",
    # Varehandel og butikk
    "varehandel": "Varehandel og butikk",
    "butikkmedarbeider": "Varehandel og butikk",
    "butikk": "Varehandel og butikk",
    "butikk/dagligvarehandel": "Varehandel og butikk",
    "butikkmedarbeider byggvare": "Varehandel og butikk",
    "butikkmedarbeider dagligvare": "Varehandel og butikk",
    "dagligvarehandel": "Varehandel og butikk",
    "detaljhandel": "Varehandel og butikk",
    "matbutikk": "Varehandel og butikk",
    "møbelbutikk": "Varehandel og butikk",
    "varehus": "Varehandel og butikk",
    "varehus (åpner i juni)": "Varehandel og butikk",
    "varehandel (detaljhandel med bredt vareutvalg)": "Varehandel og butikk",
    "varehandel/sport": "Varehandel og butikk",
    "engros": "Varehandel og butikk",
    "salg": "Varehandel og butikk",
    "salg/service": "Varehandel og butikk",
    "kioskmedarbeider/lager": "Varehandel og butikk",
    "bensinstasjon": "Varehandel og butikk",
    "07-eleven": "Varehandel og butikk",
    # Sikkerhet og vakt
    "sikkerhet": "Sikkerhet og vakt",
    "vekter": "Sikkerhet og vakt",
    "alarmoperatør": "Sikkerhet og vakt",
    "forretningsmessig tjenesteyting": "Sikkerhet og vakt",
    "forretningsmessig tjenesteyting (vakttjenester ikke nevnt annet sted)": "Sikkerhet og vakt",
    "saferoad": "Sikkerhet og vakt",
    "veisikkerhet": "Sikkerhet og vakt",
    "sikkerhet på vei": "Sikkerhet og vakt",
    "sikkerhet vei": "Sikkerhet og vakt",
    "trafikkdirigenter": "Sikkerhet og vakt",
    "vakthald/": "Sikkerhet og vakt",
    # Industri og produksjon
    "industri": "Industri og produksjon",
    "hjelpearbeider industri innen iso-faget": "Industri og produksjon",
    "industri (overflatebehandling av metaller)": "Industri og produksjon",
    "industri - fiskefor": "Industri og produksjon",
    "produksjon": "Industri og produksjon",
    "mat produksjon": "Industri og produksjon",
    "næringsmiddel": "Industri og produksjon",
    "sjømat": "Industri og produksjon",
    "lager/produksjon": "Industri og produksjon",
    "flycatering/lager/produksjon": "Industri og produksjon",
    "nor tekstil": "Industri og produksjon",
    # Renhold
    "renhold": "Renhold",
    "renhold/husøkonom": "Renhold",
    "forretningsmessig tjenesteyting (rengjøring av bygninger)": "Renhold",
    "elis": "Renhold",
    "housmen": "Renhold",
    # Lager og logistikk
    "lager": "Lager og logistikk",
    "lager/logistikk": "Lager og logistikk",
    "lagermedarbeider byggvare": "Lager og logistikk",
    "terminalarbeider": "Lager og logistikk",
    # Transport
    "transport": "Transport",
    "transport og service": "Transport",
    # Helse og omsorg
    "helsefagarbeider": "Helse og omsorg",
    "helse": "Helse og omsorg",
    "helse/oppvekst": "Helse og omsorg",
    "bpa": "Helse og omsorg",
    "hjemmetjenester/bpa": "Helse og omsorg",
    "oppvekst": "Helse og omsorg",
    # Barnehage og utdanning
    "barnehage": "Barnehage og utdanning",
    "undervisning/formidling": "Barnehage og utdanning",
    "tjønnstuggu barnehage": "Barnehage og utdanning",
    # Bygg og anlegg
    "bygg og anlegg": "Bygg og anlegg",
    "byggebransje": "Bygg og anlegg",
    "byggvarehus": "Bygg og anlegg",
    "tømrer / snekker": "Bygg og anlegg",
    "verksted": "Bygg og anlegg",
    # Hotell og reiseliv
    "hotell": "Hotell og reiseliv",
    "hotell/reiseliv": "Hotell og reiseliv",
    "hotellbransjen": "Hotell og reiseliv",
    "friluft": "Hotell og reiseliv",
    # Bil og kjøretøy
    "bil": "Bil og kjøretøy",
    "bilglass": "Bil og kjøretøy",
    "bilindustri": "Bil og kjøretøy",
    "(truck)mekaniker": "Bil og kjøretøy",
    "bilpleie": "Bil og kjøretøy",
    # Annet (beholder, men sorteres sist i plott)
    "it support": "Annet",
    "kontor og administrasjon": "Annet",
    "renovasjon": "Annet",
    "gjenvinning": "Annet",
    "bemanningsbyrå": "Annet",
    "jordbruk/gartneri": "Annet",
    "landbrukstjenester": "Annet",
    "telefonsalg": "Annet",
    "salgs- og markedskonsulent": "Annet",
    "låsesmed": "Annet",
    "foliering": "Annet",
}

# Forms-bransjer som trenger normalisering til BRANSJE_NORM-kategorier
_FORMS_BRANSJE_MAP: dict[str, str] = {
    "butikk": "Varehandel og butikk",
    "resturant og servering": "Restaurant og servering",
    "industri": "Industri og produksjon",
    "kultur": "Annet",
}


# ---------------------------------------------------------------------------
# Interne hjelpere
# ---------------------------------------------------------------------------


def _normaliser_kolonnenavn(cols: list[str]) -> list[str]:
    """Erstatter NBSP (\\xa0) med vanlig mellomrom i kolonnenavn."""
    return [c.replace("\xa0", " ") for c in cols]


def _safe_int(value: object) -> int | None:
    """Konverterer til int, eller None ved tomme/ugyldige verdier."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return None


def _parse_forms_date(raw: str | None) -> datetime | None:
    """Parser dato på formatet dd/mm/yyyy fra Forms CSV."""
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    try:
        dt = datetime.strptime(raw, "%d/%m/%Y")
        # Fang åpenbare typos (år utenfor rimelig intervall)
        if dt.year < 2023 or dt.year > 2030:
            return None
        return dt
    except ValueError:
        return None


def _read_forms_csv(filepath: str | Path) -> pd.DataFrame:
    """Leser Forms CSV med semikolon-separator og BOM-håndtering."""
    df = pd.read_csv(
        filepath,
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
    )
    df.columns = _normaliser_kolonnenavn(df.columns.tolist())
    return df


def _normaliser_bransje(raw: str | None) -> str | None:
    """
    Mapper råbransje til standardisert kategori.
    Sjekker først Forms-nedtrekksliste, deretter fritekst-mapping fra gammel Excel.
    """
    if not raw or not raw.strip():
        return None
    raw_stripped = raw.strip()
    # Forms-nedtrekksliste bruker kortere navn — sjekk først
    forms_match = _FORMS_BRANSJE_MAP.get(raw_stripped.lower())
    if forms_match:
        return forms_match
    # Sjekk om det allerede er en gyldig normalisert kategori
    valid_categories = set(BRANSJE_NORM.values())
    if raw_stripped in valid_categories:
        return raw_stripped
    # Fallback til fritekst-mapping
    return BRANSJE_NORM.get(raw_stripped.lower(), "Annet")


def _storrelse_kategori(antall_ansatte: int | None) -> str | None:
    """EU SME-standardkategorier basert på antall ansatte."""
    if antall_ansatte is None:
        return None
    if antall_ansatte < 10:
        return "Mikro"
    if antall_ansatte < 50:
        return "Liten"
    if antall_ansatte < 250:
        return "Medium"
    return "Stor"


# ---------------------------------------------------------------------------
# Hovedekstraksjon — extract_all()
# ---------------------------------------------------------------------------


def extract_all(
    forms1_path: str | Path | None = None,
    forms2_path: str | Path | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Leser Forms 1 (gjennomføring) og Forms 2 (jobb-resultater) CSV-filer.

    Returnerer:
        df       — DataFrame med én rad per WorkOp (kompatibel med gammel API)
        warnings — liste med datakvalitetsadvarsler
    """
    f1_path = Path(forms1_path) if forms1_path else FORMS1_CSV
    f2_path = Path(forms2_path) if forms2_path else FORMS2_CSV

    warns: list[str] = []

    # --- Les CSV-filer ---
    f1 = _read_forms_csv(f1_path)
    f2 = _read_forms_csv(f2_path)

    # Filtrer tomme rader (WorkOp-felt er tomt eller NaN)
    f1 = f1[f1["WorkOp"].notna() & (f1["WorkOp"].str.strip() != "")].copy()
    f2 = f2[f2["WorkOp"].notna() & (f2["WorkOp"].str.strip() != "")].copy()

    # Konverter WorkOp til int for joining
    f1["workop_nr"] = f1["WorkOp"].str.strip().astype(int)
    f2["workop_nr"] = f2["WorkOp"].str.strip().astype(int)

    # --- Forms 1: oppmøte og innsatsbehov ---
    f1_cols = f1.columns.tolist()
    f1_data = pd.DataFrame({
        "workop_nr": f1["workop_nr"],
        "dato_raw": f1[f1_cols[6]],  # Dato for selve WorkOp
        "nav_kontor": f1[f1_cols[7]],  # Hvilket Nav-kontor var arrangør?
        "oppmotte_forberedende": f1[f1_cols[8]].map(_safe_int),
        "oppmotte": f1[f1_cols[9]].map(_safe_int),
        "innkalt_intervju": f1[f1_cols[10]].map(_safe_int),
        "arbeidsgivere": f1[f1_cols[11]].map(_safe_int),
        # Innsatsgrupper for oppmøtte
        "ungdomsgaranti_oppmotte": f1[f1_cols[12]].map(_safe_int),
        "innsats_gode_oppmotte": f1[f1_cols[13]].map(_safe_int),
        "innsats_nedsatt_oppmotte": f1[f1_cols[14]].map(_safe_int),
        "innsats_veiledning_oppmotte": f1[f1_cols[15]].map(_safe_int),
    })

    # --- Forms 2: jobb-resultater ---
    f2_cols = f2.columns.tolist()
    f2_data = pd.DataFrame({
        "workop_nr": f2["workop_nr"],
        "deltakere_f2": f2[f2_cols[8]].map(_safe_int),  # Deltakere (duplikat)
        "jobb_hos_wo_ag": f2[f2_cols[9]].map(_safe_int),
        "jobb_annen_ag": f2[f2_cols[10]].map(_safe_int),
        "takket_nei": f2[f2_cols[11]].map(_safe_int),
        "ansatt_med_tiltak": f2[f2_cols[12]].map(_safe_int),
        # Innsatsgrupper for de som fikk jobb
        "ungdomsgaranti_jobb": f2[f2_cols[13]].map(_safe_int),
        "fatt_jobb_gode": f2[f2_cols[14]].map(_safe_int),
        "fatt_jobb_nedsatt": f2[f2_cols[15]].map(_safe_int),
        "fatt_jobb_veiledning": f2[f2_cols[16]].map(_safe_int),
        "n_ag_f2": f2[f2_cols[17]].map(_safe_int),
    })

    # --- Join på workop_nr ---
    df = f1_data.merge(f2_data, on="workop_nr", how="outer")
    df = df.sort_values("workop_nr").reset_index(drop=True)

    # --- Parse dato ---
    df["dato"] = df["dato_raw"].map(_parse_forms_date)
    # Warn about bad dates
    bad_dates = df[df["dato_raw"].notna() & df["dato"].isna()]
    for _, row in bad_dates.iterrows():
        warns.append(f"WO {row['workop_nr']}: ugyldig dato '{row['dato_raw']}'")

    # --- Beregn fatt_jobb med semantikk-skift ---
    def _calc_fatt_jobb(row: pd.Series) -> int | None:
        wo = row["workop_nr"]
        jobb_wo = row["jobb_hos_wo_ag"]
        jobb_annen = row["jobb_annen_ag"]
        if jobb_wo is None:
            return None
        if wo <= SEMANTIKK_GRENSE:
            # Historisk: kol 9 = total fått jobb
            return jobb_wo
        else:
            # Nytt: kol 9 = kun WO-AG, kol 10 = annen AG
            return jobb_wo + (jobb_annen or 0)

    df["fatt_jobb"] = df.apply(_calc_fatt_jobb, axis=1)

    # --- Kompatibilitetskolonner ---
    df["fatt_jobb_tiltak"] = df["ansatt_med_tiltak"]

    # raw_title for hover/tooltip — generert fra kontor + dato
    df["raw_title"] = df.apply(
        lambda r: f"WorkOp {r['nav_kontor'] or ''} {r['dato_raw'] or ''}".strip(),
        axis=1,
    )
    df["title_kort"] = df["nav_kontor"].fillna("")

    # fallback_year beregnes fra dato (brukes i bootstrap_usikkerhet)
    df["fallback_year"] = df["dato"].apply(
        lambda d: d.year if pd.notna(d) else 2026
    )

    # Kolonner som ikke finnes i Forms
    df["dagsverk"] = None
    df["kostnader"] = None

    # har_data: True hvis vi har fatt_jobb
    df["har_data"] = df["fatt_jobb"].notna()

    # --- Sanity checks ---
    aktive = df[df["har_data"]]
    violations = aktive[aktive["fatt_jobb"] > aktive["oppmotte"]]
    for _, row in violations.iterrows():
        warns.append(
            f"WO {row['workop_nr']}: fatt_jobb ({row['fatt_jobb']}) > "
            f"oppmotte ({row['oppmotte']})"
        )

    # Velg kolonner i riktig rekkefølge (kompatibel med gammel API)
    output_cols = [
        "workop_nr", "raw_title", "title_kort", "dato", "fallback_year",
        "nav_kontor",
        "oppmotte_forberedende", "oppmotte", "arbeidsgivere",
        "innkalt_intervju",
        "fatt_jobb", "fatt_jobb_tiltak", "fatt_jobb_nedsatt",
        "fatt_jobb_veiledning", "fatt_jobb_gode",
        "jobb_hos_wo_ag", "jobb_annen_ag", "takket_nei", "ansatt_med_tiltak",
        "ungdomsgaranti_oppmotte", "innsats_gode_oppmotte",
        "innsats_nedsatt_oppmotte", "innsats_veiledning_oppmotte",
        "ungdomsgaranti_jobb",
        "dagsverk", "kostnader", "har_data",
    ]
    df = df[output_cols]

    return df, warns


# ---------------------------------------------------------------------------
# Arbeidsgiverdata — extract_arbeidsgivere()
# ---------------------------------------------------------------------------


def extract_arbeidsgivere(
    forms2_path: str | Path | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Henter arbeidsgiverdata fra Forms 2 CSV (7 slots med branching).

    Returnerer:
        df_ag      — DataFrame med én rad per arbeidsgiver per WorkOp (lang format)
        ag_warnings — liste over WorkOps uten arbeidsgiverdata
    """
    f2_path = Path(forms2_path) if forms2_path else FORMS2_CSV
    warns: list[str] = []

    f2 = _read_forms_csv(f2_path)
    f2 = f2[f2["WorkOp"].notna() & (f2["WorkOp"].str.strip() != "")].copy()
    f2["workop_nr"] = f2["WorkOp"].str.strip().astype(int)

    f2_cols = f2.columns.tolist()

    # AG-data starter ved kolonne 17 (n_ag) + 1 = kolonne 18
    # Slot 0: cols 18-23 (Bedriftsnavn, Bransje, Ansatte, Rekruttering, Speed, Ansatt)
    # Slot 1: cols 24-29 (suffixed med "1")
    # ...
    # Slot 6: cols 54-59 (suffixed med "6")
    AG_FIELDS_PER_SLOT = 6
    AG_START_COL = 18  # First employer field

    rows: list[dict] = []

    for _, record in f2.iterrows():
        wo_nr = record["workop_nr"]
        n_ag = _safe_int(record[f2_cols[17]])
        if not n_ag or n_ag <= 0:
            warns.append(f"WorkOp {wo_nr}: mangler arbeidsgiverdata (n_ag={n_ag})")
            continue

        # Branching fyller fra SLUTTEN: start_slot = AG_SLOTS - n_ag
        start_slot = AG_SLOTS - n_ag
        ag_idx = 0

        for slot in range(start_slot, AG_SLOTS):
            col_offset = AG_START_COL + slot * AG_FIELDS_PER_SLOT
            if col_offset + AG_FIELDS_PER_SLOT > len(f2_cols):
                break

            navn = str(record[f2_cols[col_offset]]).strip() if record[f2_cols[col_offset]] else ""
            if not navn or navn == "nan":
                continue

            ag_idx += 1
            bransje_raw = str(record[f2_cols[col_offset + 1]]).strip() if record[f2_cols[col_offset + 1]] else None
            if bransje_raw == "nan":
                bransje_raw = None

            antall_ansatte = _safe_int(record[f2_cols[col_offset + 2]])

            rows.append({
                "workop_nr": wo_nr,
                "ag_idx": ag_idx,
                "navn": navn,
                "er_anonym": False,  # Forms har alltid navngitte bedrifter
                "bransje_raw": bransje_raw,
                "bransje": _normaliser_bransje(bransje_raw),
                "antall_ansatte": antall_ansatte,
                "storrelse": _storrelse_kategori(antall_ansatte),
                "rekrutteringsbehov": _safe_int(record[f2_cols[col_offset + 3]]),
                "speedintervjuer": _safe_int(record[f2_cols[col_offset + 4]]),
                "ansatt": _safe_int(record[f2_cols[col_offset + 5]]),
            })

        if n_ag and ag_idx == 0:
            warns.append(f"WorkOp {wo_nr}: n_ag={n_ag} men ingen AG-data i slots")

    if rows:
        df_ag = pd.DataFrame(rows).sort_values(["workop_nr", "ag_idx"]).reset_index(drop=True)
    else:
        df_ag = pd.DataFrame(columns=[
            "workop_nr", "ag_idx", "navn", "er_anonym", "bransje_raw",
            "bransje", "antall_ansatte", "storrelse",
            "rekrutteringsbehov", "speedintervjuer", "ansatt",
        ])

    return df_ag, warns
