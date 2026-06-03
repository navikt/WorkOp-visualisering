# WorkOp — resultater og fremskrivning

Visualiseringer av WorkOp-programmet ved Nav. Datagrunnlaget er en Excel-fil med
resultater fra individuelle arrangementer. Nettsiden bygges med Quarto og oppdateres
ved å kjøre `just render` etter at ny Excel-fil er lagt inn.

## Kom i gang

```bash
# Installer avhengigheter (krever uv og just)
just install

# Forhåndsvis nettsiden lokalt
just preview

# Bygg statisk nettside til _site/
just render
```

## Oppdater med nye data

1. Erstatt `data/Resultat og måling 1-32 Workop.xlsx` med ny fil
2. Kjør `just render`

Sjekk at datauttrekket ser riktig ut før du bygger:

```bash
just extract
```

## Juster estimeringsparametere

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

## Sandkasse

`notebooks/eksperimentering.py` er en Jupytext-fil for fri utforsking.
Synk mellom `.py` og `.ipynb` med:

```bash
just sync
# Åpne deretter notebooks/eksperimentering.ipynb i VS Code eller JupyterLab
```
