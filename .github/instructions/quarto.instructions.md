---
applyTo: "**/*.qmd,_quarto.yml"
---

# Quarto-sider i workop-visualisering

Nettstedet er en Quarto-website konfigurert i `_quarto.yml`. Sidene henter data
via `from src.workop...` og rendrer Plotly-figurer.

## Inline-uttrykk — vanligste fellen

Quarto sin inline-syntaks tar **kun et enkelt uttrykk**, ikke f-strings:

````
Feil:  `{python} f"{sum_ytelser / 1e6:.1f}"`
Rett:  `{python} sum_ytelser_mill`
````

Formater strengen ferdig i en code chunk først:

````markdown
```{python}
#| echo: false
#| output: false
sum_ytelser_mill = f"{sum_ytelser / 1e6:.1f}"
```

Deltakerne mottok til sammen `{python} sum_ytelser_mill` mill kr i ytelser.
````

Ikke bruk `print()` til løpende tekst — det gir lange monospace-linjer i stedet
for brødtekst.

## Chunk-options

- `#| echo: false` på alle chunks — leserne skal se resultater, ikke kode
- `#| output: false` i tillegg på oppsett-chunks (import, datainnlasting)
- Figurer vises med `fig_navn(df).show()`

## Legge til en ny side

Siden må inn **to steder** i `_quarto.yml`, ellers blir den enten ikke bygget
eller ikke synlig:

```yaml
project:
  render:
    - din-nye-side.qmd   # 1. bygges

website:
  navbar:
    left:
      - href: din-nye-side.qmd   # 2. vises i menyen
        text: Din nye side
```

## Mønstre i repoet

**KPI-bokser:** `_boks(verdi, tekst, bg, border, farge)` bygger et HTML-kort.
Boksene samles i en f-string og vises med `HTML(...)` fra `IPython.display`.
Fargetriplene `blaa`, `gronn` og `teal` gjenbrukes — definer ikke nye ad hoc.

**Callouts** brukes til forbehold om datagrunnlaget:
`::: {.callout-tip appearance="simple"}` og `.callout-important`.

**Forbehold hører hjemme på siden.** Tallene er selvrapporterte, og flere
datasett dekker bare et utvalg WorkOp-er. Når du viser et deltall, skriv hvor
mange arrangementer det gjelder.

**Faner** genereres fra Python i en `#| output: asis`-blokk, som i `fylker.qmd`:

```python
print("::: {.panel-tabset}\n")
for fylke in fylker:
    print(f"### {fylke}\n")
    print(html_innhold + "\n")
print(":::\n")
```

Overskriftsnivået må ligge ett hakk under seksjonen fanene står i, og det må
være blank linje mellom overskrift og rå HTML. `print()` legger på den ene
linjeskiftet, strengen må ha det andre.

## Ikke bruk OJS

OJS krever at siden serveres over HTTP. Åpner noen den ferdigbygde HTML-fila
rett fra disk, får de «This document uses OJS, which requires JavaScript
features disabled when running in file:// URLs», og hele siden faller sammen.
Observable Plot lastes i tillegg fra CDN, så figurene krever nett.

Trenger en side interaktivitet, gjør det med Plotly: tegnforklaringen kan
klikkes for å vise og skjule serier, og `updatemenus` gir nedtrekksmenyer.
Alt bakes inn i sida og virker uten server.

Trengs ekte flervalgsfilter over en tabell, bruker nabo-repoet
`navikt/ung-arbeidsindikatorverktoey-ungdomsgarantien` `itables` med DataTables
SearchBuilder. Det virker fra `file://`, men er tregt å laste.

## Bygging og publisering

```bash
just render     # bygger til _site/
just preview    # lokal forhåndsvisning
```

`_site/` er et byggeartefakt og er gitignorert — rediger aldri filer der.

Publisering: `just oppdater-quarto _site`. Krever `.env.team-token`, som aldri
skal committes eller gjengis.

Hvis `quarto` er blokkert i terminalen din, be brukeren kjøre kommandoen i stedet
for å lete etter omveier.
