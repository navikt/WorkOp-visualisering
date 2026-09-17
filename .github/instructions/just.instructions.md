---
applyTo: "justfile"
---

# justfile

`just` er inngangsporten til alt i repoet. Kjør `just` uten argumenter for å se
lista.

| Kommando | Formål |
|----------|--------|
| `install` | `uv sync` — installerer avhengigheter |
| `extract` | Kjører datauttrekket og skriver ut tabell + advarsler. Røyktest |
| `render` | Bygger nettstedet til `_site/` |
| `preview` | Lokal forhåndsvisning med hot reload |
| `sync` | Jupytext-sync av `notebooks/eksperimentering.py` |
| `brand` | Henter Nav-brand-extension (`navikt/nav-quarto-brand`) |
| `update` | `uv lock --upgrade` — oppdaterer pakker |
| `diff-xlsx-csv` | Sammenligner Forms-CSV mot den gamle Excel-fila |
| `cpseed` | Kopierer CSV fra `data/` til `dbt/seeds/` |
| `oppdater-quarto <dir>` | Laster opp bygget nettsted til datamarkedsplassen |

## Konvensjoner

- Python kjøres alltid gjennom `uv run`, aldri mot systemets Python
- Nye kommandoer får en kort norsk kommentar over seg
- **Ingen hemmeligheter i justfile.** `oppdater-quarto` henter team-token fra
  `.env.team-token`, som er gitignorert. Ikke hardkod tokens eller lim dem inn
  i eksempler
- `quarto_id` øverst er dashbordets id på datamarkedsplassen — ikke endre den
  uten at det er bestilt
