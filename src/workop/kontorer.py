"""
Oppslag fra WorkOp-lokasjon til Nav-kontor og fylke.

Lokasjonen som oppgis i Forms er ikke alltid et kontornavn. Noen arrangementer
er samarbeid mellom flere kontorer («Øvre Romerike»), og noen bruker en kortform
av kontornavnet («Sunnfjord» for «Sunnfjord og Ytre Sogn»). Oppslaget går derfor
i to hopp:

    nav_kontor (Forms)  ->  lokasjon-kontor.csv  ->  kontor-fylke.csv
    «Øvre Romerike»         4 kontornavn             Øst-Viken

Lokasjoner som allerede heter det samme som kontoret hopper over første steg.

Filene i lister/ er eneste fasit. Mangler et navn, stopper vi med LokasjonError
framfor å gjette — et stille feilestimat i en figur er verre enn en feilmelding.

Bruk:
    from src.workop.kontorer import fylke_for_lokasjon, valider_lokasjoner
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
LISTER_DIR = _REPO_ROOT / "lister"
LOKASJON_KONTOR_CSV = LISTER_DIR / "lokasjon-kontor.csv"
KONTOR_FYLKE_CSV = LISTER_DIR / "kontor-fylke.csv"


class LokasjonError(ValueError):
    """En lokasjon eller et kontor mangler i lister/-filene."""


@lru_cache(maxsize=1)
def last_kontorregister() -> tuple[dict[str, tuple[str, ...]], dict[str, str]]:
    """
    Leser begge oppslagsfilene i lister/.

    Returnerer:
        (lokasjon -> kontorer, kontor -> fylke). Begge med trimmede navn.
        Resultatet caches, så filene leses én gang per prosess.
    """
    lok_df = pd.read_csv(LOKASJON_KONTOR_CSV, sep=";", dtype=str)
    fylke_df = pd.read_csv(KONTOR_FYLKE_CSV, sep=";", dtype=str)

    lokasjon_til_kontorer = {
        str(rad["lokasjon"]).strip(): tuple(
            del_navn.strip() for del_navn in str(rad["nav_kontorer"]).split(",")
        )
        for _, rad in lok_df.iterrows()
    }
    kontor_til_fylke = {
        str(rad["kontor"]).strip(): str(rad["fylke"]).strip()
        for _, rad in fylke_df.iterrows()
    }
    return lokasjon_til_kontorer, kontor_til_fylke


def kontorer_for_lokasjon(lokasjon: str) -> tuple[str, ...]:
    """
    Nav-kontorene en lokasjon dekker.

    Lokasjoner uten egen rad i lokasjon-kontor.csv antas å være ett kontor med
    samme navn. Det gjelder de fleste.
    """
    lokasjon_til_kontorer, _ = last_kontorregister()
    return lokasjon_til_kontorer.get(str(lokasjon).strip(), (str(lokasjon).strip(),))


def fylke_for_lokasjon(lokasjon: str) -> str:
    """
    Fylket en lokasjon hører til.

    Kaster LokasjonError hvis et kontor mangler i kontor-fylke.csv, eller hvis
    et samarbeid krysser fylkesgrensen — da må vi bestemme hvilket fylke
    arrangementet skal telle i, og det er ikke noe koden kan avgjøre selv.
    """
    _, kontor_til_fylke = last_kontorregister()
    kontorer = kontorer_for_lokasjon(lokasjon)

    ukjente = [k for k in kontorer if k not in kontor_til_fylke]
    if ukjente:
        raise LokasjonError(_ukjent_melding({lokasjon: ukjente}))

    fylker = {kontor_til_fylke[k] for k in kontorer}
    if len(fylker) > 1:
        raise LokasjonError(
            f"Lokasjonen {lokasjon!r} dekker kontorer i flere fylker: "
            f"{', '.join(sorted(fylker))}. Bestem hvilket fylke arrangementet "
            f"skal telle i, og del opp raden i {LOKASJON_KONTOR_CSV.name}."
        )
    return fylker.pop()


def unike_kontorer(lokasjoner: list[str]) -> set[str]:
    """
    Settet av Nav-kontorer en samling lokasjoner dekker.

    Sett, ikke sum: et kontor kan både ha arrangert alene og inngått i et
    samarbeid, og skal da telles én gang.
    """
    kontorer: set[str] = set()
    for lokasjon in lokasjoner:
        kontorer.update(kontorer_for_lokasjon(lokasjon))
    return kontorer


def valider_lokasjoner(lokasjoner: list[str]) -> None:
    """
    Sjekker at alle lokasjoner kan slås opp til et fylke.

    Samler alle problemene i én feilmelding framfor å stoppe på det første, så
    en oppdatering av lister/ kan gjøres i én omgang.
    """
    _, kontor_til_fylke = last_kontorregister()

    manglende: dict[str, list[str]] = {}
    for lokasjon in sorted({str(lok).strip() for lok in lokasjoner if pd.notna(lok)}):
        ukjente = [k for k in kontorer_for_lokasjon(lokasjon) if k not in kontor_til_fylke]
        if ukjente:
            manglende[lokasjon] = ukjente

    if manglende:
        raise LokasjonError(_ukjent_melding(manglende))


def _ukjent_melding(manglende: dict[str, list[str]]) -> str:
    """Feilmelding som sier hvilken fil som må rettes, og hvordan."""
    linjer = [
        f"  {lokasjon!r} -> fant ikke kontoret {', '.join(repr(k) for k in kontorer)}"
        for lokasjon, kontorer in manglende.items()
    ]
    return (
        "Ukjent lokasjon i Forms-dataene:\n"
        + "\n".join(linjer)
        + f"\n\nRett opp i lister/{LOKASJON_KONTOR_CSV.name}: legg inn en rad som "
        f"oversetter lokasjonen til kontornavn slik de staves i "
        f"lister/{KONTOR_FYLKE_CSV.name}. Dekker lokasjonen flere kontorer, "
        "skill dem med komma."
    )
