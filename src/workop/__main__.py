"""Kjør som modul: python -m workop (eller: just extract)."""

from src.workop.extract import extract_all

df, warnings = extract_all()
gjennomfort = df[df["har_gjennomforing"]].copy()
gjennomfort["status"] = gjennomfort["venter_pa_forms2"].map(
    {True: "Venter på resultater", False: ""}
)

print(
    gjennomfort[
        ["workop_nr", "dato", "nav_kontor", "oppmotte", "fatt_jobb", "status"]
    ].to_string()
)

antall_venter = int(df["venter_pa_forms2"].sum())
print(
    f"\nGjennomført: {int(df['har_gjennomforing'].sum())}  |  "
    f"med resultat: {int(df['har_data'].sum())}  |  "
    f"Venter på resultater: {antall_venter}"
)

if warnings:
    print(f"\nAdvarsler ({len(warnings)} stk):")
    for w in warnings:
        print(f"  ⚠️  {w}")
