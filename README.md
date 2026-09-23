# WorkOp — resultater og fremskrivning

Se datafortellingen på datamarkedsplassen: https://data.ansatt.nav.no/quarto/a191ebb5-1c8d-4d42-ac01-6740c3425c86/index.html

## Hvorfor gjøre datainnsamling

Datainnsamling gir et grunnlag for å få oversikt over gjennomføring og resultater fra WorkOp-arrangementene.
Den første datainnsamlingen ble brukt som grunnlag for nasjonal oppskalering av konseptet.
Tall på gjennomføringene gir også mulighet til å lære og så justere konseptet fortløpende.
Overfor ledelsen kan oversikten brukes til forankring og prioritering, slik at beslutninger om å fortsette eller justere WorkOp-konseptet kan tas på et informert grunnlag.

På sikt skal det være mulig for fylkene og kontorene å følge sin egen utvikling og resultater over tid.


## Datafangst

Data samles inn i to steg per WorkOp-arrangement:

| Forms | Tidspunkt | Innhold |
|-------|-----------|---------|
| **Gjennomføring** | Rett etter WorkOp | Dato, kontor, oppmøte, arbeidsgivere, innsatsbehov |
| **Oppfølging** | ~4 uker etter | Antall i jobb, innsatsgrupper, arbeidsgiverdetaljer |

### Oppdatere data

1. Last ned begge Forms-svar som Excel fra SharePoint
2. Lagre som CSV i `data/`:
   - `data/Rett etter gjennomføring av WorkOp.csv`
   - `data/Hvor mange fikk jobb etter WorkOp.csv`
3. Kjør `just render` for å bygge oppdatert nettside

Gjennomføringsskjemaet leses på kolonnenavn, så nye spørsmål kan legges til i
Forms uten at uttrekket brekker. Fritekstsvar hentes bevisst ikke ut — nettsiden
er offentlig, så fritekst leses i Forms av de som gjør nærmere analyser.

### Gjennomført vs. målt

De to skjemaene er ikke i synk: oppfølgingsskjemaet skal fylles ut fem uker
etter arrangementet. Nylig gjennomførte WorkOp-er telles derfor som gjennomført,
men inngår ikke i jobbtall og andeler før resultatet er kommet inn. Differansen
vises på forsiden, og arrangementene ligger med status «Venter på resultater» i
tabellen på Data-fanen.

## Kjøring

```bash
# vis oversikt over datautrekk
just extract

# bygg statisk nettside
just render

# last opp til datamarkedsplassen
just oppdater-quarto _site
```

## Eksperimentering

`notebooks/eksperimentering.py` er en Jupytext-sandkasse for utforsking.
Krever VS Code-extension Jupytext for å synce mellom `.py` og `.ipynb`.

## Estimeringsparametere

Fremskrivningen bruker parametere i `src/workop/transform.py`:

- `KONTORER_PLAN` — planlagt antall Nav-kontorer per år
- `WORKOP_PER_KONTOR_PER_AAR` — antall WorkOp per kontor per år
- `PLANLAGT_WORKOP` — planlagt totalt antall WorkOp for delvis gjennomførte år

## Prosjektstruktur

```
.
├── index.qmd            # Oversikt: KPI, kvartalsvis trend, kontor-tabell
├── fremskrivning.qmd    # Fremskrivning med bootstrap-usikkerhet
├── arbeidsgivere.qmd    # Bransje og bedriftsstørrelse
├── fylker.qmd           # Resultater per fylke, med faner per fylke
├── src/workop/
│   ├── extract.py       # Les og normaliser data fra Forms CSV
│   ├── kontorer.py      # Lokasjon → Nav-kontor → fylke (leser lister/)
│   ├── transform.py     # Beregninger og fremskrivning
│   └── plots.py         # Plotly-figurer og kontor-tabell
├── lister/
│   ├── lokasjon-kontor.csv  # Lokasjon → ett eller flere kontornavn
│   └── kontor-fylke.csv     # Kontor → fylke
├── data/                # CSV-filer fra Forms (ikke på GitHub)
├── notebooks/
│   └── eksperimentering.py  # Jupytext-sandkasse
└── justfile             # Vanlige kommandoer
```

## For AI-agenter

Kontekst for Copilot og andre kodeagenter ligger i
[`.github/copilot-instructions.md`](.github/copilot-instructions.md), med
filspesifikke tillegg i [`.github/instructions/`](.github/instructions/) for
Python, Quarto, `just` og dbt. [`AGENTS.md`](AGENTS.md) peker dit.

Filene dokumenterer blant annet fallgruvene som har gitt feil før: posisjonelle
kolonneindekser i `extract.py`, `output_cols`-allowlisten, og Quarto sin
inline-uttrykk-syntaks.


## Palett

Paletten er fra team Nav Ung, og finnes i sin helhet i `palett.json`.
Her brukes lilla, blå, turkis og grønn som hovedfarger i plott, mens rød og oransje brukes for ekstra kontrast.
