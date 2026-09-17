---
applyTo: "**/*.py"
---

# Python i workop-visualisering

## Modulansvar

| Modul | Ansvar |
|-------|--------|
| `extract.py` | Leser og normaliserer Forms-CSV. Returnerer `(df, warnings)` |
| `transform.py` | Avledede kolonner, historiske snitt, fremskrivning, bootstrap |
| `plots.py` | Rene figurfunksjoner: `df -> go.Figure`. Ingen datainnlesing |

Hold laget rent: ingen filinnlesing i `plots.py`, ingen plotting i `extract.py`.

## Konvensjoner

- `from __future__ import annotations` øverst, type hints på alle signaturer
- Norske docstrings med `Args:` / `Returnerer:`
- `_`-prefiks på private hjelpere
- Nye avhengigheter med `uv add`, aldri manuell redigering av `uv.lock`
- Import i `.qmd` og `__main__.py` bruker `from src.workop...` — pakken er ikke
  installert som distribusjon, og `just extract` kjører `python -m src.workop`
  fra repo-rot. Ikke "fiks" dette til bare `workop`

## extract.py — feller

**1. Forms 1 leses på NAVN, Forms 2 på POSISJON.**
Forms 1 gikk over til navneoppslag (`FORMS1_FELT` + `_finn_kolonne()`) fordi nye
spørsmål settes inn midt i skjemaet og forskyver alt etter seg — sist flyttet
«Antall arbeidsgivere» seg fra indeks 11 til 12. Legger du til et felt, legg inn
nøkkelordet i `FORMS1_FELT`; er feltet nytt i skjemaet, legg det også i
`FORMS1_VALGFRIE` så eldre CSV-er ikke gir advarsel. Tallfelt må inn i
`FORMS1_TALLFELT`.

Nøkkelord må matche **nøyaktig én** kolonne — `_finn_kolonne()` advarer både ved
null og flere treff. Pass på delstrenger: «trenger veiledning» finnes i to
spørsmål, derfor nøkkelordet `trenger veiledning"?`.

Forms 2 leses fortsatt på indeks, med `FORMS2_SKJEMA` + `_sjekk_skjema()` som
vaktpost. Endrer du indeksene der, må tabellen oppdateres samtidig.

**2. Fritekst skal aldri ut av Forms.**
Dashbordet er offentlig. Fritekstsvar (f.eks. «Har du noen forslag til endring i
metoden …») hentes bevisst ikke ut, og skal ikke legges til i `FORMS1_FELT`.
De leses i Forms av de som gjør nærmere analyser. Flervalgsfelt uten
personopplysninger, som `metode_etterlevelse`, er derimot greit.

**3. `SEMANTIKK_GRENSE = 46` er en forretningsregel, ikke et magisk tall.**

- WO ≤ 46: `jobb_hos_wo_ag` er *totalt* antall som fikk jobb
- WO > 46: totalt = `jobb_hos_wo_ag + jobb_annen_ag`

Forms-spørsmålet ble delt i to fra og med WO 47. Ikke "forenkle" bort dette.

**4. `output_cols` på slutten av `extract_all()` er en allowlist.**
Kolonner som ikke står der, forsvinner stille. Legger du til en kolonne i
`f1_data` eller `f2_data`, må den også inn i `output_cols`.

**5. Datoer.**
Forms leverer `dd.mm.yyyy` (noen ganger `dd/mm/yyyy`) — begge håndteres i
`_parse_forms_date()`. `.map()` over en parse-funksjon gir `object`-dtype, så
resultatet må wrappes i `pd.to_datetime()`. Uten det feiler `.dt`-accessoren
lenger ned i pipelinen.

I tillegg: `_fjern_testrader()` dropper rader der Email, Name *og* Nav-kontor
alle er `"test"`. Alle tre må matche.

## Gjennomføring vs. resultat

Data kommer inn i to omganger, og skjemaene er ikke i synk: Forms 2 sendes ut
omtrent fem uker etter arrangementet. De nyeste arrangementene finnes derfor i
Forms 1, men mangler resultat.

| Kolonne | Betydning |
|---------|-----------|
| `har_gjennomforing` | Registrert i Forms 1 — arrangementet er avholdt |
| `har_data` | Registrert i Forms 2 — resultat foreligger |
| `venter_pa_forms2` | Avholdt, men resultatet er ikke kommet inn ennå |

**Alle resultattall og andeler regnes på `har_data`.** Bruk aldri antall
gjennomførte som nevner for jobbtall — det undervurderer resultatet.

`har_gjennomforing` brukes til å telle arrangementer og kontorer, og til å vise
hele datasettet på Data-fanen. Figurer holdes på `har_data` så alle har samme
grunnlag. Hvor mange arrangementer en figur bygger på, oppgis i hjelpeteksten
under figuren.

## transform.py

`KONTORER_PLAN`, `WORKOP_PER_KONTOR_PER_AAR` og `PLANLAGT_WORKOP` er bevisste
antakelser om oppskalering. Ikke juster dem uten at det er bestilt.

`bootstrap_usikkerhet()` bruker fast `seed=42` — resultatene skal være
reproduserbare mellom kjøringer.

## plots.py — husstil

- **`plotly.graph_objects`, ikke `plotly.express`.** Hele modulen bruker `go.*`
  for å ha full kontroll på stil
- **Farger kun via `PALETT`** (lastet fra `palett.json`, Nav Ung-paletten).
  Bruk de navngitte konstantene: `FARGE_OPPMOTTE`, `FARGE_JOBB`, `FARGE_ESTIMAT`
  osv. Ingen hardkodede hex-verdier i nye figurer
- **Delte layout-konstanter:** `PLOTLY_TEMPLATE`, `_LEGEND_BUNN`, `_MARGIN`
- **Filtrer alltid på `har_data`** før aggregering — rader uten oppfølgingssvar
  skal ikke telles
- **Hover-template** bør inneholde WO-nummer, lokasjon og dato
- **Skriv for folk på kontorene, ikke for forskere.** Titler og aksetitler skal
  være vanlig norsk. Ikke bruk statistikknotasjon eller fagord som «bins»,
  «observasjoner» eller antallsforkortelser i noe som vises på siden.
  Datagrunnlaget forklares i stedet i en kort hjelpetekst under figuren — se
  `figurtekst()`
- `_rgba()` brukes for gjennomsiktighet i konfidensbånd og fyll

## Hjelpetekst under figurer

`figurtekst(beskrivelse, df)` lager en kort forklaring som legges under hvert
plott: én setning om hva figuren viser, pluss hvor mange arrangementer tallene
bygger på. Teksten rendres som vanlig HTML, ikke som en del av bildet, slik at
skjermlesere får den med.

Legg alltid en `figurtekst()` under nye figurer på de publiserte sidene.

## Verifisering

`just extract` kjører hele uttrekket og skriver ut advarsler. Sjekk at antall
rader og `har_data` ser fornuftig ut, og at det ikke er kommet nye advarsler.
