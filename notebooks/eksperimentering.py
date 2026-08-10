# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
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
import warnings
warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, "..")   # slik at 'src.workop' finnes når notebook kjøres fra notebooks/

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
    fig_deltakere_jobb,
    fig_deltakere_jobb_tid,
    fig_kumulativ,
    fig_andel_jobb,
    fig_estimat,
    fig_innsatsgrupper,
)

fig_deltakere_jobb(df).show()

# %%
fig_deltakere_jobb_tid(df).show()

# %%
fig_kumulativ(df).show()

# %%
fig_andel_jobb(df).show()

# %%
fig_innsatsgrupper(df).show()

# %% [markdown]
# ## Steg 4: Estimeringsmodell

# %%
from src.workop.transform import estimat, KONTORER_PLAN, WORKOP_PER_KONTOR_PER_AAR

# Standard estimat
est = estimat(df)
print("Standard estimat:")
print(est[["aar", "antall_kontorer", "antall_workop", "est_oppmotte", "est_fatt_jobb", "kilde"]].to_string())

# %%
# Alternativt scenario: færre kontorer per år
alternativt_plan = {2026: 20, 2027: 40, 2028: 60, 2029: 80}
est_alt = estimat(df, kontorer_plan=alternativt_plan, workop_per_kontor=2)
print("Alternativt (lavt) scenario:")
print(est_alt[["aar", "antall_kontorer", "antall_workop", "est_oppmotte", "est_fatt_jobb", "kilde"]].to_string())

# %%
fig_estimat(df, est).show()

# %%
fig_estimat(df, est_alt).show()

# %% [markdown]
# ## Steg 5: Validering
#

# %%
total_jobb = aktive["fatt_jobb"].sum()
total_oppmotte = aktive["oppmotte"].sum()
print(f"Totalt fikk jobb:   {total_jobb:.0f}")
print(f"Totalt oppmøtte:    {total_oppmotte:.0f}")
print(f"Historisk jobbrate: {total_jobb/total_oppmotte:.1%}")
