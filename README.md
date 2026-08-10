# WorkOp — resultater og fremskrivning

Se datafortellingen på datamarkedsplassen: https://data.ansatt.nav.no/quarto/a191ebb5-1c8d-4d42-ac01-6740c3425c86/index.html

Visualiseringer av WorkOp-programmet ved Nav. Data samles inn via to Microsoft
Forms-undersøkelser og lastes ned som CSV-filer.

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
├── src/workop/
│   ├── extract.py       # Les og normaliser data fra Forms CSV
│   ├── transform.py     # Beregninger og fremskrivning
│   └── plots.py         # Plotly-figurer og kontor-tabell
├── data/                # CSV-filer fra Forms (ikke på GitHub)
├── notebooks/
│   └── eksperimentering.py  # Jupytext-sandkasse
└── justfile             # Vanlige kommandoer
```
