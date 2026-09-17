---
applyTo: "dbt/**"
---

# dbt (påbegynt)

> **Status: skjelett.** Foreløpig finnes bare `dbt_project.yml`, `profiles.yml`
> og seeds. Ingen modeller er skrevet ennå. Målet er å eksponere WorkOp-tall i
> Metabase.

Ikke bygg ut modellag på eget initiativ — vent på en konkret bestilling.

## Oppsett

- Egen uv-workspace-medlem (`dbt/pyproject.toml`), target er BigQuery
- Seeds fylles med `just cpseed`, som kopierer CSV fra `data/`. Seeds er
  gitignorert, semikolon-separert (`+delimiter: ';'`)

## Tenkt lagstruktur

```
staging  →  intermediate  →  marts  →  dataprodukt
view        view             table     view
```

Mappene `models/staging/` og `models/marts/` finnes allerede, men er tomme.

## Personvern

`vars.prikk_terskel: 10` er et personvernkrav: dataprodukt-laget skal ikke
eksponere grupper med færre enn 10 personer. Tallene er selvrapporterte per
Nav-kontor. Aldri commit seed-data, og aldri gjengi rader i commit-meldinger
eller PR-tekst.
