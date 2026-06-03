quarto_id := 'a191ebb5-1c8d-4d42-ac01-6740c3425c86'

default:
    just --list

install:
    uv sync

render:
    uv run quarto render

preview:
    uv run quarto preview

sync:
    uv run jupytext --sync notebooks/eksperimentering.py

extract:
    uv run python -m src.workop

brand:
    quarto add navikt/nav-quarto-brand

oppdater-quarto dir:
    #!/usr/bin/env bash
    set -euo pipefail
    files=()
    for file in "{{dir}}"/*; do
        [ -f "$file" ] || continue
        files+=(-F "$(basename "$file")=@$file")
    done
    curl -X PUT "${files[@]}" "https://data.nav.no/quarto/update/{{ quarto_id }}" \
        -H "Authorization: Bearer ${TEAM_TOKEN}"
