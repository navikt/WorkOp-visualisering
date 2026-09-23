# WorkOp-visualisering

Quarto-datafortelling om WorkOp — arrangementer der Nav kobler arbeidsledige mot
arbeidsgivere. Nettsiden publiseres på datamarkedsplassen og oppdateres omtrent
hver fjerde uke når nye Forms-svar kommer inn.

Se `README.md` for prosjektoversikt og publiseringsrutine.

## Dataflyt

```
data/*.csv (Forms)  →  extract.py  →  transform.py  →  plots.py  →  *.qmd  →  _site/
                       les og         avledede         Plotly-       sider     bygget
                       normaliser     kolonner,        figurer                 nettsted
                                      fremskrivning

lister/*.csv        →  kontorer.py  →  extract.py (validering) + transform.py (fylke)
```

`lister/` er fasit for hvilke Nav-kontorer og hvilket fylke en lokasjon hører
til. En lokasjon som ikke finnes der stopper `just extract` med `LokasjonError` —
det er med vilje, se instruksjonsfila for Python.

Alt kjøres via `just`. Avhengigheter håndteres med `uv` — bruk aldri `pip install`
direkte, og rediger aldri `uv.lock` manuelt.

| Kommando | Formål |
|----------|--------|
| `just extract` | Røyktest av datauttrekket — skriver ut tabell og advarsler |
| `just render` | Bygger hele nettstedet til `_site/` |
| `just preview` | Lokal forhåndsvisning med hot reload |

## Språk

Norsk i kode, kommentarer, docstrings, UI-tekst, commit-meldinger og
PR-beskrivelser. Kolonnenavn og variabler er norske (`oppmotte`, `fatt_jobb`,
`nav_kontor`, `har_data`) — de skal ikke oversettes til engelsk.

## Absolutte regler

- **Ikke commit.** Brukeren committer selv. Lag endringene, og la dem ligge.
- **Ikke commit eller gjengi innhold fra `data/`.** Mappa er gitignorert fordi
  tallene er selvrapporterte per Nav-kontor. Ingen rådata i commit-meldinger,
  PR-tekst eller eksempler.
- **Fritekstsvar fra Forms skal aldri ut i dashbordet.** Nettsiden er offentlig.
  Fritekst leses i Forms av de som gjør nærmere analyser, og hentes ikke ut i
  `extract.py`.
- **Ikke endre estimeringsparametere** i `transform.py` (`KONTORER_PLAN`,
  `WORKOP_PER_KONTOR_PER_AAR`, `PLANLAGT_WORKOP`) uten at det er bestilt. Det er
  bevisste antakelser, ikke magiske tall.

## Gjennomføring vs. resultat

Dataene kommer i to omganger, og skjemaene er ikke i synk — oppfølgingsskjemaet
sendes ut omtrent fem uker etter arrangementet:

- `har_gjennomforing` — arrangementet er avholdt (Forms 1)
- `har_data` — resultat foreligger (Forms 2)
- `venter_pa_forms2` — avholdt, men venter på resultat

Alle jobbtall og andeler regnes på `har_data`. Antall gjennomførte skal aldri
brukes som nevner for resultattall.

## Feller som har bitt før

1. **`data/` er gitignorert.** Får du `FileNotFoundError`, mangler brukeren
   CSV-filene lokalt. Si ifra — ikke generer syntetiske data og ikke endre stier.
2. **`extract.py` leser Forms 1 på kolonnenavn**, Forms 2 på posisjon. Nye
   spørsmål i Forms forskyver indeksene — det har skjedd. Se
   `.github/instructions/python.instructions.md`.
3. **`output_cols` i `extract_all()` er en allowlist.** Nye kolonner som ikke
   legges til der, forsvinner stille fra resultatet.
4. **Quarto inline-uttrykk tar kun enkle variabelnavn.** `` `{python} x` ``
   virker, f-strings inline gjør ikke. Formater i en code chunk først.
5. **Ny `.qmd`-side må inn to steder i `_quarto.yml`**: både under
   `project.render` og under `website.navbar`.

## Verifisering

Kjør `just extract` etter endringer i `src/workop/` — den viser både tabellen og
datakvalitetsadvarsler. Kjør `just render` ved endringer i `.qmd` eller
`_quarto.yml`. Merk at `quarto` kan være blokkert i enkelte terminaler; be i så
fall brukeren kjøre kommandoen.

## Commit-konvensjon

Gitmoji + norsk imperativ, én linje:

```
📊 histogram over oppmøte
🐛 fra ytelser -> statlige ytelser
🧑‍💻 render bare riktige qmd-filer
```

## Mer spesifikke instruksjoner

- `.github/instructions/python.instructions.md` — `src/workop/`
- `.github/instructions/quarto.instructions.md` — `.qmd` og `_quarto.yml`
- `.github/instructions/just.instructions.md` — `justfile`
- `.github/instructions/dbt.instructions.md` — `dbt/` (påbegynt skjelett)
