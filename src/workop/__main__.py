"""Kjør som modul: python -m workop (eller: just extract)."""

from src.workop.extract import extract_all

DATAFIL = "data/Resultat og måling 1-32 Workop.xlsx"

df, missing = extract_all(DATAFIL)
aktive = df[df["har_data"]]

print(aktive[["workop_nr", "dato", "oppmotte", "fatt_jobb", "raw_title"]].to_string())
print(f"\nArk uten data ({len(missing)} stk): {missing}")
