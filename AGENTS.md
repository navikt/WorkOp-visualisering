# AGENTS.md

Instruksjonene for dette repoet ligger i
[`.github/copilot-instructions.md`](.github/copilot-instructions.md).

Filspesifikke instruksjoner i [`.github/instructions/`](.github/instructions/):

| Fil | Gjelder |
|-----|---------|
| `python.instructions.md` | `**/*.py` |
| `quarto.instructions.md` | `**/*.qmd` |
| `just.instructions.md` | `justfile` |
| `dbt.instructions.md` | `dbt/**` |

Tre ting som gjelder uansett:

- **Ikke commit** — brukeren committer selv
- **Ikke commit eller gjengi innhold fra `data/`** — selvrapporterte tall per
  Nav-kontor, mappa er gitignorert
- **Norsk** i kode, kommentarer, UI-tekst og commit-meldinger
