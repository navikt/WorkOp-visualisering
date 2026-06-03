# WorkOp — resultater og fremskrivning

Visualiseringer av WorkOp-programmet ved Nav. Datagrunnlaget er en Excel-fil med
resultater fra individuelle arrangementer. Nettsiden bygges med Quarto og oppdateres
ved å kjøre `just render` etter at ny Excel-fil er lagt inn.

## Kjøring

For oppdaterte tall legg en kopi av excelfila i `data/`-mappa, og kjør deretter:

```bash
# viser en oversikt over datauthenting fra excelfila
just extract

# bygg statisk nettside
just render

# last opp oppdatert versjon til datamarkedsplassen
just oppdater-quarto _site
```


## Eksperimentering i en sandkasse

Repoet har også en sandkasse for utforsking av data og visualiseringer i `notebooks/eksperimentering.py`.
Krever VScode extension Jupytext for å synce mellom .py og .ipynb.

## Estimeringsparametere

Fremskrivningen bruker parametere i `src/workop/transform.py`:

- `KONTORER_PLAN` — planlagt antall Nav-kontorer per år
- `WORKOP_PER_KONTOR_PER_AAR` — antall WorkOp per kontor per år
- `PLANLAGT_WORKOP` — planlagt totalt antall WorkOp for delvis gjennomførte år

## Prosjektstruktur

```
.
├── 01_data.qmd          # Datagrunnlag og råtabell
├── 02_resultater.qmd    # Resultater og innsatsgrupper
├── 03_fremskrivning.qmd # Fremskrivning med usikkerhetsestimat
├── 04_arbeidsgivere.qmd # Bransje og bedriftsstørrelse
├── index.qmd            # Sammendragsside
├── src/workop/
│   ├── extract.py       # Les og normaliser data fra Excel
│   ├── transform.py     # Beregninger og fremskrivning
│   └── plots.py         # Alle Plotly-figurer
├── data/                # Excel-kildefil (ikke versjonert)
├── notebooks/
│   └── eksperimentering.py  # Jupytext-sandkasse for utforsking
└── justfile             # Vanlige kommandoer
```
