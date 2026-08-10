"""Kjør som modul: python -m workop (eller: just extract)."""

from src.workop.extract import extract_all

df, warnings = extract_all()
aktive = df[df["har_data"]]

print(aktive[["workop_nr", "dato", "nav_kontor", "oppmotte", "fatt_jobb"]].to_string())
if warnings:
    print(f"\nAdvarsler ({len(warnings)} stk):")
    for w in warnings:
        print(f"  ⚠️  {w}")
