# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # WorkOp — eksperimentering og utforskning
#
# Kjør med: `just sync` for å synke til/fra .ipynb
# Eller åpne direkte i VS Code / JupyterLab.

# %%
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, "..")  # slik at 'src.workop' finnes når notebook kjøres fra notebooks/

# %% [markdown]
# ## Steg 1: Les data fra Forms CSV

# %%
from src.workop.extract import extract_all

df_raw, data_warnings = extract_all()

print(f"WorkOp-er lest: {len(df_raw)}")
print(f"Med data: {df_raw['har_data'].sum()}")
if data_warnings:
    print(f"Advarsler: {data_warnings}")

# %%
df_raw[["workop_nr", "dato", "nav_kontor", "oppmotte", "fatt_jobb"]].head(10)

# %% [markdown]
# ## Steg 2: Beregn nøkkeltall

# %%
from src.workop.transform import legg_til_kalkulerte_kolonner, snitt_fra_data

df = legg_til_kalkulerte_kolonner(df_raw)
snitt = snitt_fra_data(df)
print("Historiske snitt:")
for k, v in snitt.items():
    print(f"  {k}: {v}")

# %%
# Andel per WorkOp
aktive = df[df["har_data"]].copy()
aktive[["workop_nr", "oppmotte", "fatt_jobb", "andel_jobb", "kumulativ_fatt_jobb"]].tail(10)

# %% [markdown]
# ## Steg 3: Figurer

# %%
from src.workop.plots import (
    fig_deltakere_jobb_tid,
    fig_kumulativ,
)

fig_deltakere_jobb_tid(df).show()

# %%
fig_kumulativ(df).show()

# %% [markdown]
# ## Steg 4: Estimeringsmodell

# %%
from src.workop.transform import estimat, bootstrap_usikkerhet, KONTORER_PLAN, WORKOP_PER_KONTOR_PER_AAR
from src.workop.plots import fig_jobb_usikkerhet

# Standard estimat
est = estimat(df)
print("Standard estimat:")
print(est[["aar", "antall_kontorer", "antall_workop", "est_oppmotte", "est_fatt_jobb", "kilde"]].to_string())

# %%
boot = bootstrap_usikkerhet(df)
fig_jobb_usikkerhet(boot).show()

# %% [markdown]
# ## Steg 5: Validering
#

# %%
total_jobb = aktive["fatt_jobb"].sum()
total_oppmotte = aktive["oppmotte"].sum()
print(f"Totalt fikk jobb:   {total_jobb:.0f}")
print(f"Totalt oppmøtte:    {total_oppmotte:.0f}")
print(f"Historisk jobbrate: {total_jobb / total_oppmotte:.1%}")


# %%


def oppdater_layout_til_lagring(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "color": "black",
            "family": "Source Sans Pro Bold, Source Sans Pro, Arial, sans-serif",
            "size": 14,
        },
    )
    return fig

def lagre_fig(fig, filsti, scale = 4):
    fig = oppdater_layout_til_lagring(fig)
    fig.write_image(filsti+ ".png", scale=scale)
    return filsti

# %%

f = fig_kumulativ(df)
navn = "fig_kumulativ"
lagre_fig(f, navn, 4)
